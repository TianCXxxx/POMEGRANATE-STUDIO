$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'stop-analyzer.ps1')
$pidPath = Join-Path $PSScriptRoot 'server-process.json'
if (-not (Test-Path -LiteralPath $pidPath)) { Write-Host 'No running demo recorded.'; exit }
$record = Get-Content -LiteralPath $pidPath -Raw | ConvertFrom-Json
$runtimeRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'runtime')) + [IO.Path]::DirectorySeparatorChar
$runtimeExe = [IO.Path]::GetFullPath($record.executable)
if (-not $runtimeExe.StartsWith($runtimeRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Recorded executable is outside this offline bundle.' }
$worker = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if ($worker -and $worker.Path -eq $runtimeExe -and $worker.StartTime.ToUniversalTime().Ticks -eq $record.start_ticks) { Stop-Process -Id $worker.Id; Write-Host 'Offline demo stopped.' }
