"""
KGG Decryptor
解密 .kgg 文件并输出到 kgm-vpr-out/ 目录

工作流程:
    1. 用 kgg-dec.exe 解密 .kgg 文件 → 输出临时 .ogg
    2. 将 .ogg 移动到 kgm-vpr-out/ 目录

用法:
    python convert_kgg.py
    python convert_kgg.py --path <目标目录>
"""

import os
import sys
import subprocess
import argparse


def check_dependencies(project_dir: str) -> bool:
    """检查必需的工具是否存在"""
    kgg_dec = os.path.join(project_dir, "kgg-dec.exe")

    if not os.path.isfile(kgg_dec):
        print("错误: 找不到 kgg-dec.exe")
        return False
    return True


def convert_kgg_files(target_dir: str, project_dir: str) -> None:
    """处理目标目录中的所有 .kgg 文件"""
    kgg_dec = os.path.join(project_dir, "kgg-dec.exe")
    output_dir = os.path.join(project_dir, "kgm-vpr-out")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 查找所有 .kgg 文件
    kgg_files = [f for f in os.listdir(target_dir)
                 if f.lower().endswith(".kgg") and os.path.isfile(os.path.join(target_dir, f))]

    if not kgg_files:
        print("没有找到 .kgg 文件")
        return

    print(f"找到 {len(kgg_files)} 个 .kgg 文件，开始解密：\n")

    for kgg_file in kgg_files:
        base_name = os.path.splitext(kgg_file)[0]
        source_path = os.path.join(target_dir, kgg_file)

        print(f"处理: {kgg_file}")

        # 步骤1: 调用 kgg-dec.exe 解密
        print(f"  运行 kgg-dec.exe ...")
        try:
            result = subprocess.run(
                [kgg_dec, source_path],
                cwd=project_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',  # kgg-dec.exe 输出含 UTF-8 字符
                errors='replace',
                timeout=120,
            )
            if result.returncode != 0:
                print(f"  ✗ kgg-dec.exe 返回错误码: {result.returncode}")
                if result.stderr:
                    print(f"    错误信息: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"  ✗ kgg-dec.exe 超时")
            continue
        except Exception as e:
            print(f"  ✗ 运行 kgg-dec.exe 失败: {e}")
            continue

        # 步骤2: 检查临时 .ogg 文件（kgg-dec 默认后缀 _kgg-dec）
        temp_ogg = os.path.join(project_dir, f"{base_name}_kgg-dec.ogg")
        output_ogg = os.path.join(output_dir, f"{base_name}.ogg")

        if not os.path.isfile(temp_ogg):
            print(f"  ✗ kgg-dec 解密失败")
            print(f"    可能原因: 缺少解密密钥。请先用酷狗客户端播放一次该文件。")
            print()
            continue

        print(f"  ✓ kgg-dec 解密成功")

        # 步骤3: 移动到输出目录
        try:
            if os.path.isfile(output_ogg):
                os.remove(output_ogg)
            os.rename(temp_ogg, output_ogg)
            print(f"  ✓ 输出: {os.path.join('kgm-vpr-out', base_name + '.ogg')}")
        except Exception as e:
            print(f"  ✗ 移动输出文件失败: {e}")
            continue

        print()

    print("=== 解密完成 ===")
    print(f"结果保存在: {output_dir}")
    print()


def safe_remove(file_path: str) -> None:
    """安全删除文件"""
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception:
        pass


def main():
    # 确保终端支持 UTF-8 输出（避免 Windows GBK 编码问题）
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="解密 .kgg 文件并输出 .ogg 到 kgm-vpr-out/")
    parser.add_argument("--path", default=".",
                        help="扫描 .kgg 文件的目录（默认：当前目录）")
    parser.add_argument("--project", default=".",
                        help="项目根目录（包含 kgg-dec.exe 和 kgm-vpr-out/，默认：当前目录）")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.path)
    project_dir = os.path.abspath(args.project)

    # 验证目录
    if not os.path.isdir(target_dir):
        print(f"错误: 扫描目录不存在 - {target_dir}")
        sys.exit(1)
    if not os.path.isdir(project_dir):
        print(f"错误: 项目目录不存在 - {project_dir}")
        sys.exit(1)

    print("=== KGG 解密工具 ===")
    print(f"扫描目录: {target_dir}")
    print(f"项目目录: {project_dir}")
    print()

    # 检查依赖
    if not check_dependencies(project_dir):
        sys.exit(1)

    convert_kgg_files(target_dir, project_dir)


if __name__ == "__main__":
    main()
