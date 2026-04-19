# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A desktop meeting subtitle tool that captures system audio (loopback), streams it to Aliyun NLS real-time speech recognition, and renders live Chinese subtitles in a frameless always-on-top overlay. Transcripts are also appended to timestamped log files.

## Setup and run

```bash
# Install the Aliyun NLS SDK (not on PyPI — install from GitHub)
pip install https://github.com/aliyun/alibabacloud-nls-python-sdk/archive/refs/heads/master.zip

# Install other dependencies
pip install -r requirements.txt

# First run: copy example config and fill in real credentials
cp config.ini.example config.ini
# Edit config.ini — set aliyun.access_key_id / access_key_secret / appkey

python main.py
```

There are no tests, lint, or build tooling configured — run `python main.py` to exercise changes end-to-end. UI changes must be verified by actually running the app, since Qt rendering cannot be validated any other way.

## Architecture

Data flows in one direction: `audio_capture → asr_client → subtitle_window + logger`. The pieces are loosely coupled through callbacks and Qt signals, wired together in `main.py`.

- **`audio_capture.LoopbackCapture`** — uses `soundcard` to open the default speaker as a loopback microphone, yielding 16 kHz mono int16 PCM frames (100 ms by default). Runs in a background `threading.Thread` started in `main.py`.
- **`asr_client.AliyunASR`** — wraps `nls.NlsSpeechTranscriber`. Exposes `start/send/stop`, and auto-reconnects every `RECONNECT_SECONDS` (9 min) because Aliyun's WebSocket session has a ~10 min hard limit. Also rebuilds the transcriber on send failure. Partial results fire `on_partial`; finalized sentences fire `on_final`. Access to `_transcriber` is guarded by `_lock` because `send` runs on the audio thread while `start/stop` run on the main thread.
- **`subtitle_window.SubtitleWindow`** — a `QWidget` (frameless, translucent, always-on-top, draggable). ASR callbacks must not touch widgets directly; they emit `partial_signal` / `final_signal`, which are Qt signals marshalled onto the UI thread. Partial text lives in a single yellow label at the bottom; finalized sentences scroll in the history above. Auto-scroll disengages when the user scrolls up (threshold check in `_check_auto_scroll`).
- **`token_manager.get_token`** — Aliyun tokens expire (~24 h). Tokens are cached in `.token_cache.json` and reused if >10 min of validity remains and the AK/region match.
- **`logger.TextLogger`** — opens `logs/meeting_<timestamp>.txt` on startup and appends one `[HH:MM:SS] text` line per finalized sentence.

## Things worth knowing before editing

- **Thread boundaries are load-bearing.** `nls` callbacks (`_on_result_changed`, `_on_sentence_end`) run on the SDK's internal thread. The audio generator runs on its own thread. Only the UI thread may touch widgets. Preserve the signal-based handoff in `SubtitleWindow` — do not call Qt methods directly from ASR callbacks.
- **Reconnect logic is in the `send` hot path.** Don't move `RECONNECT_SECONDS` handling elsewhere without accounting for the fact that audio arrives continuously; the time check piggybacks on incoming frames.
- **Loopback capture on macOS requires a virtual loopback device** (e.g., BlackHole) set as the system's default output, because macOS has no native speaker loopback. `soundcard`'s `include_loopback=True` works natively on Windows/Linux.
- **All UI strings and log headers are Chinese** (`会议字幕`, `会议记录`) — the tool is built for Mandarin meetings, and ASR is configured with Chinese defaults.
- **`config.ini` is gitignored-by-convention** (it holds real credentials); always edit `config.ini.example` when adding new config keys and update the `cfg[...]` reads in `main.py` accordingly.
