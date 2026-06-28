param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 2091,
    [string]$Profile = "overtli-blender-http"
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$LocalTunnelExe = Join-Path $Root "tools\tunnel-client.exe"
$TunnelExe = if ($env:OVERTLI_TUNNEL_CLIENT_EXE) { $env:OVERTLI_TUNNEL_CLIENT_EXE } elseif (Test-Path -LiteralPath $LocalTunnelExe) { $LocalTunnelExe } else { "tunnel-client" }
$ToolProfile = if ($env:OVERTLI_TUNNEL_PROFILE) { $env:OVERTLI_TUNNEL_PROFILE } else { $Profile }
$McpUrl = if ($env:OVERTLI_MCP_SERVER_URL) { $env:OVERTLI_MCP_SERVER_URL } else { "http://${HostAddress}:${Port}/mcp" }
$HealthUrl = "http://${HostAddress}:${Port}/health"
$LocalStateDir = Join-Path $Root ".overtli_blender\local\chatgpt_connector"
$RuntimeKeyPath = Join-Path $LocalStateDir "control_plane_api_key.dpapi"
$TunnelConfigPath = Join-Path $LocalStateDir "tunnel.json"
$RuntimeKeysUrl = "https://platform.openai.com/settings/organization/api-keys"
$TunnelsUrl = "https://platform.openai.com/settings/organization/tunnels"
$ServerProcess = $null
$StartedServer = $false

function Convert-SecureStringToPlainText([securestring]$SecureValue) {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Test-LocalBridgeHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 -Uri $HealthUrl
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
    } catch {
        return $false
    }
}

function Require-File([string]$Path, [string]$Message) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw $Message
    }
}

function Test-TunnelId([string]$TunnelId) {
    return $TunnelId -match '^tunnel_[a-z0-9]{32}$'
}

function Test-PlaceholderTunnelId([string]$TunnelId) {
    return $TunnelId -eq "tunnel_0123456789abcdef0123456789abcdef" -or $TunnelId -like "tunnel_0123456789abcdef0123456789*"
}

function Open-SetupPage([string]$Url, [string]$Purpose) {
    Write-Host "[Overtli-Blender] Opening ${Purpose}:"
    Write-Host "  $Url"
    try {
        Start-Process $Url | Out-Null
    } catch {
        Write-Host "[Overtli-Blender] Could not open browser automatically; paste the URL above into your browser."
    }
}

function Read-StoredRuntimeKey {
    if (-not (Test-Path -LiteralPath $RuntimeKeyPath)) {
        return $null
    }
    try {
        $secureValue = Get-Content -Raw -LiteralPath $RuntimeKeyPath | ConvertTo-SecureString
        return Convert-SecureStringToPlainText $secureValue
    } catch {
        Write-Host "[Overtli-Blender] Stored runtime API key could not be read; prompting again."
        return $null
    }
}

function Save-StoredRuntimeKey([string]$RuntimeKey) {
    New-Item -ItemType Directory -Force -Path $LocalStateDir | Out-Null
    $RuntimeKey | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Set-Content -NoNewline -LiteralPath $RuntimeKeyPath
}

function Read-StoredTunnelId {
    if (-not (Test-Path -LiteralPath $TunnelConfigPath)) {
        return $null
    }
    try {
        $config = Get-Content -Raw -LiteralPath $TunnelConfigPath | ConvertFrom-Json
        return $config.tunnel_id
    } catch {
        Write-Host "[Overtli-Blender] Stored tunnel config could not be read; prompting again."
        return $null
    }
}

