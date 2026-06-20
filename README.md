# Kugo Music Converter

本项目旨在帮助用户将酷狗音乐的专有格式（如.kgm、假.flac以及.kgg）转换为广泛支持的.mp3格式。

整合了unlock-kugou和kgg-dec工具的功能，使得转换过程更加简便快捷。

## 下载https://github.com/hu568/Kugo-Music-Converter-Modpacks/releases

## 支持的文件格式

- `.kgg`：使用`kgg-dec.exe`转换
- `.kgm`：使用`unlockKuGoWin-32.exe`或`unlockKuGoWin-64.exe`转换
- `.flac`：可以通过`convert-flac-kgm.ps1`脚本重命名为.kgm格式

## 依赖说明

- `kgg-dec.exe`：用于转换.kgg文件
- `unlockKuGoWin-32.exe`：用于32位系统转换.kgm文件
- `unlockKuGoWin-64.exe`：用于64位系统转换.kgm文件
- `ffmpeg.exe`：位于`kgm-vpr-out`文件夹中，用于将.ogg转换为.mp3
- `kgm.mask`：用于.kgm文件转换的掩码文件

## 输出目录

所有转换后的文件将保存在`kgm-vpr-out`文件夹中，包含部分的元数据信息（标题、专辑、艺术家等）。

## 使用说明
先下载并解压'Kugo-Music-Converter-Modpacks.zip'
### 方法一：使用一键启动脚本（推荐）

1. 将需要转换的文件（.flac、.kgm、.kgg）复制到当前文件夹
2. 右键点击`一键三联启动.ps1`，选择"使用PowerShell运行"
3. 脚本将自动执行以下操作：
   - 调用`convert-flac-kgm.ps1`脚本，将.flac文件重命名为.kgm格式
   - 启动`unlockKuGoWin-64.exe`，用于处理.kgm文件
   - 调用`convert-kgg-simple.ps1`脚本，用于处理.kgg文件

### 方法二：单独使用PowerShell脚本

#### 处理.flac文件

1. 将需要转换的.flac文件复制到当前文件夹
2. 右键点击`convert-flac-kgm.ps1`，选择"使用PowerShell运行"
3. 脚本将自动将.flac文件重命名为.kgm格式

#### 处理.kgm文件

1. 将需要转换的.kgm文件复制到当前文件夹
2. 双击运行`unlockKuGoWin-32.exe`（32位系统）或`unlockKuGoWin-64.exe`（64位系统）
3. 工具将自动转换.kgm文件为.mp3格式

#### 处理.kgg文件

1. 使用酷狗音乐客户端播放需要转换的.kgg文件一次
2. 将需要转换的.kgg文件复制到当前文件夹
3. 右键点击`convert-kgg-simple.ps1`，选择"使用PowerShell运行"
4. 脚本将自动将.kgg文件转换为.mp3格式

## 关于kgg文件无法转换的问题

解决方案：
1. 使用酷狗音乐客户端播放带有.kgg后缀的文件一次后可以正常转换。

- 或者

2. 参考 [kgg-dec-mirror](https://github.com/DHJComical/kgg-dec-mirror?tab=readme-ov-file#kgg-dec) ，拷贝 infra.dll 文件到这个kgg目录后直接双击运行kgg-dec.exe，就能正常转换格式了

## 注意事项

1. 转换.kgg文件前，请确保已使用酷狗音乐客户端播放过该文件
2. 部分文件可能需要最新版本的转换工具才能正常转换
3. 转换过程中请勿关闭命令窗口
4. 建议使用64位版本的转换工具（`unlockKuGoWin-64.exe`）以获得更好的性能
5. PowerShell脚本需要在PowerShell 3.0或更高版本中运行
6. 首次运行PowerShell脚本时，可能需要设置执行策略：
   - 以管理员身份运行PowerShell
   - 执行命令：`Set-ExecutionPolicy RemoteSigned`
   - 选择"是"或"全是"

## 了解更多

[kgg-dec-mirror](https://github.com/DHJComical/kgg-dec-mirror?tab=readme-ov-file#kgg-dec)

[kugou-kgm-decoder](https://github.com/ghtz08/kugou-kgm-decoder)

~[kgg-dec](https://github.com/ix64/unlock-music)~

~[unlock-music](https://github.com/ix64/unlock-music)~
