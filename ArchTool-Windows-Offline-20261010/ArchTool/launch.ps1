param([switch]$NoBrowser, [int]$Port = 18765)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'start-analyzer.ps1')
$runtimePath = Join-Path $PSScriptRoot 'runtime'
$modelPath = Join-Path $PSScriptRoot 'models/qwen2.5-1.5b-instruct-q4_k_m.gguf'
$webPath = Join-Path $PSScriptRoot 'web'
$exe = Get-ChildItem -LiteralPath $runtimePath -Filter 'llama-server.exe' -Recurse | Select-Object -First 1
if (-not $exe -or -not (Test-Path -LiteralPath $modelPath)) { throw 'Offline bundle is incomplete.' }
$listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback,$Port)
try { $listener.Start() } catch { throw ('Port ' + $Port + ' is occupied. Close the previous demo or pass another -Port.') } finally { $listener.Stop() }
$stdout = Join-Path $PSScriptRoot 'server.log'
$stderr = Join-Path $PSScriptRoot 'server-error.log'
$arguments = @('-m',('"' + $modelPath + '"'),'--host','127.0.0.1','--port',"$Port",'--path',('"' + $webPath + '"'),'--cors-origins',"http://127.0.0.1:$Port",'-c','8192','-ngl','0','--parallel','1','--alias','goutu-small')
$worker = Start-Process -FilePath $exe.FullName -ArgumentList $arguments -WorkingDirectory $exe.DirectoryName -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$pidPath = Join-Path $PSScriptRoot 'server-process.json'
@{ pid=$worker.Id; executable=$exe.FullName; start_ticks=$worker.StartTime.ToUniversalTime().Ticks } | ConvertTo-Json | Set-Content -LiteralPath $pidPath -Encoding UTF8
try {
    $ready = $false
    for ($i=0;$i -lt 90;$i++) {
        if ($worker.HasExited) { throw ('Model service exited. See ' + $stderr) }
        try { $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2; if ($health.status -eq 'ok') { $ready=$true; break } } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'Model load timed out. See server-error.log.' }
    $url = "http://127.0.0.1:$Port/index.html"
    Write-Host "Offline model ready: $url"
    Write-Host 'Close this window or press Ctrl+C to stop the model.'
    if (-not $NoBrowser) { Start-Process -FilePath $url -WindowStyle Hidden | Out-Null }
    $worker.WaitForExit()
} finally {
    & (Join-Path $PSScriptRoot 'stop-analyzer.ps1')
    if (-not $worker.HasExited) { Stop-Process -Id $worker.Id }
    if (Test-Path -LiteralPath $pidPath) { $current = Get-Content -LiteralPath $pidPath -Raw | ConvertFrom-Json; if ($current.pid -eq $worker.Id) { Remove-Item -LiteralPath $pidPath } }
}
