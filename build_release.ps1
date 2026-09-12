[CmdletBinding()]
param([string]$Version = "2.23.5")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$distRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "dist"))
$stageDirectory = [IO.Path]::GetFullPath(
    (Join-Path $distRoot "SpiritValeBot-v$Version")
)
$zipPath = [IO.Path]::GetFullPath(
    (Join-Path $distRoot "SpiritValeBot-v$Version-win64.zip")
)
$workspaceRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
$filterDefaultPath = Join-Path $PSScriptRoot `
    "spiritvale_equipment_filter.default.json"

if (
    -not ($stageDirectory.StartsWith(
        $workspaceRoot, [StringComparison]::OrdinalIgnoreCase
    )) -or -not ($zipPath.StartsWith(
        $workspaceRoot, [StringComparison]::OrdinalIgnoreCase
    ))
) {
    throw "Release target is outside the workspace."
}

$files = @(
    "SpiritValeProbeLoader.dll",
    "SpiritValePositionProbe.dll",
    "spiritvale_paths.py",
    "spiritvale_red_dot_bot.py",
    "spiritvale_config.py",
    "spiritvale_models.py",
    "spiritvale_snapshot.py",
    "spiritvale_ipc.py",
    "spiritvale_navigation.py",
    "spiritvale_loot.py",
    "spiritvale_upkeep.py",
    "spiritvale_earnings.py",
    "spiritvale_card_buyer.py",
    "spiritvale_equipment_filter.py",
    "spiritvale_inventory_pricer.py",
    "spiritvale_auction_query.py",
    "spiritvale_position_reporter.py",
    "spiritvale_bot_config.json",
    "spiritvale_mode_config.json",
    "requirements.txt",
    "install_spiritvale_bot.ps1",
    "run_spiritvale_bot.ps1",
    "INSTALL.cmd",
    "RUN_BOT.cmd",
    "RUN_PREVIEW.cmd",
    "README_RELEASE.md"
)

foreach ($file in $files) {
    $source = Join-Path $PSScriptRoot $file
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing release file: $source"
    }
}
if (-not (Test-Path -LiteralPath $filterDefaultPath)) {
    throw "Missing release file: $filterDefaultPath"
}

# Windows PowerShell 5.1 treats UTF-8 without a BOM as the local ANSI code page.
# These scripts contain localized messages, so require a BOM to prevent parser
# corruption on systems whose active code page is not UTF-8.
foreach ($file in @("install_spiritvale_bot.ps1", "run_spiritvale_bot.ps1")) {
    $source = Join-Path $PSScriptRoot $file
    $bytes = [IO.File]::ReadAllBytes($source)
    if (($bytes.Length -lt 3) -or
        ($bytes[0] -ne 0xEF) -or
        ($bytes[1] -ne 0xBB) -or
        ($bytes[2] -ne 0xBF)) {
        throw "Windows PowerShell script must be UTF-8 with BOM: $source"
    }
}

New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
if (Test-Path -LiteralPath $stageDirectory) {
    Remove-Item -LiteralPath $stageDirectory -Recurse -Force
}
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
New-Item -ItemType Directory -Path $stageDirectory | Out-Null

foreach ($file in $files) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) `
        -Destination (Join-Path $stageDirectory $file)
}
Copy-Item -LiteralPath $filterDefaultPath `
    -Destination (Join-Path $stageDirectory "spiritvale_equipment_filter.json")

Compress-Archive -LiteralPath $stageDirectory -DestinationPath $zipPath `
    -CompressionLevel Optimal
Write-Host "Created: $zipPath"
