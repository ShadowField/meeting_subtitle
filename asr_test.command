#!/bin/bash
cd "$(dirname "$0")"
unset QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH DYLD_LIBRARY_PATH DYLD_FRAMEWORK_PATH
./.venv/bin/python - <<'PY'
import configparser, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nls
nls.enableTrace(True)   # 打印全部 WebSocket 交互

cfg = configparser.ConfigParser()
cfg.read("config.ini", encoding="utf-8")
ak     = cfg["aliyun"]["access_key_id"].strip()
sk     = cfg["aliyun"]["access_key_secret"].strip()
appkey = cfg["aliyun"]["appkey"].strip()
region = cfg["aliyun"].get("region", "cn-shanghai").strip()

from token_manager import get_token
token = get_token(ak, sk, region)

import soundcard as sc, numpy as np

url = f"wss://nls-gateway-{region}.aliyuncs.com/ws/v1"

t = nls.NlsSpeechTranscriber(
    url=url, token=token, appkey=appkey,
    on_start          = lambda *_: print(">>> STARTED"),
    on_sentence_begin = lambda msg, *_: print(">>> BEGIN", msg),
    on_sentence_end   = lambda msg, *_: print(">>> FINAL", msg),
    on_result_changed = lambda msg, *_: print(">>> PARTIAL", msg),
    on_completed      = lambda msg, *_: print(">>> COMPLETED", msg),
    on_error          = lambda msg, *_: print(">>> ERROR", msg),
    on_close          = lambda *_: print(">>> CLOSED"),
)
t.start(aformat="pcm", sample_rate=16000,
        enable_intermediate_result=True,
        enable_punctuation_prediction=True,
        enable_inverse_text_normalization=True)

print("录音 5 秒（播放视频）...")
mic = sc.get_microphone(id="BlackHole")
with mic.recorder(samplerate=16000, channels=1) as rec:
    for _ in range(50):
        data = rec.record(numframes=1600)
        if data.ndim > 1:
            data = data[:, 0]
        pcm = (np.clip(data, -1.0, 1.0) * 32767).astype("int16").tobytes()
        t.send_audio(pcm)

t.stop()
PY
