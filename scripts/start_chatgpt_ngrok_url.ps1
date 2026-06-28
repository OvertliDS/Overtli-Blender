param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 2091,
    [string]$NgrokUrl = $env:OVERTLI_NGROK_URL,
    [switch]$AllowParallelTunnels
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$ToolsDir = Join-Path $Root "tools"
$LocalNgrokExe = Join-Path $ToolsDir "ngrok.exe"
$McpBaseUrl = "http://${HostAddress}:${Port}"
$McpUrl = "${McpBaseUrl}/mcp"
$HealthUrl = "${McpBaseUrl}/health"
$LocalStateDir = Join-Path $Root ".overtli_blender\local\chatgpt_ngrok_url"
$NgrokUrlPath = Join-Path $LocalStateDir "ngrok_url.txt"
$ServerUrlPath = Join-Path $LocalStateDir "server_url.txt"
$StdoutLogPath = Join-Path $LocalStateDir "ngrok.stdout.log"
$StderrLogPath = Join-Path $LocalStateDir "ngrok.stderr.log"
$NgrokApiTunnelsUrl = "http://127.0.0.1:4040/api/tunnels"
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

function Resolve-Ngrok {
    if ($env:OVERTLI_NGROK_EXE) {
        if (Test-Path -LiteralPath $env:OVERTLI_NGROK_EXE) {
            return $env:OVERTLI_NGROK_EXE
        }
        throw "OVERTLI_NGROK_EXE points to a missing file: $env:OVERTLI_NGROK_EXE"
    }
    if (Test-Path -LiteralPath $LocalNgrokExe) {
        return $LocalNgrokExe
    }
    $pathCommand = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($pathCommand) {
        return $pathCommand.Source
    }
    throw "ngrok.exe was not found. Install ngrok, put ngrok.exe on PATH, copy it to tools\ngrok.exe, or set OVERTLI_NGROK_EXE."
}

function Normalize-NgrokUrl([string]$Url) {
    $trimmed = ($Url -as [string]).Trim()
    $trimmed = $trimmed -replace '^[\s"''“”‘’<>]+', ''
    $trimmed = $trimmed -replace '[\s"''“”‘’<>]+$', ''
    if (-not $trimmed) {
        throw "Missing ngrok static/dev domain. Set OVERTLI_NGROK_URL or enter a domain such as https://example.ngrok-free.dev."
    }

    $urlMatches = [regex]::Matches($trimmed, 'https?://[^\s"''<>]+')
    if ($urlMatches.Count -gt 0) {
        $trimmed = $urlMatches[$urlMatches.Count - 1].Value
    }

    if ($trimmed -notmatch "^https?://") {
        $trimmed = "https://$trimmed"
    }

    $trimmed = $trimmed.TrimEnd("/")
    $trimmed = $trimmed -replace "/mcp$", ""
    $trimmed = $trimmed.TrimEnd("/")

    try {
        $uri = [System.Uri]::new($trimmed)
    } catch {
        throw "Invalid ngrok URL '$Url'. Enter only the assigned domain, for example https://example.ngrok-free.dev."
    }
    if (-not $uri.Scheme -or $uri.Scheme -notin @("http", "https") -or -not $uri.Host) {
        throw "Invalid ngrok URL '$Url'. Enter only the assigned domain, for example https://example.ngrok-free.dev."
    }
    if ($uri.AbsolutePath -and $uri.AbsolutePath -ne "/") {
        throw "Invalid ngrok URL '$Url'. Enter the base domain only, without a path."
    }

    return $uri.GetLeftPart([System.UriPartial]::Authority)
}

function Resolve-NgrokUrl {
    if ($NgrokUrl) {
        return Normalize-NgrokUrl $NgrokUrl
    }
    if (Test-Path -LiteralPath $NgrokUrlPath) {
        $saved = Get-Content -Raw -LiteralPath $NgrokUrlPath
        if ($saved.Trim()) {
            return Normalize-NgrokUrl $saved
        }
    }
    Write-Host "[Overtli-Blender] Enter your ngrok static/dev domain."
    Write-Host "[Overtli-Blender] Example: https://example.ngrok-free.dev"
    Write-Host "[Overtli-Blender] Find it in ngrok Dashboard > Gateway > Domains."
    $entered = Read-Host "ngrok URL"
    $normalized = Normalize-NgrokUrl $entered
    New-Item -ItemType Directory -Force -Path $LocalStateDir | Out-Null
    $normalized | Set-Content -NoNewline -LiteralPath $NgrokUrlPath
    return $normalized
}

