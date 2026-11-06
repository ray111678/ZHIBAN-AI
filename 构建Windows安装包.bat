@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where py >nul 2>nul || (echo 需要 Windows Python 3.10+ 用于构建。& pause & exit /b 1)
py -3 -m venv buildenv
call buildenv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name "智伴AI" --collect-all PySide6 --collect-all pyttsx3 main.py
if errorlevel 1 (echo PyInstaller 构建失败。& pause & exit /b 1)
where ISCC >nul 2>nul
if errorlevel 1 (
  echo EXE 已生成：dist\智伴AI\智伴AI.exe
  echo 如需安装程序，请安装 Inno Setup 后运行 installer.iss。
  pause
  exit /b 0
)
ISCC installer.iss
pause
