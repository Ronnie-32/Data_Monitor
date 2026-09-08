$ErrorActionPreference = 'Stop'

$localPython = Join-Path $PSScriptRoot '..\.venv\Scripts\pythonw.exe'
if (Test-Path -LiteralPath $localPython) {
    $python = (Resolve-Path -LiteralPath $localPython).Path
} else {
    $command = Get-Command 'pythonw.exe' -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show('没有找到 Python，请先安装 Python 和 PySide6。', '桌面图片贴') | Out-Null
        exit 1
    }
    $python = $command.Source
}

$script = Join-Path $PSScriptRoot 'app.py'
$processInfo = [System.Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = $python
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.ArgumentList.Add($script)
[System.Diagnostics.Process]::Start($processInfo) | Out-Null
