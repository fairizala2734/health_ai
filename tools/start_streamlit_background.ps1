$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Runner = Join-Path $ProjectRoot "tools\run_streamlit.ps1"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "streamlit.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Existing = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    $Existing | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $Runner) `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden

for ($Attempt = 1; $Attempt -le 10; $Attempt++) {
    try {
        $Health = Invoke-WebRequest -UseBasicParsing http://localhost:8501/ -TimeoutSec 5
        "Streamlit aktif: http://localhost:8501/ ($($Health.StatusCode))"
        exit 0
    } catch {
        Start-Sleep -Seconds 2
    }
}

throw "Streamlit belum merespons di http://localhost:8501/ setelah menunggu."
