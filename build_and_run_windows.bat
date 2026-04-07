@echo off
setlocal

echo [1/5] Preparing Python virtual environment...
if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate

echo [2/5] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/5] Building JARVIS.exe...
pyinstaller --noconfirm --clean --onefile --windowed --name JARVIS ^
  --add-data "data;data" ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  main.py

if not exist dist\JARVIS.exe (
  echo Build failed. dist\JARVIS.exe not found.
  exit /b 1
)

echo [4/5] Build complete: dist\JARVIS.exe
echo [5/5] Launching JARVIS...
start "" dist\JARVIS.exe

echo Done. You can now double-click dist\JARVIS.exe anytime.
