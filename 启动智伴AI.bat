@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Python。源码调试模式需要 Python 3.10+。
  echo 普通用户请使用 Windows 安装包，不需要安装 Python。
  pause
  exit /b 1
)
py -3 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
pause
