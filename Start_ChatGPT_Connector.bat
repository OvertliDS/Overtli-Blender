@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "SCRIPT=%ROOT_DIR%scripts\start_chatgpt_connector.ps1"

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
    echo [Overtli-Blender] ChatGPT connector launcher stopped before it could stay running.
    echo Exit code: %EXIT_CODE%
    echo.
    echo Most common setup requirement:
    echo   $env:CONTROL_PLANE_API_KEY = "^<runtime-api-key^>"
    echo   $env:OVERTLI_TUNNEL_ID = "^<tunnel-id^>"
    echo   .\Start_ChatGPT_Connector.bat
    echo.
    echo Run those commands from PowerShell in this repo folder, or set the environment variables permanently.
    echo.
    pause
)

exit /b %EXIT_CODE%
