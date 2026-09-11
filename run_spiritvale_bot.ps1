[CmdletBinding()]
param([switch]$Preview)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPython) {
    $python = $venvPython
} else {
    $pythonCommand = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "找不到 Python。請先執行 INSTALL.cmd。"
    }
    $python = $pythonCommand.Source
}

$arguments = @((Join-Path $PSScriptRoot "spiritvale_red_dot_bot.py"))
if ($Preview) {
    $arguments += "--no-loot"
} else {
    $arguments += "--run"
}

Push-Location $PSScriptRoot
try {
    & $python @arguments
    exit $LASTEXITCODE
} finally {
    Pop-Location
}

