@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "SCRIPT=%ROOT_DIR%scripts\start_chatgpt_ngrok_url.ps1"

if not exist "%SCRIPT%" (
    echo [Overtli-Blender] Missing launcher script:
    echo   %SCRIPT%
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [Overtli-Blender] Stable ngrok Server URL launcher failed.
    echo Exit code: %EXIT_CODE%
    echo.
    echo This launcher needs:
    echo   .\.venv\Scripts\python.exe
    echo   ngrok.exe on PATH, tools\ngrok.exe, or OVERTLI_NGROK_EXE
    echo   OVERTLI_NGROK_URL or a saved ngrok static/dev domain
    echo.
    pause
)

exit /b %EXIT_CODE%
