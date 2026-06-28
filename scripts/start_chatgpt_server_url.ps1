param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 2091,
    [switch]$AllowParallelTunnels
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$ToolsDir = Join-Path $Root "tools"
$LocalCloudflaredExe = Join-Path $ToolsDir "cloudflared.exe"
$CloudflaredDownloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$CloudflaredExe = $null
$McpBaseUrl = "http://${HostAddress}:${Port}"
$McpUrl = "${McpBaseUrl}/mcp"
$HealthUrl = "${McpBaseUrl}/health"
$LocalStateDir = Join-Path $Root ".overtli_blender\local\chatgpt_server_url"
$StdoutLogPath = Join-Path $LocalStateDir "cloudflared.stdout.log"
$StderrLogPath = Join-Path $LocalStateDir "cloudflared.stderr.log"
$PublicUrlPath = Join-Path $LocalStateDir "server_url.txt"
$ChatGptConnectorsUrl = "https://chatgpt.com/#settings/Connectors"
$ServerProcess = $null
$TunnelProcess = $null
$StartedServer = $false

function Require-File([string]$Path, [string]$Message) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw $Message
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

function Resolve-Cloudflared {
    if ($env:OVERTLI_CLOUDFLARED_EXE) {
        if (Test-Path -LiteralPath $env:OVERTLI_CLOUDFLARED_EXE) {
            return $env:OVERTLI_CLOUDFLARED_EXE
        }
        throw "OVERTLI_CLOUDFLARED_EXE points to a missing file: $env:OVERTLI_CLOUDFLARED_EXE"
    }
    if (Test-Path -LiteralPath $LocalCloudflaredExe) {
        return $LocalCloudflaredExe
    }
    $pathCommand = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($pathCommand) {
        return $pathCommand.Source
    }

    Write-Host "[Overtli-Blender] cloudflared was not found locally or on PATH."
    Write-Host "[Overtli-Blender] Downloading Cloudflare Tunnel client to ignored local tools folder:"
    Write-Host "  $LocalCloudflaredExe"
    New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri $CloudflaredDownloadUrl -OutFile $LocalCloudflaredExe
    if (-not (Test-Path -LiteralPath $LocalCloudflaredExe)) {
        throw "cloudflared download did not create $LocalCloudflaredExe"
    }
    return $LocalCloudflaredExe
}

function Read-CloudflaredPublicUrl {
    $content = ""
    foreach ($path in @($StdoutLogPath, $StderrLogPath)) {
        if (Test-Path -LiteralPath $path) {
            $content += "`n" + (Get-Content -Raw -LiteralPath $path)
        }
    }
    $matches = [regex]::Matches($content, "https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    if ($matches.Count -gt 0) {
        return $matches[$matches.Count - 1].Value.TrimEnd("/")
    }
    return $null
}

function Stop-StaleQuickTunnels([string]$CloudflaredPath) {
    if ($AllowParallelTunnels) {
        Write-Host "[Overtli-Blender] AllowParallelTunnels is set; not stopping existing quick tunnels."
        return
    }

    $resolvedCloudflared = try { (Resolve-Path -LiteralPath $CloudflaredPath).Path } catch { $CloudflaredPath }
    $escapedCloudflared = [regex]::Escape($resolvedCloudflared)
    $escapedUrl = [regex]::Escape($McpBaseUrl)
    $candidates = Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -ieq "cloudflared.exe" -and
            $_.CommandLine -match $escapedCloudflared -and
            $_.CommandLine -match "\btunnel\b" -and
            $_.CommandLine -match "--url\s+$escapedUrl"
        }

    foreach ($process in $candidates) {
        try {
            Write-Host "[Overtli-Blender] Stopping stale Cloudflare quick tunnel process $($process.ProcessId) for $McpBaseUrl"
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Host "[Overtli-Blender] Warning: could not stop stale Cloudflare process $($process.ProcessId): $($_.Exception.Message)"
        }
    }
}

