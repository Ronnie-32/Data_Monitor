[CmdletBinding()]
param(
    [string]$ExecutablePath,
    [ValidateRange(5, 300)]
    [int]$TimeoutSeconds = 45,
    [switch]$DisableQtWebEngineSandbox,
    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $ExecutablePath) {
    $ExecutablePath = Join-Path $Root "dist\DeskBoard\DeskBoard.exe"
}
$ExecutablePath = (Resolve-Path $ExecutablePath).Path
$InstallDirectory = Split-Path -Parent $ExecutablePath

$smokeId = "{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
$SmokeRoot = Join-Path $Root "build\smoke\$smokeId"
$LocalAppData = Join-Path $SmokeRoot "LocalAppData"
$StdoutPath = Join-Path $SmokeRoot "stdout.txt"
$StderrPath = Join-Path $SmokeRoot "stderr.txt"
New-Item -ItemType Directory -Force -Path $LocalAppData | Out-Null

$process = $null
try {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $ExecutablePath
    $startInfo.Arguments = "--smoke"
    $startInfo.WorkingDirectory = $InstallDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.EnvironmentVariables["LOCALAPPDATA"] = $LocalAppData
    if ($DisableQtWebEngineSandbox) {
        $startInfo.EnvironmentVariables["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw "Could not start packaged application: $ExecutablePath"
    }

    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        try { $process.Kill() } catch { }
        throw "Packaged application did not exit within $TimeoutSeconds seconds. Check for an existing DeskBoard instance or inspect $SmokeRoot."
    }
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    Set-Content -LiteralPath $StdoutPath -Value $stdout -Encoding UTF8
    Set-Content -LiteralPath $StderrPath -Value $stderr -Encoding UTF8

    if ($process.ExitCode -ne 0) {
        throw "Packaged application exited with code $($process.ExitCode). See $StdoutPath and $StderrPath."
    }

    $databasePath = Join-Path $LocalAppData "DeskBoard\data\deskboard.db"
    $logPath = Join-Path $LocalAppData "DeskBoard\logs\deskboard.log"
    if (-not (Test-Path -LiteralPath $databasePath -PathType Leaf)) {
        throw "Smoke launch did not create the expected database: $databasePath"
    }
    if (-not (Test-Path -LiteralPath $logPath -PathType Leaf)) {
        throw "Smoke launch did not create the expected log: $logPath"
    }

    $frontendPath = Get-ChildItem -LiteralPath $InstallDirectory -Recurse -File -Filter "index.html" |
        Where-Object { $_.FullName -match "deskboard[\\/]ui[\\/]dashboard[\\/]web[\\/]index\.html$" } |
        Select-Object -First 1
    $gridStackPath = Get-ChildItem -LiteralPath $InstallDirectory -Recurse -File -Filter "gridstack-all.js" |
        Where-Object { $_.FullName -match "deskboard[\\/]ui[\\/]dashboard[\\/]web[\\/]vendor[\\/]gridstack" } |
        Select-Object -First 1
    $webEngineProcess = Get-ChildItem -LiteralPath $InstallDirectory -Recurse -File -Filter "QtWebEngineProcess.exe" |
        Select-Object -First 1
    if (-not $frontendPath -or -not $gridStackPath -or -not $webEngineProcess) {
        throw "Packaged WebEngine/frontend asset check failed below $InstallDirectory"
    }

    Write-Host "PASS: packaged executable exited cleanly"
    Write-Host "PASS: LOCALAPPDATA database exists at $databasePath"
    Write-Host "PASS: LOCALAPPDATA log exists at $logPath"
    Write-Host "PASS: local frontend and GridStack assets are present"
    Write-Host "PASS: QtWebEngineProcess is present at $($webEngineProcess.FullName)"
    Write-Host "Smoke evidence: $SmokeRoot"
}
finally {
    if ($process) {
        $process.Dispose()
    }
    if ($Cleanup -and (Test-Path -LiteralPath $SmokeRoot)) {
        Remove-Item -LiteralPath $SmokeRoot -Recurse -Force
    }
}
