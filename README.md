# JARVIS (Windows Voice Assistant)

JARVIS is a practical AI voice assistant app with **online + offline mode** designed for Windows laptops.

## Delivered capabilities

- Continuous voice listening with wake word: **"Hey Jarvis"**.
- Offline-friendly STT pipeline using `faster-whisper` (preferred) with fallback path.
- Hindi + English command understanding and speech output.
- Offline TTS via `pyttsx3`.
- Command brain with history/memory using SQLite.
- System control: open/close apps, screenshots, files, volume, shutdown/restart, folder open.
- Online integrations (optional keys): weather + email + future API extensions.
- Tkinter dashboard with listening status, command history, and logs.
- Optional password lock through `JARVIS_PASSWORD_HASH`.

## Quick start (development)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build a single Windows `.exe`

Run this on a **Windows machine**:

```bat
build_windows_exe.bat
```

Output:

- `dist\\JARVIS.exe` (double-click to run)

## Environment variables (optional)

- `WEATHER_API_KEY`
- `OPENAI_API_KEY`
- `NEWS_API_KEY`
- `JARVIS_EMAIL`
- `JARVIS_EMAIL_PASSWORD`
- `JARVIS_PASSWORD_HASH` (SHA256 hash of password)

## Important notes

1. Offline core features (voice loop, TTS, local commands) are implemented.
2. For best offline bilingual accuracy, ship Whisper model files with the final EXE installer image.
3. `PyAudio` wheels should be installed in Windows build environment before packaging.
4. Some high-risk commands (shutdown/restart/delete) should be protected with future policy prompts.
