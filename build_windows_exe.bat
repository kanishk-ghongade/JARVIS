@echo off
setlocal
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --name JARVIS --collect-all faster_whisper --hidden-import=scipy run_jarvis.py
if %ERRORLEVEL% NEQ 0 (
  echo Build failed.
  exit /b 1
)
echo Build complete: dist\JARVIS.exe
endlocal
