"""
FLAC to KGM Renamer
将加密的 .flac 文件重命名为 .kgm（加密 FLAC 其实是伪装的 KGM 格式）

用法:
    python convert_flac_kgm.py
    python convert_flac_kgm.py --path <目标目录>
"""

import os
import sys
import argparse


def rename_flac_to_kgm(target_dir: str = ".") -> None:
    """将目标目录下的所有 .flac 文件重命名为 .kgm"""
    source_ext = ".flac"
    target_ext = ".kgm"

    success_count = 0
    skip_count = 0
    error_count = 0

    # 查找所有 .flac 文件
    flac_files = [f for f in os.listdir(target_dir)
                  if f.lower().endswith(source_ext) and os.path.isfile(os.path.join(target_dir, f))]

    if not flac_files:
        print("没有找到 .flac 文件")
        return

    print(f"找到 {len(flac_files)} 个 .flac 文件，开始重命名：\n")

    for flac_file in flac_files:
        base_name = os.path.splitext(flac_file)[0]
        target_name = base_name + target_ext
        source_path = os.path.join(target_dir, flac_file)
        target_path = os.path.join(target_dir, target_name)

        print(f"处理: {flac_file}")

        if os.path.exists(target_path):
            print(f"  ⚠️  跳过: {target_name} 已存在")
            skip_count += 1
        else:
            try:
                os.rename(source_path, target_path)
                print(f"  ✓ 已重命名: {flac_file} -> {target_name}")
                success_count += 1
            except Exception as e:
                print(f"  ✗ 错误: 重命名 {flac_file} 失败 - {e}")
                error_count += 1

        print()

    # 显示统计信息
    print("=== 重命名总结 ===")
    print(f"成功重命名: {success_count} 个文件")
    print(f"跳过（已存在）: {skip_count} 个文件")
    print(f"失败: {error_count} 个文件")
    print()

    if error_count == 0 and skip_count == 0:
        print("✅ 所有文件均已成功重命名！")
    elif error_count == 0:
        print("✅ 所有重命名操作已完成，部分文件被跳过。")
    else:
        print("⚠️  重命名完成，但存在一些错误。")
    print()


def main():
    # 确保终端支持 UTF-8 输出（避免 Windows GBK 编码问题）
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="将加密的 .flac 文件重命名为 .kgm")
    parser.add_argument("--path", default=".",
                        help="目标目录路径（默认：当前目录）")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.path)

    if not os.path.isdir(target_dir):
        print(f"错误: 目录不存在 - {target_dir}")
        sys.exit(1)

    print("=== FLAC 转 KGM 文件重命名工具 ===")
    print(f"目标目录: {target_dir}\n")

    rename_flac_to_kgm(target_dir)


if __name__ == "__main__":
    main()
