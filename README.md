# Kugo Music Converter Modpacks

> 酷狗音乐加密音频解密/转换工具箱

一键解密酷狗音乐加密格式（`.kgg` / `.kgm` / `.kgma` / `.vpr` / 加密 `.flac`），无需安装 Python，开箱即用。

---

## 快速开始

1. 将需要解密的音乐文件放入 `input/` 文件夹
2. 双击运行 `Kugo-Music-Converter.exe`
3. 选择需要的功能（输入数字后回车）

### 菜单选项说明

| 选项 | 功能 | 说明 |
|:----:|------|------|
| **1** | 完整流程（含批量转MP3） | 复制→解密→转MP3→自动清理，一步到位 |
| **2** | 完整流程（仅解密，不转MP3） | 只解密不解码，输出原始音频格式 |
| **3** | KGM 专用流程 | 只处理 `.kgm/.kgma/.vpr` + 加密 `.flac`，不碰 KGG |
| **4** | 仅解密 .kgg → .ogg | 只解密 `.kgg` 文件为 ogg 格式 |
| **5** | 仅批量转 MP3 | 将输出目录中的 FLAC/OGG 批量转 MP3（保留元数据和封面） |
| **0** | 退出 | |

### 独立工具

也可以直接使用独立 exe 完成单项操作：

```bash
# 将加密的 .flac 重命名为 .kgm（当前目录）
FLAC转KGM.exe

# 解密 .kgg 文件（当前目录）
KGG解密.exe
```

### 图形界面版

不想敲命令行/数字菜单，可以使用图形界面（基于 pywebview + [WinUIonWeb](https://github.com/Furry-Xiyi/WinUIonWeb) 样式）：

```bash
pip install pywebview
python gui.py
```

界面只有三个功能：

1. **添加文件** — 点击选择，或直接把文件/文件夹拖进窗口；文件夹会自动扫描其中的音乐文件。此步骤仅暂存到列表，不会复制到 `input/`
2. **开始处理** — 右下角单个按钮执行完整流程：把列表文件复制到 `input/` → 调用主程序解密 → 批量转 MP3 → 自动清理；窗口底部有流程进度状态条，处理日志在"处理日志"页签中实时显示
3. **清理缓存** — 左下角按钮，删除 `input/` 与 `kgm-vpr-out/` 中的音乐文件（保留 `ffmpeg.exe` 和 `批量转MP3.bat`），点击后会先弹出确认对话框

界面自动跟随系统明暗主题。

---

## 支持的加密格式

| 后缀 | 说明 | 处理方式 |
|------|------|----------|
| `.kgg` | 酷狗加密音频 | `KGG解密.exe` 解密为 `.ogg` |
| `.kgm` / `.kgma` | 酷狗加密音频 | `unlockKuGoWin` 自动解密 |
| `.vpr` | 酷狗加密音频 | `unlockKuGoWin` 自动解密 |
| `.flac`（加密伪装） | 实为伪装的 KGM 格式 | 自动重命名为 `.kgm` 后解密 |
| `.kgg.flac`（伪装） | 手机端酷狗下载，实为伪装的 KGG 格式 | 自动去掉 `.flac` 伪装，按 `.kgg` 解密为 `.ogg` |

---

## 目录结构

```
Kugo-Music-Converter/
├── Kugo-Music-Converter.exe      # 主程序（一键操作）
├── FLAC转KGM.exe                 # 独立工具：FLAC→KGM 重命名
├── KGG解密.exe                   # 独立工具：KGG 解密
├── kgg-dec.exe                   # KGG 解密引擎
├── unlockKuGoWin-64.exe          # KGM/KGMA/VPR 解密引擎（64位）
├── unlockKuGoWin-32.exe          # KGM/KGMA/VPR 解密引擎（32位）
├── kgm.mask                      # 解密掩码文件
├── gui.py                        # 图形界面入口（pywebview，需 pip install pywebview）
├── gui_assets/                   # 图形界面资源（HTML/CSS/JS）
├── README.md                     # 本说明文件
├── input/                        # ← 把音乐文件放这里
│   └── 把音乐文件放到这里.txt
└── kgm-vpr-out/                  # 解密输出目录
    ├── ffmpeg.exe                # 格式转换工具
    └── 批量转MP3.bat             # 批量转 MP3 脚本
```

---

## 注意事项

- **`.kgg` 解密失败** — 提示"缺少解密密钥"时，需要先用酷狗音乐客户端播放一次该文件（获取密钥缓存）
- **手机端下载的 `.kgg.flac`** — 实为 KGG 格式伪装成 `.flac`，工具会自动识别并还原后解密，无需手动改名；解密前同样需要先用酷狗客户端播放一次
- **文件大小限制** — `unlockKuGoWin` 仅支持 78MB 以下的文件
- **解密输出** — 所有解密产物都在 `kgm-vpr-out/` 目录
- 运行完整流程后，复制到根目录的临时文件会自动清理，无需手动删除
- 图形界面需要 `pip install pywebview`；打包时需把界面资源一起带上：
  `pyinstaller --onefile --console gui.py --name 图形界面 --add-data "gui_assets;gui_assets" --icon gui_assets/icon.ico`
  （图标源文件为 `gui_assets/icon.svg`，修改后需重新生成 `icon.ico`）
- 本工具仅用于解密已购买或已获取的合法音乐文件，请尊重版权

---

## 开源许可

本项目基于 GPL v3 许可证发布。
