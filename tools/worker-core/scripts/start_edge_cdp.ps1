param(
    [int]$Port = 9242,
    [string]$ProfileDirectory = "Default",
    [string]$StartUrl = "https://www.freepik.com/pikaso/ai-image-generator"
)

$edgeCandidates = @(
    "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LocalAppData\Microsoft\Edge\Application\msedge.exe"
)

$edgePath = $edgeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edgePath) {
    Write-Error "No encontre msedge.exe en las rutas habituales."
    exit 1
}

$running = Get-Process msedge -ErrorAction SilentlyContinue
if ($running) {
    Write-Error "Edge ya esta abierto. Cierra todas las ventanas y vuelve a ejecutar este script para exponer CDP sobre tu perfil actual."
    exit 1
}

$args = @(
    "--remote-debugging-port=$Port",
    "--profile-directory=$ProfileDirectory",
    $StartUrl
)

Start-Process -FilePath $edgePath -ArgumentList $args | Out-Null

Write-Host "Edge iniciado con CDP en http://127.0.0.1:$Port"
Write-Host "Define BROWSER_CDP_URL=http://127.0.0.1:$Port en worker-core/.env"
