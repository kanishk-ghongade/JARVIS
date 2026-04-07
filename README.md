# JARVIS (Windows AI Assistant)

JARVIS is a bilingual (Hindi + English) desktop AI assistant designed for **online + offline** usage.

## Features
- Wake-word based voice assistant (`Hey Jarvis`)
- Offline STT with `faster-whisper`
- Offline TTS with `pyttsx3`
- System automation: open apps, screenshots, volume, shutdown/restart, folders, music, files
- Command history + logs dashboard (Tkinter)
- SQLite memory/log storage
- Online integrations (weather API now; ready for news/email/API extensions)
- Optional password lock via config

## Run (dev)
```bash
python -m pip install -r requirements.txt
python run_jarvis.py
```

## Build single Windows EXE
On a **Windows machine**, run:
```bat
build_windows_exe.bat
```
Output:
- `dist\JARVIS.exe`

## Notes
- Whisper model downloads on first run.
- For best Hindi support, keep your microphone quality good and use clear speech.
- You can configure wake word/password/API settings in `data/config.json`.

## Predefined commands
- `open chrome`
- `open notepad`
- `search on google <query>`
- `what is time`
- `take screenshot`
- `shutdown system`
- `restart system`
- `increase volume` / `decrease volume`
- `open folder`
- `play music`
- `send email`
- `tell weather`
- Hindi equivalents like `chrome kholo`, `time batao`, `screenshot lo`

