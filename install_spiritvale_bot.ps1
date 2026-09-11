[CmdletBinding()]
param(
    [string]$GameDirectory = "",
    [switch]$SkipPythonSetup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-GameDirectory {
    param([string]$RequestedDirectory)

    if ($RequestedDirectory) {
        return [IO.Path]::GetFullPath($RequestedDirectory)
    }

    $candidates = @(
        @(
            (Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\SpiritVale"),
            (Join-Path $env:ProgramFiles "Steam\steamapps\common\SpiritVale")
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    )

    if ($candidates.Count -gt 0) {
        return [IO.Path]::GetFullPath($candidates[0])
    }

    throw "找不到 SpiritVale。請用 -GameDirectory 指定遊戲資料夾。"
}

$gamePath = Find-GameDirectory -RequestedDirectory $GameDirectory
$bepInExCore = Join-Path $gamePath "BepInEx\core"
$loaderDirectory = Join-Path $gamePath "BepInEx\plugins\SpiritValeProbeLoader"
$probeDirectory = Join-Path $gamePath "BepInEx\ondemand\SpiritValePositionProbe"
$sourceLoaderDll = Join-Path $PSScriptRoot "SpiritValeProbeLoader.dll"
$sourceProbeDll = Join-Path $PSScriptRoot "SpiritValePositionProbe.dll"
$destinationLoaderDll = Join-Path $loaderDirectory "SpiritValeProbeLoader.dll"
$destinationProbeDll = Join-Path $probeDirectory "SpiritValePositionProbe.dll"
$legacyProbeDll = Join-Path `
    $gamePath `
    "BepInEx\plugins\SpiritValePositionProbe\SpiritValePositionProbe.dll"

if (-not (Test-Path -LiteralPath $bepInExCore)) {
    throw "找不到 BepInEx\core。請先為 SpiritVale 安裝 BepInEx 6 IL2CPP。"
}
if (-not (Test-Path -LiteralPath $sourceLoaderDll)) {
    throw "發佈包缺少 SpiritValeProbeLoader.dll。"
}
if (-not (Test-Path -LiteralPath $sourceProbeDll)) {
    throw "發佈包缺少 SpiritValePositionProbe.dll。"
}
if (Get-Process -Name "SpiritVale" -ErrorAction SilentlyContinue) {
    throw "SpiritVale 正在執行。請先完全關閉遊戲再重新安裝。"
}

New-Item -ItemType Directory -Path $loaderDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $probeDirectory -Force | Out-Null
Copy-Item -LiteralPath $sourceLoaderDll -Destination $destinationLoaderDll -Force
Copy-Item -LiteralPath $sourceProbeDll -Destination $destinationProbeDll -Force
if (Test-Path -LiteralPath $legacyProbeDll) {
    Remove-Item -LiteralPath $legacyProbeDll -Force
    Write-Host "已移除開機自動載入的舊探針：$legacyProbeDll"
}
Write-Host "已安裝輕量 Loader：$destinationLoaderDll"
Write-Host "已安裝按需探針：$destinationProbeDll"

if (-not $SkipPythonSetup) {
    $pythonCommand = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "找不到 Python。請先安裝 64 位元 Python 3.11 或更新版本。"
    }

    $python = $pythonCommand.Source
    & $python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 版本必須是 3.11 或更新版本。"
    }

    $venvDirectory = Join-Path $PSScriptRoot ".venv"
    $venvPython = Join-Path $venvDirectory "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $python -m venv $venvDirectory
        if ($LASTEXITCODE -ne 0) {
            throw "建立 Python 虛擬環境失敗。"
        }
    }
    & $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "安裝 Python 套件失敗。請確認網路連線後重試。"
    }
    Write-Host "Python 環境已完成：$venvDirectory"
}

$ipcDirectory = Join-Path $env:LOCALAPPDATA "SpiritValeBot"
New-Item -ItemType Directory -Path $ipcDirectory -Force | Out-Null
Write-Host "IPC 資料夾：$ipcDirectory"
Write-Host "安裝完成。啟動 SpiritVale 時只會載入 Loader；執行 Python 後才載入探針。"
