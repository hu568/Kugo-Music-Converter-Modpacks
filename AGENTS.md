# Kugo Music Converter Modpacks

> 酷狗音乐加密音频解密/转换工具箱。

## 项目结构

```
├── input/                          # 输入文件夹（放置待处理的音乐文件）
├── kgm-vpr-out/                    # 输出文件夹（所有解密产物都在这里）
│   ├── ffmpeg.exe                  # ffmpeg，用于转换格式
│   └── flac转mp3.bat               # 将 FLAC/OGG 批量转 MP3（含元数据）
├── Test-m/                         # 测试文件（.kgg, .kgma, 加密.flac）
│   └── Test-Music-Pack.zip         # 测试文件备份
├── kgg-dec.exe                     # 解密 .kgg 文件（v0.6.1, MIT）
├── unlockKuGoWin-64.exe            # 解密 .kgm/.kgma/.vpr 文件（64位, Alpha-2）
├── unlockKuGoWin-32.exe            # 同上（32位）
├── kgm.mask                        # 解密掩码文件（二进制，被各工具使用）
├── AGENTS.txt                      # 旧版说明（已迁移至此文件）
└── COPYING                         # GPL v3 许可证
```

## 支持的加密格式

| 后缀 | 解密工具 | 来源项目 |
|------|----------|----------|
| `.kgg` | `kgg-dec.exe` | https://git.unlock-music.dev/um/kgg-dec |
| `.kgm` / `.kgma` | `unlockKuGoWin-64.exe` / `-32.exe` | https://github.com/ix64/unlock-music |
| `.vpr` | `unlockKuGoWin-64.exe` / `-32.exe` | 同上 |
| `.flac`（加密伪装） | 需先重命名为 `.kgm`，再用 unlockKuGoWin 处理 | 加密 FLAC 其实是伪装的 kgm |

## 工具行为（实测结论，不看会踩坑）

### unlockKuGoWin.exe（解密 .kgm / .kgma / .vpr）
- **纯 CLI 工具，不是 GUI** — 运行后自动扫描当前目录下的文件，处理完输出 "完成，按Enter退出……"
- **不支持** 手动指定文件路径，所有处理都是自动的
- 会自动扫描当前目录中的 `.kgm`、`.kgma`、`.vpr` 文件
- 输出到同级的 `kgm-vpr-out/` 文件夹
- ⚠️ **文件大小限制**: 仅支持 78MB 以下的文件
- Alpha-2 Build 2020/04/17，来自 ix64/unlock-music 项目
- 退出时提示 "按Enter退出"，但在脚本中启动后它会自行处理并退出

### kgg-dec.exe（解密 .kgg）
- **支持** CLI 参数，用法：`kgg-dec.exe <文件路径>`
- **不加参数时** 也会自动扫描当前目录中的所有 `.kgg` 文件
- 完整的 CLI 选项：
  - `--scan-all-file-ext 0` — 是否扫描所有文件扩展名
  - `--db /path/to/KGMusicV3.db` — 指定密钥数据库路径
  - `--suffix _kgg-dec` — 自定义输出文件后缀（默认 `_kgg-dec`）
  - `[FILE]...` — 可指定多个文件路径
- 输出到 `kgm-vpr-out/` 目录，文件名格式为 `原文件名_kgg-dec.ogg`
- 如果解密失败，原因通常是**缺少解密密钥** → 需要先用酷狗客户端播一次该文件

### 加密 .flac 文件的特殊处理
- 酷狗下载的部分 FLAC 文件其实是加密的（伪装的 KGM 格式）
- 必须先将 `.flac` 后缀改为 `.kgm`，再用 unlockKuGoWin 解密
- 旧项目有 `convert-flac-kgm.ps1` 脚本自动做这个重命名

## 完整工作流

1. 将需要的音乐文件放入 `input/` 文件夹
2. 从 `input/` 复制到项目根目录（两个工具都自动扫描根目录）
3. 根据文件类型选择工具处理：
   - `.kgg` → 直接运行 `kgg-dec.exe`（自动扫描）或 `kgg-dec.exe <文件路径>`
   - `.kgm` / `.kgma` / `.vpr` → 直接运行 `unlockKuGoWin-64.exe`（自动扫描并解密）
   - 加密 `.flac` → 先重命名为 `.kgm` → 再运行 `unlockKuGoWin-64.exe`
4. 最终输出在 `kgm-vpr-out/` 目录
5. 可选：运行 `flac转mp3.bat` 将目录中的 FLAC/OGG 文件批量转 MP3（保留元数据和封面）

## 测试说明

测试前务必阅读 `Test-m/test.md`，里面有详细的操作细则。

- 测试文件在 `Test-m/` 目录（`.kgg`, `.kgma`, 加密`.flac` 各一个）
- **测试前**将文件拷贝到 `input/` 文件夹（不是直接操作 Test-m/ 内的文件）
- `Test-Music-Pack.zip` 是测试文件备份，文件丢失时可解压恢复

## 关于旧项目

- 旧项目位于 `C:\Users\Administrator\Downloads\Kugo-Music-Converter-Modpacks`
- 包含 PowerShell 自动化脚本（`一键三联启动.ps1`, `convert-flac-kgm.ps1`, `convert-kgg-simple.ps1`）
- 新项目是重构版，尚未包含这些脚本
- 如需自动化流程，可参考旧项目的 PS1 脚本

## 注意事项

- `ffmpeg.exe` 位于 `kgm-vpr-out/ffmpeg.exe` — 不要在别处找
- unlockKuGoWin 不是 GUI，它是 CLI 工具，在脚本中可以直接调用并等待完成
- `.kgg` 解密失败时提示的 "missing decryption key" → 需要酷狗客户端先播放一次该文件
- unlockKuGoWin 不支持 78MB 以上的文件
- 所有输出都汇集到 `kgm-vpr-out/` 目录
- 本项目使用 GPL v3 许可证（kgg-dec.exe 使用 MIT 许可证）
