@echo off
setlocal

if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

pyinstaller --noconfirm --onefile --windowed --name JARVIS ^
  --add-data "data;data" ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  main.py

echo Build complete. EXE location: dist\JARVIS.exe
pause
