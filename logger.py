import os
from datetime import datetime


class TextLogger:
    def __init__(self, save_dir: str = "./logs"):
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.abspath(os.path.join(save_dir, f"meeting_{ts}.txt"))
        self._fp = open(self.path, "w", encoding="utf-8")
        self._fp.write(f"# 会议记录 {ts}\n\n")
        self._fp.flush()

    def write(self, text: str):
        text = text.strip()
        if not text:
            return
        now = datetime.now().strftime("%H:%M:%S")
        self._fp.write(f"[{now}] {text}\n")
        self._fp.flush()

    def write_claude(self, text: str):
        text = text.strip()
        if not text:
            return
        now = datetime.now().strftime("%H:%M:%S")
        self._fp.write(f"[{now}] [Claude]: {text}\n")
        self._fp.flush()

    def close(self):
        try:
            self._fp.close()
        except Exception:
            pass
