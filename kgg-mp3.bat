@echo off
setlocal enabledelayedexpansion

:: 创建输出目录（如果不存在）
if not exist "kgm-vpr-out" mkdir "kgm-vpr-out"

:: 遍历当前目录中的所有 .kgg 文件
for %%f in (*.kgg) do (
    :: 获取文件名（不带扩展名）
    set "filename=%%~nf"
    
    :: 运行 kgg-dec.exe 转换文件
    kgg-dec.exe "%%f"
    
    :: 重命名生成的 .ogg 文件
    ren "!filename!_kgg-dec.ogg" "!filename!.ogg"
    
    :: 使用 ffmpeg 将 .ogg 转换为 .mp3（最高品质，保留元数据）
    ffmpeg.exe -i "!filename!.ogg" -q:a 0 -map_metadata 0 "kgm-vpr-out\!filename!.mp3"
    
    :: 删除中间生成的 .ogg 文件
    del "!filename!.ogg"
)

echo 转换完成！
pause