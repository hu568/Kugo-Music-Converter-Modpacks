# One-Click Start Script
# Function:
# 1. First use convert-flac-kgm.ps1 to rename .flac files to .kgm
# 2. Then start unlockKuGoWin-64.exe and convert-kgg-simple.ps1 simultaneously

Clear-Host
Write-Output "=== One-Click Start ==="
Write-Output ""

Write-Output "1. Processing .flac files..."
Write-Output ""

# Call convert-flac-kgm.ps1 script directly in current window
& ".\convert-flac-kgm.ps1"

Write-Output ""
Write-Output "1. .flac files processing completed"
Write-Output ""
Write-Output "2. Starting conversion tools..."
Write-Output ""

# Start unlockKuGoWin-64.exe
Write-Output "Starting unlockKuGoWin-64.exe..."
Start-Process -FilePath ".\unlockKuGoWin-64.exe" -WindowStyle Normal

# Call convert-kgg-simple.ps1 script directly in current window
Write-Output "Starting convert-kgg-simple.ps1 script..."
& ".\convert-kgg-simple.ps1"

Write-Output ""
Write-Output "2. Conversion tools started successfully"
Write-Output ""
Write-Output "=== Start Complete ==="
Write-Output ""
Write-Output "Info:"
Write-Output "- unlockKuGoWin-64.exe is running, for processing .kgm files"
Write-Output "- convert-kgg-simple.ps1 script has completed processing .kgg files"
Write-Output ""
pause