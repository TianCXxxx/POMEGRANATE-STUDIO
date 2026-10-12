$ErrorActionPreference = 'Stop'
$analyzerRecordPath = Join-Path $PSScriptRoot 'analyzer-process.json'
if (-not (Test-Path -LiteralPath $analyzerRecordPath)) { return }
$analyzerRecord = Get-Content -LiteralPath $analyzerRecordPath -Raw | ConvertFrom-Json
$allowedExecutable = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'python/python.exe'))
if ([IO.Path]::GetFullPath($analyzerRecord.executable) -ne $allowedExecutable) { throw 'Invalid analyzer process record.' }
$analyzerWorker = Get-Process -Id $analyzerRecord.pid -ErrorAction SilentlyContinue
if ($analyzerWorker -and $analyzerWorker.Path -eq $allowedExecutable -and $analyzerWorker.StartTime.ToUniversalTime().Ticks -eq $analyzerRecord.start_ticks) {
    Stop-Process -Id $analyzerWorker.Id
}
Remove-Item -LiteralPath $analyzerRecordPath
