@echo off
setlocal enabledelayedexpansion

set "sourceExt=.flac"
set "targetExt=.kgm"
set "errorFlag=0"

for %%f in (*%sourceExt%) do (
    set "originalFile=%%f"
    set "filename=%%~nf"
    set "newname=!filename!%targetExt%"

    rem 检查目标文件是否已存在
    if exist "!newname!" (
        echo 错误：文件 "!newname!" 已存在，跳过 "%%f"
        set /a errorFlag+=1
    ) else (
        ren "%%f" "!newname!" 2>nul
        if !errorlevel! neq 0 (
            echo 重命名失败：%%f → !newname!
            set /a errorFlag+=1
        ) else (
            echo 已重命名：%%f → !newname!
        )
    )
)

echo 完成. 共处理文件数：%errorFlag%
if %errorFlag% gtr 0 (
    echo 注意：有 %errorFlag% 个文件未处理
) else (
    echo 所有文件已成功重命名
)
pause