# 测试说明

> 本目录存放测试用音乐文件，供验证解密工具是否正常工作。

## 测试文件列表

| 文件 | 对应格式 | 解密工具 |
|------|----------|----------|
| `测试用-音阙诗听、泠鸢yousa - 大喜.kgg` | `.kgg` | `kgg-dec.exe` |
| `测试用-Light Years Away (From Hardcore Utopia 4) - Synthion.kgma` | `.kgma` | `unlockKuGoWin-64.exe` |
| `测试用-森羅万象 - 無意識レクイエム (无意识安魂曲)_SQ.flac` | 加密 `.flac`（伪装 kgm） | 先重命名→`unlockKuGoWin-64.exe` |

## 操作规则

- **测试前必须**将文件拷贝到项目根目录的 `input/` 文件夹，**不要直接操作 Test-m/ 目录下的原始文件**
- 如果需要验证完整工作流，同样把文件复制到 `input/`，再按 AGENTS.md 的流程操作
- 两个解密工具（`kgg-dec.exe` / `unlockKuGoWin-64.exe`）都会**自动扫描项目根目录**（即它们所在的目录），无需手动指定文件路径
- 解密后输出见 `kgm-vpr-out/` 目录

## 文件备份

- `Test-Music-Pack.zip` 是原始文件备份
- 如果 Test-m/ 中的文件丢失或损坏，解压此 ZIP 即可恢复
