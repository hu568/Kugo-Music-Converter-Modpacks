@echo off
chcp 65001 >nul
cd /d "%~dp0"

call "flac-kgm.bat"

start "" "unlockKuGoWin-64.exe"
start "" "kgg-mp3.bat"

exit