function Open-SetupPage([string]$Url) {
    try {
        Start-Process $Url | Out-Null
    } catch {
        Write-Host "[Overtli-Blender] Could not open ChatGPT automatically; paste the URL below into your browser."
        Write-Host "  $Url"
    }
}

try {
    Require-File $PythonExe "Missing virtual environment Python at $PythonExe. Run py -3.12 -m venv .venv and .\.venv\Scripts\python -m pip install -e ."
    $CloudflaredExe = Resolve-Cloudflared

    New-Item -ItemType Directory -Force -Path $LocalStateDir | Out-Null
    Remove-Item -LiteralPath $StdoutLogPath, $StderrLogPath -Force -ErrorAction SilentlyContinue

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
            "--remote-safety", "remote_browser_safe",
            "--allow-public-tunnel-hosts"
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

    Stop-StaleQuickTunnels $CloudflaredExe

    Write-Host "[Overtli-Blender] Starting Cloudflare quick tunnel for $McpBaseUrl"
    Write-Host "[Overtli-Blender] Using cloudflared: $CloudflaredExe"
    $tunnelArgs = @("tunnel", "--url", $McpBaseUrl)
    $TunnelProcess = Start-Process -FilePath $CloudflaredExe -ArgumentList $tunnelArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden -RedirectStandardOutput $StdoutLogPath -RedirectStandardError $StderrLogPath

    $publicBaseUrl = $null
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if ($TunnelProcess.HasExited) {
            $stderr = if (Test-Path -LiteralPath $StderrLogPath) { Get-Content -Raw -LiteralPath $StderrLogPath } else { "" }
            throw "cloudflared exited early with code $($TunnelProcess.ExitCode). $stderr"
        }
        $publicBaseUrl = Read-CloudflaredPublicUrl
        if ($publicBaseUrl) {
            break
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $publicBaseUrl) {
        throw "Cloudflare quick tunnel did not publish a trycloudflare.com URL within 60 seconds. See $StderrLogPath"
    }

    $serverUrl = "${publicBaseUrl}/mcp"
    $serverUrl | Set-Content -NoNewline -LiteralPath $PublicUrlPath

    Write-Host ""
    Write-Host "[Overtli-Blender] ChatGPT Server URL is ready:" -ForegroundColor Green
    Write-Host "  $serverUrl"
    Write-Host ""
    Write-Host "Use these ChatGPT connector settings:"
    Write-Host "  Connection:     Server URL"
    Write-Host "  Server URL:     $serverUrl"
    Write-Host "  Authentication: No Auth"
    Write-Host ""
    Write-Host "[Overtli-Blender] Saved URL to:"
    Write-Host "  $PublicUrlPath"
    Write-Host ""
    Write-Host "[Overtli-Blender] Keep this window open while testing ChatGPT.com."
    Write-Host "[Overtli-Blender] Closing this window stops the public tunnel."
    Write-Host ""
    Write-Host "[Overtli-Blender] Important: Cloudflare quick-tunnel URLs are temporary." -ForegroundColor Yellow
    Write-Host "[Overtli-Blender] A new run usually creates a different trycloudflare.com URL."
    Write-Host "[Overtli-Blender] If ChatGPT will not let you edit the Server URL, delete/recreate that test connector."
    Write-Host "[Overtli-Blender] For a stable ChatGPT connector, use Start_ChatGPT_Connector.bat with OpenAI Secure MCP Tunnel."
    Open-SetupPage $ChatGptConnectorsUrl

    while (-not $TunnelProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
    exit $TunnelProcess.ExitCode
} catch {
    Write-Host ""
    Write-Host "[Overtli-Blender] Server URL launcher failed:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)"
    exit 1
} finally {
    if ($TunnelProcess -and -not $TunnelProcess.HasExited) {
        Write-Host "[Overtli-Blender] Stopping Cloudflare tunnel process $($TunnelProcess.Id)."
        Stop-Process -Id $TunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($StartedServer -and $ServerProcess -and -not $ServerProcess.HasExited) {
        Write-Host "[Overtli-Blender] Stopping local MCP bridge process $($ServerProcess.Id)."
        Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
