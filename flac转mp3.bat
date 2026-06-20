@echo off
setlocal enabledelayedexpansion

:: 检查ffmpeg是否存在
if not exist ffmpeg.exe (
    echo ffmpeg.exe not found in the current directory.
    pause
    exit /b
)

:: 转换flac文件并保留元数据（含封面）
echo Converting FLAC files to MP3 and preserving metadata...
for %%f in (*.flac) do (
    echo Converting %%f...
    ffmpeg -i "%%f" -q:a 0 -map_metadata 0 -map 0:a -map 0:v? -c:v copy -id3v2_version 3 "%%~nf.mp3"
)

:: 转换ogg文件并保留元数据（含封面）
echo Converting OGG files to MP3 and preserving metadata...
for %%f in (*.ogg) do (
    echo Converting %%f...
    ffmpeg -i "%%f" -q:a 0 -map_metadata 0 -map 0:a -map 0:v? -c:v copy -id3v2_version 3 "%%~nf.mp3"
)

echo Conversion complete.
pause
