# JARVIS (Windows Voice Assistant)

JARVIS is a practical AI voice assistant app with **online + offline mode** designed for Windows laptops.

## What you asked: "Direct .exe to run"

I cannot physically send a binary `.exe` file through this chat session. However, this repo includes a **one-click Windows script** that generates and launches `JARVIS.exe` for you.

### Fastest way (Windows laptop)

1. Install Python 3.11 (from python.org) with **"Add Python to PATH"** enabled.
2. Download this project folder.
3. Double-click:

```bat
build_and_run_windows.bat
```

This script will:
- create `.venv`
- install required packages
- build `dist\\JARVIS.exe`
- auto-launch it

After first build, you can directly run:

- `dist\\JARVIS.exe` (double-click)

## Delivered capabilities

- Continuous voice listening with wake word: **"Hey Jarvis"**.
- Offline-friendly STT pipeline using `faster-whisper` (preferred).
- Hindi + English command understanding and speech output.
- Offline TTS via `pyttsx3`.
- Command brain with history/memory using SQLite.
- System control: open/close apps, screenshots, files, volume, shutdown/restart, folder open.
- Online integrations (optional keys): weather + email + future API extensions.
- Tkinter dashboard with listening status, command history, and logs.
- Optional password lock through `JARVIS_PASSWORD_HASH`.

## Alternate build command

If you want manual control:

```bat
build_windows_exe.bat
```

Output:
- `dist\\JARVIS.exe`

## Environment variables (optional)

- `WEATHER_API_KEY`
- `OPENAI_API_KEY`
- `NEWS_API_KEY`
- `JARVIS_EMAIL`
- `JARVIS_EMAIL_PASSWORD`
- `JARVIS_PASSWORD_HASH` (SHA256 hash of password)

## Notes

1. Offline core features (voice loop, TTS, local commands) are implemented.
2. For best offline bilingual accuracy, ensure Whisper model files are available in first run.
3. `PyAudio` wheels should be installed in Windows build environment before packaging.
