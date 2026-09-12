[CmdletBinding()]
param(
    [string]$GameDirectory = "C:\Program Files (x86)\Steam\steamapps\common\SpiritVale",
    [switch]$Install,
    [switch]$WaitForGameExit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourcePath = Join-Path $PSScriptRoot "SpiritValePositionProbe.cs"
$outputPath = Join-Path $PSScriptRoot "SpiritValePositionProbe.dll"
$loaderSourcePath = Join-Path $PSScriptRoot "SpiritValeProbeLoader.cs"
$loaderOutputPath = Join-Path $PSScriptRoot "SpiritValeProbeLoader.dll"
$bepInExDirectory = Join-Path $GameDirectory "BepInEx"
$coreDirectory = Join-Path $bepInExDirectory "core"
$compilerPath = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$runtimeRoot = "C:\Program Files\dotnet\shared\Microsoft.NETCore.App"

foreach ($requiredPath in @(
    $sourcePath,
    $loaderSourcePath,
    $compilerPath,
    $coreDirectory,
    $runtimeRoot
)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required build path was not found: $requiredPath"
    }
}

$runtimeDirectory = Get-ChildItem -LiteralPath $runtimeRoot -Directory |
    Sort-Object { [version]$_.Name } -Descending |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $runtimeDirectory) {
    throw "No .NET runtime was found under $runtimeRoot"
}

$runtimeReferences = @(
    "System.Private.CoreLib.dll",
    "System.Runtime.dll",
    "netstandard.dll",
    "System.Collections.dll",
    "System.Diagnostics.Process.dll",
    "System.IO.FileSystem.dll",
    "System.Threading.Thread.dll",
    "System.Text.Encoding.Extensions.dll",
    "System.Text.RegularExpressions.dll"
) | ForEach-Object { Join-Path $runtimeDirectory $_ }

$pluginReferences = @(
    "BepInEx.Core.dll",
    "BepInEx.Unity.Common.dll",
    "BepInEx.Unity.IL2CPP.dll",
    "Il2CppInterop.Runtime.dll",
    "0Harmony.dll"
) | ForEach-Object { Join-Path $coreDirectory $_ }

$references = @($runtimeReferences) + @($pluginReferences)
foreach ($reference in $references) {
    if (-not (Test-Path -LiteralPath $reference)) {
        throw "Compiler reference was not found: $reference"
    }
}

function Invoke-CSharpBuild {
    param(
        [string]$Source,
        [string]$Output,
        [string[]]$ExtraReferences = @()
    )

    $allReferences = @($references) + @($ExtraReferences)
    foreach ($reference in $allReferences) {
        if (-not (Test-Path -LiteralPath $reference)) {
            throw "Compiler reference was not found: $reference"
        }
    }
    $compilerArguments = @(
        "/nologo",
        "/noconfig",
        "/nostdlib",
        "/target:library",
        "/optimize+",
        "/out:$Output"
    )
    $compilerArguments += $allReferences | ForEach-Object { "/reference:$_" }
    $compilerArguments += $Source

    & $compilerPath @compilerArguments
    if ($LASTEXITCODE -ne 0) {
        throw "C# compiler failed with exit code $LASTEXITCODE for $Source"
    }

    $built = Get-Item -LiteralPath $Output
    Write-Host "Built $($built.FullName) ($($built.Length) bytes)"
}

function Get-Sha256Hex {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        try {
            $bytes = $sha256.ComputeHash($stream)
        }
        finally {
            $sha256.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
    return ([System.BitConverter]::ToString($bytes)).Replace("-", "")
}

Invoke-CSharpBuild -Source $sourcePath -Output $outputPath
Invoke-CSharpBuild -Source $loaderSourcePath -Output $loaderOutputPath

if ($Install) {
    $running = Get-Process -Name "SpiritVale" -ErrorAction SilentlyContinue
    if ($running) {
        if (-not $WaitForGameExit) {
            Write-Warning "SpiritVale is running and the loaded plugin DLL is locked."
            Write-Warning "Installation was deferred. Close the game, rerun this command with -Install, then start the game."
            return
        }
        Write-Host "Waiting for SpiritVale to exit before installing..."
        while ($running) {
            foreach ($process in @($running)) {
                try {
                    Wait-Process -Id $process.Id -ErrorAction Stop
                }
                catch [Microsoft.PowerShell.Commands.ProcessCommandException] {
                    # The process exited between discovery and Wait-Process.
                }
            }
            $running = Get-Process -Name "SpiritVale" -ErrorAction SilentlyContinue
        }
    }

    $loaderDirectory = Join-Path $bepInExDirectory "plugins\SpiritValeProbeLoader"
    $probeDirectory = Join-Path `
        $bepInExDirectory "ondemand\SpiritValePositionProbe"
    New-Item -ItemType Directory -Path $loaderDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $probeDirectory -Force | Out-Null

    $loaderDestination = Join-Path $loaderDirectory "SpiritValeProbeLoader.dll"
    $probeDestination = Join-Path $probeDirectory "SpiritValePositionProbe.dll"
    Copy-Item -LiteralPath $loaderOutputPath -Destination $loaderDestination -Force
    Copy-Item -LiteralPath $outputPath -Destination $probeDestination -Force
    $sourceProbeHash = Get-Sha256Hex -Path $outputPath
    $installedProbeHash = Get-Sha256Hex -Path $probeDestination
    if ($sourceProbeHash -ne $installedProbeHash) {
        throw "Installed probe hash did not match the built DLL."
    }

    $legacyProbe = Join-Path `
        $bepInExDirectory `
        "plugins\SpiritValePositionProbe\SpiritValePositionProbe.dll"
    if (Test-Path -LiteralPath $legacyProbe) {
        Remove-Item -LiteralPath $legacyProbe -Force
        Write-Host "Removed startup-loaded legacy probe: $legacyProbe"
    }

    Write-Host "Installed loader: $loaderDestination"
    Write-Host "Installed on-demand probe: $probeDestination"
    Write-Host "Installed probe SHA256: $installedProbeHash"
    Write-Host "Start SpiritVale; probe v2.23.5 loads only after Python starts."
}
