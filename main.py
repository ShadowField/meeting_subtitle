import configparser
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

CLAUDE_BIN = Path.home() / ".local/lib/nodejs/current/bin/claude"

from asr_client import AliyunASR
from audio_capture import LoopbackCapture
from logger import TextLogger
from subtitle_window import SubtitleWindow
from token_manager import get_token


def load_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(__file__), "config.ini")
    if not os.path.exists(path):
        print("未找到 config.ini，请先复制 config.ini.example 为 config.ini 并填入阿里云配置")
        sys.exit(1)
    cfg.read(path, encoding="utf-8")
    return cfg


def main():
    cfg = load_config()
    ak = cfg["aliyun"]["access_key_id"].strip()
    sk = cfg["aliyun"]["access_key_secret"].strip()
    appkey = cfg["aliyun"]["appkey"].strip()
    region = cfg["aliyun"].get("region", "cn-shanghai").strip()

    if ak.startswith("YOUR_") or sk.startswith("YOUR_") or appkey.startswith("YOUR_"):
        print("请在 config.ini 中填入真实的 AccessKey / Appkey")
        sys.exit(1)

    print("[1/3] 获取阿里云 Token ...")
    token = get_token(ak, sk, region)
    print("[2/3] Token 就绪")

    url = f"wss://nls-gateway-{region}.aliyuncs.com/ws/v1"

    app = QApplication(sys.argv)
    win = SubtitleWindow(
        font_size=cfg.getint("ui", "font_size", fallback=16),
        opacity=cfg.getfloat("ui", "opacity", fallback=0.85),
        w=cfg.getint("ui", "window_width", fallback=820),
        h=cfg.getint("ui", "window_height", fallback=420),
        max_lines=cfg.getint("ui", "max_history_lines", fallback=800),
    )
    win.show()

    logger = TextLogger(cfg["log"].get("save_dir", "./logs"))
    capture = LoopbackCapture(sample_rate=16000, frame_ms=100)

    def on_final(text: str):
        win.final_signal.emit(text)
        logger.write(text)

    asr = AliyunASR(
        url=url,
        appkey=appkey,
        token=token,
        on_partial=win.partial_signal.emit,
        on_final=on_final,
        on_error=lambda e: print("[ASR]", e),
    )

    def on_start():
        asr.start()
        def audio_loop():
            try:
                for pcm in capture.frames():
                    asr.send(pcm)
            except Exception as e:
                print("[capture]", e)
        threading.Thread(target=audio_loop, daemon=True).start()
        print(f"[3/3] 字幕已启动，日志保存到: {logger.path}")

    win.start_signal.connect(on_start)
    win.set_log_path(logger.path)

    last_ask_idx = [0]

    def on_ask():
        lines = [lbl.text() for lbl in win._lines]
        new_lines = lines[last_ask_idx[0]:]
        last_ask_idx[0] = len(lines)
        content = "\n".join(new_lines).strip()
        if not content:
            win.claude_signal.emit("还没有字幕内容，请先启动识别并等待字幕出现。")
            return

        def run_claude():
            prompt = (
                "以下是一段会议实时字幕：\n\n"
                f"{content}\n\n"
                "请用1-2句简洁的中文回应：如果内容里有明确的问题就回答，"
                "否则做一句话的核心摘要。"
                "只输出回答本身，不换行，不加任何前缀。"
            )
            try:
                result = subprocess.run(
                    [str(CLAUDE_BIN), "-p", prompt],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(Path(__file__).parent),
                )
                answer = result.stdout.strip()
                if not answer:
                    answer = result.stderr.strip() or "（无回答）"
            except Exception as e:
                answer = f"调用失败：{e}"

            logger.write_claude(answer)
            win.claude_signal.emit(answer)

        threading.Thread(target=run_claude, daemon=True).start()

    win.ask_signal.connect(on_ask)

    def cleanup():
        capture.stop()
        asr.stop()
        logger.close()

    app.aboutToQuit.connect(cleanup)

    print("[2/3] 就绪，点击窗口中的「▶ 启动」按钮开始识别")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
