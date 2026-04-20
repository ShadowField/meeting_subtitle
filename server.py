import asyncio
import subprocess
import threading
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
clients: list[WebSocket] = []
_loop: asyncio.AbstractEventLoop = None

# injected by main.py
asr = None
capture = None
logger = None


def set_loop(loop: asyncio.AbstractEventLoop):
    global _loop
    _loop = loop


def broadcast_sync(msg: dict):
    if _loop:
        asyncio.run_coroutine_threadsafe(_broadcast(msg), _loop)


async def _broadcast(msg: dict):
    dead = []
    for ws in clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in clients:
            clients.remove(ws)


@app.on_event("startup")
async def on_startup():
    set_loop(asyncio.get_event_loop())


@app.get("/")
async def index():
    return HTMLResponse(HTML)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            data = await ws.receive_json()
            t = data.get("type")
            if t == "start":
                await _do_start(ws)
            elif t == "ask":
                content = data.get("content", "").strip()
                if content:
                    threading.Thread(target=_run_claude, args=(content,), daemon=True).start()
    except WebSocketDisconnect:
        if ws in clients:
            clients.remove(ws)


async def _do_start(ws: WebSocket):
    if asr is None:
        return
    asr.start()
    await _broadcast({"type": "started"})

    def audio_loop():
        try:
            for pcm in capture.frames():
                asr.send(pcm)
        except Exception as e:
            print("[capture]", e)

    threading.Thread(target=audio_loop, daemon=True).start()


def _run_claude(content: str):
    CLAUDE_BIN = Path.home() / ".local/lib/nodejs/current/bin/claude"
    prompt = (
        "以下是一段会议实时字幕：\n\n"
        f"{content}\n\n"
        "请用1-2句简洁的中文回应：如果内容里有明确的问题就回答，"
        "否则做一句话的核心摘要。只输出回答本身，不换行，不加任何前缀。"
    )
    try:
        result = subprocess.run(
            [str(CLAUDE_BIN), "-p", prompt],
            capture_output=True, text=True, timeout=60,
            cwd=str(Path(__file__).parent),
        )
        answer = result.stdout.strip() or result.stderr.strip() or "（无回答）"
    except Exception as e:
        answer = f"调用失败：{e}"

    if logger:
        logger.write_claude(answer)
    broadcast_sync({"type": "claude", "text": answer})


HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>会议字幕</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: rgb(20,20,30); color: white;
  font-family: "PingFang SC","Hiragino Sans GB","STHeiti",sans-serif;
  height: 100vh; display: flex; flex-direction: column;
}
#toolbar {
  display: flex; align-items: center; gap: 12px; padding: 10px 16px;
  background: rgb(28,28,42); border-bottom: 1px solid rgb(50,50,70); flex-shrink: 0;
}
#toolbar h1 { font-size: 15px; font-weight: bold; flex: 1; }
button {
  padding: 4px 14px; border-radius: 4px; border: 1px solid;
  cursor: pointer; font-size: 13px; font-weight: bold; background: transparent;
}
#startBtn { color: #4caf50; border-color: #4caf50; }
#startBtn.active { color: #aaa; border-color: #555; cursor: default; }
#askBtn { color: #7eb8f7; border-color: #7eb8f7; }
#askBtn:disabled { color: #aaa; border-color: #555; cursor: default; }
#main { display: flex; flex: 1; overflow: hidden; }
#left { flex: 3; display: flex; flex-direction: column; overflow: hidden; border-right: 1px solid rgb(60,60,80); }
#right { flex: 2; display: flex; flex-direction: column; overflow: hidden; }
.panel-hdr { padding: 6px 12px; font-size: 11px; color: #aaa; background: rgb(28,28,42); flex-shrink: 0; }
#right .panel-hdr { color: #7eb8f7; }
#subtitles { flex: 1; overflow-y: auto; padding: 8px 12px; background: rgb(28,28,42); }
.line { padding: 3px 2px; line-height: 1.6; font-size: 16px; }
#partial {
  padding: 6px 12px; color: #ffd966; font-size: 16px;
  background: rgb(28,28,42); border-top: 1px solid rgb(40,40,55);
  flex-shrink: 0; min-height: 32px;
}
#claude-box {
  flex: 1; overflow-y: auto; padding: 10px 12px;
  background: rgb(28,28,42); color: #7eb8f7;
  font-size: 16px; line-height: 1.6; white-space: pre-wrap;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgb(40,40,55); }
::-webkit-scrollbar-thumb { background: rgb(100,100,130); border-radius: 3px; }
</style>
</head>
<body>
<div id="toolbar">
  <h1>会议字幕</h1>
  <button id="startBtn" onclick="startASR()">▶ 启动</button>
  <button id="askBtn" onclick="askClaude()">◉ 问 Claude</button>
</div>
<div id="main">
  <div id="left">
    <div class="panel-hdr">实时字幕</div>
    <div id="subtitles"></div>
    <div id="partial"></div>
  </div>
  <div id="right">
    <div class="panel-hdr">Claude 回答</div>
    <div id="claude-box"></div>
  </div>
</div>
<script>
const ws = new WebSocket("ws://localhost:8765/ws");
const subtitles = document.getElementById("subtitles");
const partial = document.getElementById("partial");
const claudeBox = document.getElementById("claude-box");
const startBtn = document.getElementById("startBtn");
const askBtn = document.getElementById("askBtn");
let autoScroll = true;
let lastAskLineCount = 0;

subtitles.addEventListener("scroll", () => {
  autoScroll = subtitles.scrollTop + subtitles.clientHeight >= subtitles.scrollHeight - 20;
});

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  if (msg.type === "partial") {
    partial.textContent = msg.text;
  } else if (msg.type === "final") {
    partial.textContent = "";
    const div = document.createElement("div");
    div.className = "line";
    div.textContent = msg.text;
    subtitles.appendChild(div);
    if (autoScroll) subtitles.scrollTop = subtitles.scrollHeight;
  } else if (msg.type === "claude") {
    if (claudeBox.textContent) claudeBox.textContent += "\\n\\n";
    claudeBox.textContent += msg.text;
    claudeBox.scrollTop = claudeBox.scrollHeight;
    askBtn.textContent = "◉ 问 Claude";
    askBtn.disabled = false;
  } else if (msg.type === "started") {
    startBtn.textContent = "● 识别中";
    startBtn.className = "active";
    startBtn.onclick = null;
  }
};

ws.onerror = () => { document.body.style.background = "rgb(40,10,10)"; };

function startASR() {
  ws.send(JSON.stringify({type: "start"}));
}

function askClaude() {
  const lines = subtitles.querySelectorAll(".line");
  const newLines = Array.from(lines).slice(lastAskLineCount).map(l => l.textContent);
  lastAskLineCount = lines.length;
  const content = newLines.join("\\n").trim();
  if (!content) { alert("还没有新字幕内容"); return; }
  askBtn.textContent = "◉ 等待回答…";
  askBtn.disabled = true;
  ws.send(JSON.stringify({type: "ask", content}));
}
</script>
</body>
</html>
"""
