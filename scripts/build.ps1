[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$SkipInstaller,
    [string]$PythonPath,
    [string]$Version
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SpecPath = Join-Path $Root "installer\deskboard.spec"
$IssPath = Join-Path $Root "installer\deskboard.iss"
$DistBase = Join-Path $Root "dist"
$BuildBase = Join-Path $Root "build"
$OnedirPath = Join-Path $DistBase "DeskBoard"
$WorkPath = Join-Path $BuildBase "DeskBoard"

if (-not $PythonPath) {
    $PythonPath = Join-Path $Root ".venv\Scripts\python.exe"
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python runtime not found: $PythonPath"
}
if (-not (Test-Path -LiteralPath $SpecPath -PathType Leaf)) {
    throw "PyInstaller spec not found: $SpecPath"
}

function Remove-TaskOutput {
    param([Parameter(Mandatory = $true)][string]$Target)

    $resolvedTarget = [IO.Path]::GetFullPath($Target)
    $resolvedRoot = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if (-not $resolvedTarget.StartsWith($resolvedRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the repository: $resolvedTarget"
    }
    if (Test-Path -LiteralPath $resolvedTarget) {
        Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
    }
}

if ($Clean) {
    Remove-TaskOutput -Target $OnedirPath
    Remove-TaskOutput -Target $WorkPath
}

New-Item -ItemType Directory -Force -Path $DistBase, $BuildBase | Out-Null

Write-Host "Building DeskBoard onedir..."
$pyInstallerArguments = @(
    "-m", "PyInstaller",
    "--clean", "--noconfirm",
    "--distpath", $DistBase,
    "--workpath", $BuildBase,
    $SpecPath
)
& $PythonPath @pyInstallerArguments
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$ExecutablePath = Join-Path $OnedirPath "DeskBoard.exe"
if (-not (Test-Path -LiteralPath $ExecutablePath -PathType Leaf)) {
    throw "PyInstaller completed without the expected executable: $ExecutablePath"
}
$FrontendPath = Get-ChildItem -LiteralPath $OnedirPath -Recurse -File -Filter "index.html" |
    Where-Object { $_.FullName -match "deskboard[\\/]ui[\\/]dashboard[\\/]web[\\/]index\.html$" } |
    Select-Object -First 1
if (-not $FrontendPath) {
    throw "The packaged local Dashboard frontend was not found below $OnedirPath"
}
$GridStackPath = Get-ChildItem -LiteralPath $OnedirPath -Recurse -File -Filter "gridstack-all.js" |
    Where-Object { $_.FullName -match "deskboard[\\/]ui[\\/]dashboard[\\/]web[\\/]vendor[\\/]gridstack" } |
    Select-Object -First 1
if (-not $GridStackPath) {
    throw "The packaged local GridStack asset was not found below $OnedirPath"
}

Write-Host "Onedir output: $OnedirPath"
Write-Host "Executable: $ExecutablePath"
Write-Host "Frontend: $($FrontendPath.FullName)"
Write-Host "GridStack: $($GridStackPath.FullName)"

if ($SkipInstaller) {
    Write-Warning "Skipping Inno Setup compiler by request."
    exit 0
}

$isccCommand = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if (-not $isccCommand) {
    $knownIsccPaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
    if ($knownIsccPaths.Count -gt 0) {
        $isccPath = $knownIsccPaths[0]
    }
    else {
        throw "Inno Setup compiler ISCC.exe was not found. Install Inno Setup 6 or rerun with -SkipInstaller."
    }
}
else {
    $isccPath = $isccCommand.Source
}

if (-not $Version) {
    $projectText = Get-Content (Join-Path $Root "pyproject.toml") -Raw
    $versionMatch = [Regex]::Match($projectText, '(?m)^version\s*=\s*"([^"]+)"')
    if (-not $versionMatch.Success) {
        throw "Could not read the project version from pyproject.toml"
    }
    $Version = $versionMatch.Groups[1].Value
}

Write-Host "Building Inno Setup installer version $Version..."
& $isccPath "/DAppVersion=$Version" $IssPath
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}

$installerPath = Join-Path $DistBase "installer\DeskBoard-Setup-$Version.exe"
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Inno Setup completed without the expected installer: $installerPath"
}
Write-Host "Installer output: $installerPath"