function Save-StoredTunnelId([string]$TunnelId, [string]$ProfileName) {
    New-Item -ItemType Directory -Force -Path $LocalStateDir | Out-Null
    [ordered]@{
        tunnel_id = $TunnelId
        profile = $ProfileName
        mcp_server_url = $McpUrl
        saved_at = (Get-Date).ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath $TunnelConfigPath
}

try {
    Require-File $PythonExe "Missing virtual environment Python at $PythonExe. Run py -3.12 -m venv .venv and .\.venv\Scripts\python -m pip install -e ."

    if (-not (Test-Path -LiteralPath $TunnelExe)) {
        $resolved = Get-Command $TunnelExe -ErrorAction SilentlyContinue
        if (-not $resolved) {
            throw "Missing tunnel-client. Expected $LocalTunnelExe or tunnel-client on PATH."
        }
    }

    if (-not $env:CONTROL_PLANE_API_KEY) {
        $storedKey = Read-StoredRuntimeKey
        if ($storedKey) {
            Write-Host "[Overtli-Blender] Loaded runtime API key from local encrypted DPAPI storage."
            $env:CONTROL_PLANE_API_KEY = $storedKey
        } else {
            Write-Host "[Overtli-Blender] CONTROL_PLANE_API_KEY is not set."
            Open-SetupPage $RuntimeKeysUrl "OpenAI Platform runtime API key settings"
            $secureKey = Read-Host "Paste tunnel-client runtime API key" -AsSecureString
            $plainKey = Convert-SecureStringToPlainText $secureKey
            if (-not $plainKey) {
                throw "CONTROL_PLANE_API_KEY is required."
            }
            $env:CONTROL_PLANE_API_KEY = $plainKey
            Save-StoredRuntimeKey $plainKey
            Write-Host "[Overtli-Blender] Saved runtime API key to local Windows DPAPI-encrypted storage."
        }
    }

    if (-not $env:OVERTLI_TUNNEL_ID) {
        $storedTunnelId = Read-StoredTunnelId
        if ($storedTunnelId) {
            if (Test-PlaceholderTunnelId $storedTunnelId) {
                Write-Host "[Overtli-Blender] Stored tunnel ID is the example/placeholder value, not a real OpenAI tunnel ID; prompting again."
                Remove-Item -LiteralPath $TunnelConfigPath -Force -ErrorAction SilentlyContinue
            } else {
                Write-Host "[Overtli-Blender] Loaded tunnel ID from local config."
                $env:OVERTLI_TUNNEL_ID = $storedTunnelId
            }
        }
        if (-not $env:OVERTLI_TUNNEL_ID) {
            Write-Host "[Overtli-Blender] OVERTLI_TUNNEL_ID is not set."
            Write-Host "[Overtli-Blender] Create/select the tunnel in OpenAI Platform tunnel settings; tunnel creation requires admin privileges."
            Write-Host "[Overtli-Blender] Do not paste the connector name or the example ID; copy the real Platform ID that starts with tunnel_."
            Open-SetupPage $TunnelsUrl "OpenAI Platform tunnel settings"
            $tunnelId = Read-Host "Paste real OpenAI tunnel ID"
            if (-not $tunnelId) {
                throw "OVERTLI_TUNNEL_ID is required."
            }
            $env:OVERTLI_TUNNEL_ID = $tunnelId
            if (Test-TunnelId $env:OVERTLI_TUNNEL_ID -and -not (Test-PlaceholderTunnelId $env:OVERTLI_TUNNEL_ID)) {
                Save-StoredTunnelId $env:OVERTLI_TUNNEL_ID $ToolProfile
                Write-Host "[Overtli-Blender] Saved tunnel ID to local ignored config."
            }
        }
    }

    if (-not (Test-TunnelId $env:OVERTLI_TUNNEL_ID)) {
        throw "OVERTLI_TUNNEL_ID must be the OpenAI tunnel ID, not the connector name or profile name. Expected format: tunnel_ followed by 32 lowercase letters or digits."
    }
    if (Test-PlaceholderTunnelId $env:OVERTLI_TUNNEL_ID) {
        throw "OVERTLI_TUNNEL_ID is still the example/placeholder tunnel ID. Copy the real tunnel ID from OpenAI Platform tunnel settings."
    }

    if (Test-LocalBridgeHealth) {
        Write-Host "[Overtli-Blender] Reusing healthy local MCP bridge at $McpUrl"
    } else {
        Write-Host "[Overtli-Blender] Starting local MCP bridge at $McpUrl"
        $serverArgs = @(
            "-m", "overtli_blender.server",
            "--transport", "http",
            "--host", $HostAddress,
            "--port", "$Port",
            "--profile", "chatgpt_browser_default",
            "--remote-safety", "remote_browser_safe"
        )
        $ServerProcess = Start-Process -FilePath $PythonExe -ArgumentList $serverArgs -WorkingDirectory $Root -NoNewWindow -PassThru
        $StartedServer = $true

        $deadline = (Get-Date).AddSeconds(20)
        while ((Get-Date) -lt $deadline) {
            if ($ServerProcess.HasExited) {
                throw "Local MCP bridge exited early with code $($ServerProcess.ExitCode)."
            }
            if (Test-LocalBridgeHealth) {
                break
            }
            Start-Sleep -Milliseconds 500
        }
        if (-not (Test-LocalBridgeHealth)) {
            throw "Local MCP bridge did not become healthy at $HealthUrl."
        }
    }

    Write-Host "[Overtli-Blender] Using tunnel client: $TunnelExe"
    Write-Host "[Overtli-Blender] Initializing tunnel profile '$ToolProfile' for $McpUrl"
    & $TunnelExe init --force --sample sample_mcp_remote_no_auth --profile $ToolProfile --tunnel-id $env:OVERTLI_TUNNEL_ID --mcp-server-url $McpUrl
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[Overtli-Blender] Running tunnel-client doctor."
    & $TunnelExe doctor --profile $ToolProfile --explain
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[Overtli-Blender] Running Secure MCP Tunnel. Keep this window open."
    & $TunnelExe run --profile $ToolProfile
    exit $LASTEXITCODE
} catch {
    Write-Host ""
    Write-Host "[Overtli-Blender] Launcher failed:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)"
    exit 1
} finally {
    if ($StartedServer -and $ServerProcess -and -not $ServerProcess.HasExited) {
        Write-Host "[Overtli-Blender] Stopping local MCP bridge process $($ServerProcess.Id)."
        Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
