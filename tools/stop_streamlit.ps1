$ErrorActionPreference = "SilentlyContinue"

$Connections = Get-NetTCPConnection -LocalPort 8501 -State Listen
if ($Connections) {
    $Connections | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force
    }
    "Streamlit di port 8501 sudah dihentikan."
} else {
    "Tidak ada Streamlit yang aktif di port 8501."
}
