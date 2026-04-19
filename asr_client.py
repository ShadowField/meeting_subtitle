import json
import threading
import time

import nls


class AliyunASR:
    RECONNECT_SECONDS = 9 * 60

    def __init__(
        self,
        url: str,
        appkey: str,
        token: str,
        on_partial,
        on_final,
        on_error=None,
    ):
        self.url = url
        self.appkey = appkey
        self.token = token
        self.on_partial = on_partial
        self.on_final = on_final
        self.on_error = on_error or (lambda msg: print("[asr-err]", msg))
        self._transcriber = None
        self._lock = threading.Lock()
        self._started_at = 0.0
        self._running = False

    def _on_result_changed(self, message, *_):
        try:
            result = json.loads(message)["payload"]["result"]
            self.on_partial(result)
        except Exception:
            pass

    def _on_sentence_end(self, message, *_):
        try:
            result = json.loads(message)["payload"]["result"]
            self.on_final(result)
        except Exception:
            pass

    def _on_err(self, message, *_):
        self.on_error(str(message))

    def _build(self):
        t = nls.NlsSpeechTranscriber(
            url=self.url,
            token=self.token,
            appkey=self.appkey,
            on_start=lambda *a: None,
            on_sentence_begin=lambda *a: None,
            on_sentence_end=self._on_sentence_end,
            on_result_changed=self._on_result_changed,
            on_completed=lambda *a: None,
            on_error=self._on_err,
            on_close=lambda *a: None,
        )
        t.start(
            aformat="pcm",
            sample_rate=16000,
            enable_intermediate_result=True,
            enable_punctuation_prediction=True,
            enable_inverse_text_normalization=True,
        )
        return t

    def start(self):
        with self._lock:
            self._transcriber = self._build()
            self._started_at = time.time()
            self._running = True

    def send(self, pcm_bytes: bytes):
        if not self._running:
            return
        with self._lock:
            if time.time() - self._started_at > self.RECONNECT_SECONDS:
                try:
                    self._transcriber.stop()
                except Exception:
                    pass
                self._transcriber = self._build()
                self._started_at = time.time()
            try:
                self._transcriber.send_audio(pcm_bytes)
            except Exception as e:
                self.on_error(f"send failed: {e}")
                try:
                    self._transcriber = self._build()
                    self._started_at = time.time()
                except Exception as ee:
                    self.on_error(f"rebuild failed: {ee}")

    def stop(self):
        self._running = False
        with self._lock:
            if self._transcriber is not None:
                try:
                    self._transcriber.stop()
                except Exception:
                    pass
                self._transcriber = None
