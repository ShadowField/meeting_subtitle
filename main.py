import configparser
import os
import sys

import uvicorn

from asr_client import AliyunASR
from audio_capture import LoopbackCapture
from logger import TextLogger
from token_manager import get_token
import server


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
    server.logger = TextLogger(cfg["log"].get("save_dir", "./logs"))
    server.capture = LoopbackCapture(sample_rate=16000, frame_ms=100)

    server.asr = AliyunASR(
        url=url,
        appkey=appkey,
        token=token,
        on_partial=lambda text: server.broadcast_sync({"type": "partial", "text": text}),
        on_final=lambda text: (server.logger.write(text), server.broadcast_sync({"type": "final", "text": text})),
        on_error=lambda e: print("[ASR]", e),
    )

    print("[3/3] 启动 Web 服务，请在浏览器打开 http://localhost:8765")
    print(f"日志保存到: {server.logger.path}")

    try:
        uvicorn.run(server.app, host="127.0.0.1", port=8765, log_level="warning")
    finally:
        if server.capture:
            server.capture.stop()
        if server.asr:
            server.asr.stop()
        if server.logger:
            server.logger.close()


if __name__ == "__main__":
    main()
