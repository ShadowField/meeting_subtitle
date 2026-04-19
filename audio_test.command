#!/bin/bash
cd "$(dirname "$0")"
unset QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH DYLD_LIBRARY_PATH DYLD_FRAMEWORK_PATH
./.venv/bin/python - <<'PY'
import soundcard as sc, numpy as np, time

mic = sc.get_microphone(id="BlackHole")
print("开始录音 3 秒，请播放声音或说话...")
with mic.recorder(samplerate=16000, channels=1) as rec:
    data = rec.record(numframes=16000 * 3)
rms = np.sqrt(np.mean(data**2))
print(f"音量 RMS: {rms:.6f}")
if rms < 0.001:
    print("❌ 几乎没有声音 — 系统输出没有走 BlackHole，请检查多输出设备设置")
else:
    print("✅ 检测到声音，BlackHole 正常采集中")
PY
