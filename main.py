"""
Kugo Music Converter — 一键三联启动脚本
酷狗音乐加密音频解密/转换工具箱

工作流程:
    1. 从 input/ 复制文件到项目根目录
    2. 将加密的 .flac 重命名为 .kgm（伪装 KGM 格式）
    3. 并行执行:
       a. unlockKuGoWin-64.exe — 解密 .kgm/.kgma/.vpr
       b. kgg-dec.exe — 解密 .kgg 并输出 .ogg
    4. 全部完成后输出汇总

用法:
    python main.py                    # 交互式默认流程
    python main.py --auto             # 自动执行全部流程
    python main.py --skip-copy        # 跳过 input/ 复制步骤
"""

import os
import sys
import shutil
import subprocess
import threading
import argparse
import time

# 项目根目录（exe 所在目录，兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    PROJECT_DIR = os.path.dirname(sys.executable)
else:
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(PROJECT_DIR, "input")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "kgm-vpr-out")
UNLOCK_TOOL = os.path.join(PROJECT_DIR, "unlockKuGoWin-64.exe")
UNLOCK_TOOL_32 = os.path.join(PROJECT_DIR, "unlockKuGoWin-32.exe")
KGG_DEC = os.path.join(PROJECT_DIR, "kgg-dec.exe")
FFMPEG = os.path.join(OUTPUT_DIR, "ffmpeg.exe")

# 记录从 input/ 复制过来的文件，用于运行结束后清理
_copied_files: list[str] = []

# 颜色输出（Windows 兼容）
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # 如果 Windows 不支持 ANSI 转义，自动禁用
    @staticmethod
    def init():
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                for attr in dir(Colors):
                    if not attr.startswith("_"):
                        setattr(Colors, attr, "")


