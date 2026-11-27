@echo off
rem Mo ung dung buoi do bang nhap dup (khong can go lenh).
rem Dung Python cua repo (.venv); pythonw khong mo cua so dong lenh.
cd /d "%~dp0.."
if not exist ".venv\Scripts\pythonw.exe" (
    echo Khong tim thay .venv\Scripts\pythonw.exe trong %CD%
    echo Cai moi truong Python theo README truoc khi mo ung dung.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "scripts\session_app.py"
