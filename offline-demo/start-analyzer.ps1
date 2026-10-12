$ErrorActionPreference = 'Stop'
$analyzerPort = 18767
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$analyzerPort/health" -TimeoutSec 2
    if ($health.service -eq 'architecture-pipeline-v2') { return }
    throw 'Analyzer port is used by another service.'
} catch {
    if ($_.Exception.Message -eq 'Analyzer port is used by another service.') { throw }
}
$pythonExecutable = Join-Path $PSScriptRoot 'python/python.exe'
$analyzerScript = Join-Path $PSScriptRoot 'code-analyzer.py'
$analyzerProcess = Start-Process -FilePath $pythonExecutable -ArgumentList @('-I',('"'+$analyzerScript+'"'),"$analyzerPort") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'analyzer.log') -RedirectStandardError (Join-Path $PSScriptRoot 'analyzer-error.log')
@{pid=$analyzerProcess.Id;executable=$pythonExecutable;start_ticks=$analyzerProcess.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'analyzer-process.json') -Encoding UTF8
for ($attempt=0;$attempt -lt 20;$attempt++) {
    if ($analyzerProcess.HasExited) { throw 'Analyzer failed to start. See analyzer-error.log.' }
    try { $health=Invoke-RestMethod -Uri "http://127.0.0.1:$analyzerPort/health" -TimeoutSec 1; if($health.service -eq 'architecture-pipeline-v2'){ return } } catch {}
    Start-Sleep -Milliseconds 100
}
throw 'Analyzer startup timed out.'