function Get-NgrokApiTunnels {
    try {
        $response = Invoke-RestMethod -TimeoutSec 3 -Uri $NgrokApiTunnelsUrl
        if ($response -and $response.tunnels) {
            return @($response.tunnels)
        }
    } catch {
        return @()
    }
    return @()
}

function Get-MatchingNgrokApiTunnels([string]$StableUrl) {
    $stable = $StableUrl.TrimEnd("/")
    $matches = @()
    foreach ($tunnel in (Get-NgrokApiTunnels)) {
        $publicUrl = ($tunnel.public_url -as [string]).TrimEnd("/")
        if ($publicUrl -eq $stable) {
            $matches += $tunnel
        }
    }
    return $matches
}

function Remove-NgrokApiTunnel([object]$Tunnel) {
    $name = $Tunnel.name -as [string]
    if (-not $name) {
        return $false
    }
    try {
        $encodedName = [System.Uri]::EscapeDataString($name)
        Write-Host "[Overtli-Blender] Removing stale ngrok API tunnel '$name' for $($Tunnel.public_url)"
        Invoke-RestMethod -Method Delete -TimeoutSec 3 -Uri "${NgrokApiTunnelsUrl}/${encodedName}" | Out-Null
        return $true
    } catch {
        Write-Host "[Overtli-Blender] Warning: could not remove stale ngrok API tunnel '$name': $($_.Exception.Message)"
        return $false
    }
}

function Stop-StaleNgrokTunnels([string]$NgrokPath, [string]$StableUrl) {
    if ($AllowParallelTunnels) {
        Write-Host "[Overtli-Blender] AllowParallelTunnels is set; not stopping existing ngrok tunnels."
        return
    }
    $matchedApiTunnel = $false
    $removedApiTunnel = $false
    foreach ($tunnel in (Get-MatchingNgrokApiTunnels $StableUrl)) {
        $matchedApiTunnel = $true
        if (Remove-NgrokApiTunnel $tunnel) {
            $removedApiTunnel = $true
        }
    }
    if ($removedApiTunnel) {
        Start-Sleep -Seconds 1
    }

    $resolvedNgrok = try { (Resolve-Path -LiteralPath $NgrokPath).Path } catch { $NgrokPath }
    $escapedNgrok = [regex]::Escape($resolvedNgrok)
    $escapedBase = [regex]::Escape($McpBaseUrl)
    $escapedStable = [regex]::Escape($StableUrl)
    $ngrokProcesses = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -ieq "ngrok.exe" })
    $candidates = @()
    foreach ($process in $ngrokProcesses) {
        $commandLine = $process.CommandLine -as [string]
        $executablePath = $process.ExecutablePath -as [string]
        $sameExecutable = $executablePath -and ($executablePath -ieq $resolvedNgrok)
        $isExactLauncherTunnel =
            $commandLine -and
            ($commandLine -match $escapedNgrok -or $sameExecutable) -and
            $commandLine -match "\bhttp\b" -and
            ($commandLine -match $escapedBase -or $commandLine -match $escapedStable)
        $isOnlyBlankLocalNgrok =
            (-not $commandLine) -and
            ($sameExecutable -or $matchedApiTunnel) -and
            $ngrokProcesses.Count -eq 1

        if ($isExactLauncherTunnel -or $isOnlyBlankLocalNgrok) {
            $candidates += $process
        }
    }
    foreach ($process in $candidates) {
        try {
            Write-Host "[Overtli-Blender] Stopping stale ngrok process $($process.ProcessId) for $StableUrl"
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Host "[Overtli-Blender] Warning: could not stop stale ngrok process $($process.ProcessId): $($_.Exception.Message)"
        }
    }
}

function Start-NgrokTunnel([string]$NgrokPath, [string]$StableUrl) {
    Write-Host "[Overtli-Blender] Starting ngrok stable Server URL tunnel:"
    Write-Host "  $StableUrl -> $McpBaseUrl"
    Write-Host "[Overtli-Blender] Using ngrok: $NgrokPath"
    $tunnelArgs = @("http", "--url", $StableUrl, $McpBaseUrl)
    return Start-Process -FilePath $NgrokPath -ArgumentList $tunnelArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden -RedirectStandardOutput $StdoutLogPath -RedirectStandardError $StderrLogPath
}