def print_step(step_num: int, message: str) -> None:
    """打印带步骤编号的消息"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}=== 步骤 {step_num}: {message} ==={Colors.RESET}\n")


def print_success(message: str) -> None:
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠  {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """打印错误消息"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """打印信息消息"""
    print(f"  {message}")


# ─── 步骤1: 从input/复制文件 ─────────────────────────────────────────


def step_copy_from_input() -> int:
    """从 input/ 复制文件到项目根目录，返回复制的文件数"""
    global _copied_files
    _copied_files = []  # 重置记录

    print_step(1, "从 input/ 复制文件到项目根目录")

    if not os.path.isdir(INPUT_DIR):
        print_warning(f"input/ 目录不存在: {INPUT_DIR}")
        print_info("请先将要处理的音乐文件放入 input/ 文件夹")
        return 0

    input_files = [f for f in os.listdir(INPUT_DIR)
                   if os.path.isfile(os.path.join(INPUT_DIR, f))]

    if not input_files:
        print_warning("input/ 目录中没有文件")
        return 0

    # 过滤出支持的音频文件
    supported_exts = {".kgg", ".kgm", ".kgma", ".vpr", ".flac"}
    audio_files = [f for f in input_files
                   if os.path.splitext(f)[1].lower() in supported_exts]

    if not audio_files:
        print_warning(f"input/ 中没有支持的音频文件（支持: {', '.join(sorted(supported_exts))}）")
        return 0

    copied = 0
    skipped = 0

    print_info(f"找到 {len(audio_files)} 个音频文件：")
    for f in audio_files:
        src = os.path.join(INPUT_DIR, f)
        dst = os.path.join(PROJECT_DIR, f)
        if os.path.exists(dst):
            # 比较大小，不同则覆盖
            if os.path.getsize(src) != os.path.getsize(dst):
                shutil.copy2(src, dst)
                print_info(f"  → 覆盖: {f}")
                copied += 1
                _copied_files.append(f)
            else:
                print_info(f"  → 跳过（已存在）: {f}")
                skipped += 1
        else:
            shutil.copy2(src, dst)
            print_info(f"  → 复制: {f}")
            copied += 1
            _copied_files.append(f)

    print_success(f"复制完成: 新增 {copied} 个文件，跳过 {skipped} 个")
    return copied


# ─── 步骤2: 重命名加密 .flac → .kgm ─────────────────────────────────


def step_rename_flac_to_kgm() -> int:
    """将加密的 .flac 重命名为 .kgm，返回重命名的文件数"""
    print_step(2, "处理加密的 .flac 文件（重命名为 .kgm）")

    flac_files = [f for f in os.listdir(PROJECT_DIR)
                  if f.lower().endswith(".flac")
                  and os.path.isfile(os.path.join(PROJECT_DIR, f))]

    if not flac_files:
        print_info("没有找到 .flac 文件，跳过")
        return 0

    renamed = 0
    skipped = 0
    errors = 0

    for flac_file in flac_files:
        base = os.path.splitext(flac_file)[0]
        target = base + ".kgm"
        src = os.path.join(PROJECT_DIR, flac_file)
        dst = os.path.join(PROJECT_DIR, target)

        print_info(f"处理: {flac_file}")

        if os.path.exists(dst):
            print_info(f"  → 跳过: {target} 已存在")
            skipped += 1
        else:
            try:
                os.rename(src, dst)
                print_info(f"  → 重命名: {flac_file} -> {target}")
                renamed += 1
            except Exception as e:
                print_error(f"重命名失败: {e}")
                errors += 1

    print_success(f"重命名完成: 成功 {renamed}，跳过 {skipped}，失败 {errors}")
    return renamed


# ─── 步骤3: 运行 unlockKuGoWin ─────────────────────────────────────


def run_unlock_tool() -> bool:
    """运行 unlockKuGoWin 解密 .kgm/.kgma/.vpr 文件"""
    # 优先使用 64 位版本
    unlock_exe = UNLOCK_TOOL if os.path.isfile(UNLOCK_TOOL) else UNLOCK_TOOL_32

    if not os.path.isfile(unlock_exe):
        print_warning(f"unlockKuGoWin 未找到（已尝试 64位和32位版本）")
        return False

    # 检查是否有需要处理的文件
    supported = {".kgm", ".kgma", ".vpr"}
    has_files = any(
        os.path.splitext(f)[1].lower() in supported
        and os.path.isfile(os.path.join(PROJECT_DIR, f))
        for f in os.listdir(PROJECT_DIR)
    )

    if not has_files:
        print_info("没有找到 .kgm/.kgma/.vpr 文件，跳过 unlockKuGoWin")
        return True

    print_info(f"正在启动 {os.path.basename(unlock_exe)} ...")
    print_info("（此工具会自动扫描当前目录并解密，请稍候）")

    try:
        result = subprocess.run(
            [unlock_exe],
            cwd=PROJECT_DIR,
            capture_output=True,
            input="\n",  # 工具结束时提示"按Enter退出"，自动发送回车
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120,
        )
        print_info(f"{os.path.basename(unlock_exe)} 已执行完成")
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    print_info(f"  {line.strip()}")
        return True
    except subprocess.TimeoutExpired:
        print_warning(f"{os.path.basename(unlock_exe)} 执行超时")
        return False
    except Exception as e:
        print_error(f"运行 {os.path.basename(unlock_exe)} 失败: {e}")
        return False


def step_run_unlock_tool() -> bool:
    """步骤3入口：运行 unlockKuGoWin"""
    print_step(3, "解密 .kgm / .kgma / .vpr 文件")
    return run_unlock_tool()


# ─── 步骤4: 处理 .kgg 文件 ─────────────────────────────────────────


def step_process_kgg() -> bool:
    """解密 .kgg 文件并输出 .ogg"""
    print_step(4, "解密 .kgg 文件")

    # 检查依赖
    if not os.path.isfile(KGG_DEC):
        print_error("缺少 kgg-dec.exe")
        return False

    # 查找 .kgg 文件
    kgg_files = [f for f in os.listdir(PROJECT_DIR)
                 if f.lower().endswith(".kgg")
                 and os.path.isfile(os.path.join(PROJECT_DIR, f))]

    if not kgg_files:
        print_info("没有找到 .kgg 文件，跳过")
        return True

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = 0
    failed = 0

    for kgg_file in kgg_files:
        base_name = os.path.splitext(kgg_file)[0]
        source_path = os.path.join(PROJECT_DIR, kgg_file)

        print_info(f"处理: {kgg_file}")

        # 步骤: kgg-dec.exe 解密
        print_info(f"  运行 kgg-dec.exe ...")
        try:
            result = subprocess.run(
                [KGG_DEC, source_path],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120,
            )
            if result.returncode != 0:
                print_info(f"  kgg-dec.exe 返回码: {result.returncode}，检查输出文件 ...")
        except Exception as e:
            print_error(f"kgg-dec 运行错误: {e}")
            failed += 1
            continue

        # 检查临时 ogg 文件（kgg-dec 默认后缀 _kgg-dec）
        temp_ogg = os.path.join(PROJECT_DIR, f"{base_name}_kgg-dec.ogg")
        # 有的版本输出到 kgm-vpr-out/，也检查一下
        temp_ogg_in_out = os.path.join(OUTPUT_DIR, f"{base_name}_kgg-dec.ogg")
        output_ogg = os.path.join(OUTPUT_DIR, f"{base_name}.ogg")

        if os.path.isfile(temp_ogg_in_out):
            # 文件在输出目录中，直接重命名
            temp_ogg = temp_ogg_in_out
            print_info(f"  在 kgm-vpr-out/ 中找到临时文件")
        elif not os.path.isfile(temp_ogg):
            print_error("kgg-dec 未生成输出文件（可能缺少解密密钥，请先用酷狗客户端播放一次该文件）")
            failed += 1
            continue

        print_info(f"  ✓ kgg-dec 解密成功")

        # 移动到输出目录
        try:
            if os.path.isfile(output_ogg):
                os.remove(output_ogg)
            os.rename(temp_ogg, output_ogg)
            print_info(f"  ✓ 输出: {os.path.join('kgm-vpr-out', base_name + '.ogg')}")
            success += 1
        except Exception as e:
            print_error(f"移动输出文件失败: {e}")
            _safe_remove(temp_ogg)
            failed += 1

    print_success(f"KGG 处理完成: 成功 {success} 个，失败 {failed} 个")
    return failed == 0


def _safe_remove(filepath: str) -> None:
    """安全删除文件"""
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
    except Exception:
        pass


# ─── 步骤5: 批量转 MP3（可选） ─────────────────────────────────────


def step_convert_flac_to_mp3() -> bool:
    """将输出目录中的 FLAC/OGG 批量转 MP3"""
    print_step(5, "（可选）将 FLAC/OGG 批量转换为 MP3（保留元数据）")

    if not os.path.isfile(FFMPEG):
        print_warning("未找到 ffmpeg.exe，跳过")
        return True

    # 查找需要转换的音频文件
    audio_files = [f for f in os.listdir(OUTPUT_DIR)
                   if (f.lower().endswith(".flac") or f.lower().endswith(".ogg"))
                   and os.path.isfile(os.path.join(OUTPUT_DIR, f))
                   and not f.lower().endswith(".mp3")]

    if not audio_files:
        print_info(f"{OUTPUT_DIR} 中没有 FLAC/OGG 文件，跳过")
        return True

    total = len(audio_files)
    success = 0
    failed = 0

    print_info(f"找到 {total} 个音频文件")
    print()

    for idx, audio_file in enumerate(audio_files, 1):
        base_name = os.path.splitext(audio_file)[0]
        src = os.path.join(OUTPUT_DIR, audio_file)
        dst = os.path.join(OUTPUT_DIR, f"{base_name}.mp3")

        print_info(f"[{idx}/{total}] 正在转换: {audio_file}")

        try:
            result = subprocess.run(
                [FFMPEG, "-i", src,
                 "-q:a", "0",
                 "-map_metadata", "0",
                 "-map", "0:a",
                 "-map", "0:v?",
                 "-c:v", "copy",
                 "-id3v2_version", "3",
                 "-y",
                 dst],
                cwd=OUTPUT_DIR,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=600,
            )
            if os.path.isfile(dst):
                # 从 ffmpeg 输出中提取时长和大小
                duration = "?"
                file_size = ""
                for line in result.stderr.splitlines():
                    if "Duration:" in line:
                        for part in line.split(","):
                            if "Duration:" in part:
                                duration = part.split(":", 1)[1].strip()
                    if "size=" in line and "time=" in line:
                        # size=    9005KiB time=00:04:39.28 bitrate=...
                        for part in line.strip().split():
                            if part.startswith("size="):
                                file_size = part.split("=", 1)[1].strip()

                size_str = f", {file_size}" if file_size else ""
                print_info(f"       ✓ {base_name}.mp3 (时长 {duration}{size_str})")
                success += 1
            else:
                print_error(f"      ✗ 转换失败")
                failed += 1
        except subprocess.TimeoutExpired:
            print_warning(f"      ! 转换超时")
            failed += 1
        except Exception as e:
            print_error(f"      ✗ 错误: {e}")
            failed += 1

        print()

    if failed == 0:
        print_success(f"批量转换完成: 成功 {success} 个")
    else:
        print_info(f"批量转换完成: 成功 {success} 个，失败 {failed} 个")
    return failed == 0


# ─── 步骤6: 清理复制的文件 ────────────────────────────────────────


def step_cleanup() -> None:
    """运行结束后，删除从 input/ 复制到项目根目录的文件"""
    global _copied_files

    if not _copied_files:
        return

    print_step(6, "清理临时文件")
    print_info("删除从 input/ 复制到根目录的文件 ...")

    deleted = 0
    for f in _copied_files:
        dst = os.path.join(PROJECT_DIR, f)
        if os.path.isfile(dst):
            try:
                os.remove(dst)
                print_info(f"  → 删除: {f}")
                deleted += 1
            except Exception as e:
                print_warning(f"删除 {f} 失败: {e}")

        # 如果原始是 .flac，可能被重命名成了 .kgm，也清理掉
        if f.lower().endswith(".flac"):
            kgm_name = os.path.splitext(f)[0] + ".kgm"
            kgm_path = os.path.join(PROJECT_DIR, kgm_name)
            if os.path.isfile(kgm_path):
                try:
                    os.remove(kgm_path)
                    print_info(f"  → 删除: {kgm_name}")
                    deleted += 1
                except Exception as e:
                    print_warning(f"删除 {kgm_name} 失败: {e}")

    # 也清理 kgg-dec 可能遗留的临时文件
    for f in os.listdir(PROJECT_DIR):
        if f.endswith("_kgg-dec.ogg") and os.path.isfile(os.path.join(PROJECT_DIR, f)):
            try:
                os.remove(os.path.join(PROJECT_DIR, f))
                print_info(f"  → 删除临时文件: {f}")
                deleted += 1
            except Exception:
                pass

    _copied_files = []
    print_success(f"清理完成，共删除 {deleted} 个文件\n")


# ─── 流程控制 ──────────────────────────────────────────────────────


def show_banner() -> None:
    """显示启动横幅"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════╗
