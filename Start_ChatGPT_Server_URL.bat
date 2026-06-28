@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "SCRIPT=%ROOT_DIR%scripts\start_chatgpt_server_url.ps1"

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
    echo [Overtli-Blender] ChatGPT Server URL launcher stopped before it could stay running.
    echo Exit code: %EXIT_CODE%
    echo.
    echo This launcher needs:
    echo   .\.venv\Scripts\python.exe
    echo   tools\cloudflared.exe or cloudflared on PATH
    echo.
    echo If cloudflared is missing, the launcher attempts a local download into tools\cloudflared.exe.
    echo.
    pause
)

exit /b %EXIT_CODE%
