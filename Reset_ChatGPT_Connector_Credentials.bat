@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "LOCAL_STATE_DIR=%ROOT_DIR%.overtli_blender\local\chatgpt_connector"

if exist "%LOCAL_STATE_DIR%" (
    echo [Overtli-Blender] Removing local ChatGPT connector credential/config state:
    echo   %LOCAL_STATE_DIR%
    rmdir /s /q "%LOCAL_STATE_DIR%"
    if errorlevel 1 (
        echo [Overtli-Blender] Failed to remove local state.
        pause
        exit /b 1
    )
    echo [Overtli-Blender] Removed local connector state.
) else (
    echo [Overtli-Blender] No local ChatGPT connector state found.
)

echo.
echo This did not revoke keys or delete tunnels in OpenAI Platform.
pause