function Wait-NgrokTunnelStarted([System.Diagnostics.Process]$Process) {
    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        if ($Process.HasExited) {
            $stderr = if (Test-Path -LiteralPath $StderrLogPath) { Get-Content -Raw -LiteralPath $StderrLogPath } else { "" }
            throw "ngrok exited early with code $($Process.ExitCode). $stderr"
        }
        Start-Sleep -Milliseconds 500
    }
}

function Test-NgrokAlreadyOnlineError([string]$Message) {
    return ($Message -match "ERR_NGROK_334" -or $Message -match "already online")
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
    $NgrokExe = Resolve-Ngrok
    $StableBaseUrl = Resolve-NgrokUrl
    $ServerUrl = "${StableBaseUrl}/mcp"

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
            "--profile", "browser_full_standard",
            "--remote-safety", "browser_standard",
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

    Stop-StaleNgrokTunnels $NgrokExe $StableBaseUrl

    try {
        $TunnelProcess = Start-NgrokTunnel $NgrokExe $StableBaseUrl
        Wait-NgrokTunnelStarted $TunnelProcess
    } catch {
        $firstError = $_.Exception.Message
        if (-not (Test-NgrokAlreadyOnlineError $firstError)) {
            throw
        }
        Write-Host "[Overtli-Blender] ngrok reported the endpoint is already online; cleaning stale local tunnel and retrying once."
        if ($TunnelProcess -and -not $TunnelProcess.HasExited) {
            Stop-Process -Id $TunnelProcess.Id -Force -ErrorAction SilentlyContinue
        }
        Stop-StaleNgrokTunnels $NgrokExe $StableBaseUrl
        Remove-Item -LiteralPath $StdoutLogPath, $StderrLogPath -Force -ErrorAction SilentlyContinue
        $TunnelProcess = Start-NgrokTunnel $NgrokExe $StableBaseUrl
        try {
            Wait-NgrokTunnelStarted $TunnelProcess
        } catch {
            $retryError = $_.Exception.Message
            if (Test-NgrokAlreadyOnlineError $retryError) {
                throw "ngrok endpoint '$StableBaseUrl' is already online and could not be stopped from this machine. Stop the existing endpoint in your local ngrok process or ngrok dashboard, then rerun this launcher. To intentionally share the same endpoint across multiple agents, run the launcher with -AllowParallelTunnels and configure ngrok pooling explicitly."
            }
            throw
        }
    }

    $ServerUrl | Set-Content -NoNewline -LiteralPath $ServerUrlPath

    Write-Host ""
    Write-Host "[Overtli-Blender] Stable ChatGPT Server URL is ready:" -ForegroundColor Green
    Write-Host "  $ServerUrl"
    Write-Host ""
    Write-Host "Use these ChatGPT connector settings:"
    Write-Host "  Connection:     Server URL"
    Write-Host "  Server URL:     $ServerUrl"
    Write-Host "  Authentication: No Auth"
    Write-Host ""
    Write-Host "[Overtli-Blender] Saved URL to:"
    Write-Host "  $ServerUrlPath"
    Write-Host ""
    Write-Host "[Overtli-Blender] Keep this window open while testing ChatGPT.com."
    Write-Host "[Overtli-Blender] The URL remains the same across restarts as long as your ngrok domain remains assigned."
    Open-SetupPage $ChatGptConnectorsUrl

    while (-not $TunnelProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
    exit $TunnelProcess.ExitCode
} catch {
    Write-Host ""
    Write-Host "[Overtli-Blender] Stable ngrok Server URL launcher failed:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)"
    exit 1
} finally {
    if ($TunnelProcess -and -not $TunnelProcess.HasExited) {
        Write-Host "[Overtli-Blender] Stopping ngrok tunnel process $($TunnelProcess.Id)."
        Stop-Process -Id $TunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($StartedServer -and $ServerProcess -and -not $ServerProcess.HasExited) {
        Write-Host "[Overtli-Blender] Stopping local MCP bridge process $($ServerProcess.Id)."
        Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
