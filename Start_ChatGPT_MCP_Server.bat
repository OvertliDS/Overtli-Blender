@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"
set "HOST=127.0.0.1"
set "PORT=2091"
set "PROFILE=chatgpt_browser_default"
set "REMOTE_SAFETY=remote_browser_safe"

cd /d "%ROOT_DIR%"

if not exist "%PYTHON_EXE%" (
    echo [Overtli-Blender] Missing virtual environment Python:
    echo   %PYTHON_EXE%
    echo.
    echo Create and install it first:
    echo   py -3.12 -m venv .venv
    echo   .\.venv\Scripts\python -m pip install -e .
    exit /b 1
)

echo [Overtli-Blender] Starting ChatGPT browser MCP bridge.
echo.
echo Local MCP endpoint:
echo   http://%HOST%:%PORT%/mcp
echo.
echo Local health endpoint:
echo   http://%HOST%:%PORT%/health
echo.
echo Keep this window open while using ChatGPT.com through your HTTPS tunnel.
echo Press Ctrl+C or close this window to stop the attached server process.
echo.

"%PYTHON_EXE%" -m overtli_blender.server --transport http --host %HOST% --port %PORT% --profile %PROFILE% --remote-safety %REMOTE_SAFETY%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [Overtli-Blender] ChatGPT browser MCP bridge stopped with exit code %EXIT_CODE%.
exit /b %EXIT_CODE%