║      Kugo Music Converter Modpacks          ║
║      酷狗音乐加密音频解密/转换工具箱           ║
╚══════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


def show_summary(results: dict) -> None:
    """显示执行结果汇总"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*50}")
    print("  执行结果汇总")
    print(f"{'='*50}{Colors.RESET}\n")

    steps = [
        ("复制文件", results.get("copy", False)),
        ("重命名 .flac → .kgm", results.get("rename", False)),
        ("unlockKuGoWin 解密", results.get("unlock", False)),
        ("KGG 解密 → .ogg", results.get("kgg", False)),
        ("批量转 MP3", results.get("convert", False)),
        ("清理临时文件", results.get("cleanup", False)),
    ]

    all_ok = True
    for name, status in steps:
        if isinstance(status, bool):
            icon = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.YELLOW}-{Colors.RESET}"
            if not status:
                all_ok = False
            print(f"  {icon} {name}")
        else:
            # 数字（复制的文件数等）
            print(f"  {Colors.GREEN}✓{Colors.RESET} {name}: {status}")

    print(f"\n{Colors.BOLD}输出目录: {OUTPUT_DIR}{Colors.RESET}")
    print()

    if all_ok:
        print(f"{Colors.GREEN}✅ 全部流程执行完毕！{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️  部分步骤未执行或出错，请查看上方日志。{Colors.RESET}")
    print()


def run_auto(skip_copy: bool = False, skip_convert: bool = False) -> None:
    """自动执行全部流程"""
    results = {}

    # 步骤1: 复制文件
    if not skip_copy:
        copied = step_copy_from_input()
        results["copy"] = copied
    else:
        results["copy"] = "已跳过"

    # 步骤2: 重命名 .flac → .kgm
    renamed = step_rename_flac_to_kgm()
    results["rename"] = renamed

    # 步骤3 & 4: 并行处理 unlockKuGoWin + KGG
    print_step("3&4", "并行解密 .kgm/.vpr 和 .kgg 文件")
    print_info("unlockKuGoWin 处理 .kgm/.kgma/.vpr")
    print_info("kgg-dec 处理 .kgg → .ogg")
    print()

    unlock_ok = run_unlock_tool()
    kgg_ok = step_process_kgg()

    results["unlock"] = unlock_ok
    results["kgg"] = kgg_ok

    # 步骤5: 批量转 MP3（可选）
    if skip_convert:
        results["convert"] = "已跳过"
    else:
        convert_ok = step_convert_flac_to_mp3()
        results["convert"] = convert_ok

    # 步骤6: 清理复制的文件
    if _copied_files:
        step_cleanup()
        results["cleanup"] = True
    else:
        results["cleanup"] = "无需清理"

    show_summary(results)


# ─── 组合步骤 ──────────────────────────────────────────────────────


def step_rename_and_unlock() -> None:
    """复制→重命名 .flac→.kgm→unlockKuGoWin 解密→清理"""
    print_step("1→3", "KGM 专用流程（复制→重命名FLAC→unlockKuGoWin 解密→清理）")

    # 1. 从 input/ 复制文件
    copied = step_copy_from_input()

    # 2. 重命名 .flac → .kgm
    step_rename_flac_to_kgm()

    # 3. 运行 unlockKuGoWin 解密
    step_run_unlock_tool()

    # 4. 清理复制的文件
    if _copied_files:
        step_cleanup()


def run_interactive() -> None:
    """交互式菜单"""
    show_banner()

    print("可用的操作：")
    print(f"  {Colors.BOLD}1{Colors.RESET}. 完整流程（含批量转MP3）")
    print(f"  {Colors.BOLD}2{Colors.RESET}. 完整流程（仅解密，不转MP3）")
    print(f"  {Colors.BOLD}3{Colors.RESET}. KGM 专用流程（复制→重命名FLAC→解密→清理）")
    print(f"  {Colors.BOLD}4{Colors.RESET}. 仅解密 .kgg → .ogg")
    print(f"  {Colors.BOLD}5{Colors.RESET}. 仅批量转 MP3（FLAC/OGG → MP3）")
    print(f"  {Colors.BOLD}0{Colors.RESET}. 退出")
    print()

    choice = input("请选择 [0-5]: ").strip()

    if choice == "1":
        run_auto()
    elif choice == "2":
        run_auto(skip_convert=True)
    elif choice == "3":
        step_rename_and_unlock()
    elif choice == "4":
        step_process_kgg()
    elif choice == "5":
        step_convert_flac_to_mp3()
    elif choice == "0":
        print("再见！")
        sys.exit(0)
    else:
        print_error("无效选择")
        run_interactive()


# ─── 入口 ──────────────────────────────────────────────────────────


def main():
    # 确保终端支持 UTF-8 输出（避免 Windows GBK 编码问题）
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    Colors.init()

    parser = argparse.ArgumentParser(
        description="Kugo Music Converter — 酷狗音乐加密音频解密/转换工具箱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py             交互式菜单
  python main.py --auto      自动执行全部流程
  python main.py --skip-copy 自动执行，跳过复制步骤
        """,
    )
    parser.add_argument("--auto", action="store_true",
                        help="自动执行全部流程（无需交互）")
    parser.add_argument("--skip-copy", action="store_true",
                        help="跳过从 input/ 复制文件的步骤")
    args = parser.parse_args()

    if args.auto:
        show_banner()
        run_auto(skip_copy=args.skip_copy)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
