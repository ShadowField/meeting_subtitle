import numpy as np
import soundcard as sc


class LoopbackCapture:
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 100,
        device_name: str = "BlackHole",
    ):
        self.sample_rate = sample_rate
        self.numframes = int(sample_rate * frame_ms / 1000)
        self.mic = sc.get_microphone(id=device_name)
        self._stop = False

    def frames(self):
        with self.mic.recorder(samplerate=self.sample_rate, channels=1) as rec:
            while not self._stop:
                data = rec.record(numframes=self.numframes)
                if data.ndim > 1:
                    data = data[:, 0]
                pcm16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
                yield pcm16

    def stop(self):
        self._stop = True
