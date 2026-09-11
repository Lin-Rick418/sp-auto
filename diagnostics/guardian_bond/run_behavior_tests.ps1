$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeDir = Get-ChildItem 'C:\Program Files\dotnet\shared\Microsoft.NETCore.App' -Directory |
    Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1 -ExpandProperty FullName
$refs = @('System.Private.CoreLib.dll','System.Runtime.dll','System.Console.dll',
    'System.Collections.dll','System.Reflection.dll','System.Reflection.Extensions.dll',
    'System.Runtime.Extensions.dll') | ForEach-Object { '/reference:' + (Join-Path $runtimeDir $_) }
$outputDll = Join-Path $PSScriptRoot 'ProbeBehaviorTests.dll'
& 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe' /nologo /noconfig /nostdlib /target:exe "/out:$outputDll" $refs (Join-Path $PSScriptRoot 'ProbeBehaviorTests.cs')
if ($LASTEXITCODE -ne 0) { throw 'Behavior test compilation failed' }
Set-Content (Join-Path $PSScriptRoot 'ProbeBehaviorTests.runtimeconfig.json') '{"runtimeOptions":{"tfm":"net6.0","framework":{"name":"Microsoft.NETCore.App","version":"6.0.0"}}}'
& dotnet $outputDll (Join-Path $workspace 'SpiritValePositionProbe.dll') 'C:\Program Files (x86)\Steam\steamapps\common\SpiritVale\BepInEx\core'
if ($LASTEXITCODE -ne 0) { throw 'Probe behavior tests failed' }
