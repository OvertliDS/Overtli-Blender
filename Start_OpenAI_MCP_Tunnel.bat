@echo off
setlocal

set "PROFILE=overtli-blender-http"
set "MCP_SERVER_URL=http://127.0.0.1:2091/mcp"
set "HEALTH_URL=http://127.0.0.1:2091/health"
set "ROOT_DIR=%~dp0"
set "TUNNEL_CLIENT_EXE=%ROOT_DIR%tools\tunnel-client.exe"

if "%OVERTLI_TUNNEL_PROFILE%" neq "" set "PROFILE=%OVERTLI_TUNNEL_PROFILE%"
if "%OVERTLI_MCP_SERVER_URL%" neq "" set "MCP_SERVER_URL=%OVERTLI_MCP_SERVER_URL%"
if "%OVERTLI_TUNNEL_CLIENT_EXE%" neq "" set "TUNNEL_CLIENT_EXE=%OVERTLI_TUNNEL_CLIENT_EXE%"

if not exist "%TUNNEL_CLIENT_EXE%" (
    where tunnel-client >nul 2>nul
    if errorlevel 1 (
        echo [Overtli-Blender] tunnel-client was not found at:
        echo   %TUNNEL_CLIENT_EXE%
        echo or on PATH.
        echo.
        echo Download it from OpenAI Platform tunnel settings or the latest openai/tunnel-client release:
        echo   https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
        exit /b 1
    )
    set "TUNNEL_CLIENT_EXE=tunnel-client"
)

if exist "%TUNNEL_CLIENT_EXE%" (
    echo [Overtli-Blender] Using tunnel client:
    echo   %TUNNEL_CLIENT_EXE%
) else (
    echo.
    echo [Overtli-Blender] Using tunnel client from PATH:
    echo   %TUNNEL_CLIENT_EXE%
)

if "%CONTROL_PLANE_API_KEY%" == "" (
    echo [Overtli-Blender] CONTROL_PLANE_API_KEY is not set.
    echo.
    echo Set a runtime API key for tunnel-client in this terminal before running this BAT:
    echo   PowerShell: $env:CONTROL_PLANE_API_KEY="sk-..."
    echo   cmd.exe:    set CONTROL_PLANE_API_KEY=sk-...
    exit /b 1
)

if "%OVERTLI_TUNNEL_ID%" == "" (
    echo [Overtli-Blender] OVERTLI_TUNNEL_ID is not set.
    echo.
    echo Create a tunnel in OpenAI Platform tunnel settings, then set:
    echo   PowerShell: $env:OVERTLI_TUNNEL_ID="tunnel_..."
    echo   cmd.exe:    set OVERTLI_TUNNEL_ID=tunnel_...
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "if ($env:OVERTLI_TUNNEL_ID -notmatch '^tunnel_[a-z0-9]{32}$') { exit 1 }"
if errorlevel 1 (
    echo [Overtli-Blender] OVERTLI_TUNNEL_ID must be the OpenAI tunnel ID, not the connector name or profile name.
    echo Expected format:
    echo   tunnel_0123456789abcdef0123456789abcdef
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "if ($env:OVERTLI_TUNNEL_ID -eq 'tunnel_0123456789abcdef0123456789abcdef' -or $env:OVERTLI_TUNNEL_ID -like 'tunnel_0123456789abcdef0123456789*') { exit 1 }"
if errorlevel 1 (
    echo [Overtli-Blender] OVERTLI_TUNNEL_ID is still the example placeholder, not a real OpenAI tunnel ID.
    echo Copy the real tunnel ID from OpenAI Platform tunnel settings.
    exit /b 1
)

echo [Overtli-Blender] Checking local MCP bridge health:
echo   %HEALTH_URL%
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 '%HEALTH_URL%'; if ($r.StatusCode -lt 200 -or $r.StatusCode -ge 300) { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
    echo.
    echo [Overtli-Blender] Local HTTP MCP bridge is not healthy.
    echo Start it first in another terminal:
    echo   .\Start_ChatGPT_MCP_Server.bat
    exit /b 1
)

echo.
echo [Overtli-Blender] Initializing tunnel-client profile:
echo   profile: %PROFILE%
echo   tunnel:  %OVERTLI_TUNNEL_ID%
echo   MCP URL: %MCP_SERVER_URL%
echo.
"%TUNNEL_CLIENT_EXE%" init --force --sample sample_mcp_remote_no_auth --profile "%PROFILE%" --tunnel-id "%OVERTLI_TUNNEL_ID%" --mcp-server-url "%MCP_SERVER_URL%"
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo [Overtli-Blender] Running tunnel-client doctor.
"%TUNNEL_CLIENT_EXE%" doctor --profile "%PROFILE%" --explain
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo [Overtli-Blender] Starting Secure MCP Tunnel client.
echo Keep this window open while testing ChatGPT.com.
echo Press Ctrl+C or close this window to stop the tunnel client.
echo.
"%TUNNEL_CLIENT_EXE%" run --profile "%PROFILE%"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [Overtli-Blender] Secure MCP Tunnel client stopped with exit code %EXIT_CODE%.
exit /b %EXIT_CODE%
