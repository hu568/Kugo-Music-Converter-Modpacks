"""
Kugo Music Converter — 图形界面启动器(pywebview)

三个功能:
    1. 添加文件 —— 点击选择或拖入文件/文件夹(仅暂存到列表,不复制到 input/)
    2. 开始处理 —— 把列表中的文件复制到 input/,再调用主程序 main.py --auto 执行完整流程
    3. 清理缓存 —— 删除 input/ 与 kgm-vpr-out/ 中的音乐文件(保留 ffmpeg.exe 与 批量转MP3.bat)

用法:
    python gui.py
"""

import os
import re
import sys
import json
import shutil
import subprocess
import threading

import webview
from webview.dom import DOMEventHandler

# 项目根目录(exe 所在目录,兼容 PyInstaller 打包)
if getattr(sys, 'frozen', False):
    PROJECT_DIR = os.path.dirname(sys.executable)
    ASSETS_DIR = os.path.join(getattr(sys, '_MEIPASS', PROJECT_DIR), 'gui_assets')
else:
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(PROJECT_DIR, 'gui_assets')

INPUT_DIR = os.path.join(PROJECT_DIR, "input")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "kgm-vpr-out")
MAIN_EXE = os.path.join(PROJECT_DIR, "Kugo-Music-Converter.exe")
MAIN_PY = os.path.join(PROJECT_DIR, "main.py")

UNLOCK_TOOL = os.path.join(PROJECT_DIR, "unlockKuGoWin-64.exe")
UNLOCK_TOOL_32 = os.path.join(PROJECT_DIR, "unlockKuGoWin-32.exe")
KGG_DEC = os.path.join(PROJECT_DIR, "kgg-dec.exe")
FFMPEG = os.path.join(OUTPUT_DIR, "ffmpeg.exe")
KGM_MASK = os.path.join(PROJECT_DIR, "kgm.mask")

# 普通音频格式(任意常见音乐格式)
AUDIO_EXTS = {
    ".mp3", ".flac", ".wav", ".wave", ".ogg", ".oga", ".opus", ".m4a", ".m4b",
    ".aac", ".mp2", ".ape", ".wma", ".wv", ".tta", ".dsf", ".dff", ".aif",
    ".aiff", ".alac", ".mka", ".ac3", ".dts", ".spx", ".tak",
}
# 酷狗加密格式
KUGOU_EXTS = {".kgm", ".kgma", ".kgg", ".vpr"}
# 清理缓存时必须保留的文件
CLEAN_KEEP = {"批量转MP3.bat", "ffmpeg.exe"}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# 子进程不创建控制台窗口(主程序等都是 console 程序,不加此标志会弹出黑色终端)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# 看板步骤(与 main.py 的流程一一对应)
STEP_COUNT = 6


def is_supported_music(name: str) -> bool:
    """判断文件名是否为可处理的音频/酷狗加密文件(含 .kgg.flac 伪装格式)"""
    lower = name.lower()
    if lower.endswith(".kgg.flac"):
        return True
    return os.path.splitext(lower)[1] in (AUDIO_EXTS | KUGOU_EXTS)


def is_encrypted(name: str) -> bool:
    lower = name.lower()
    if lower.endswith(".kgg.flac"):
        return True
    return os.path.splitext(lower)[1] in KUGOU_EXTS


class Api:
    """暴露给前端 JS 的接口(window.pywebview.api.*)"""

    def __init__(self) -> None:
        # pywebview 生成 JS API 时会递归遍历所有公开属性,window 引用必须用 _ 前缀,
        # 否则会把整个 WinForms/WebView2 控件树拖进控制台报错
        self._window = None
        self._files: dict[str, dict] = {}   # normcase(绝对路径) -> 文件信息
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._running = False
        self._step_states = ["pending"] * STEP_COUNT

    # ── JS 推送工具 ────────────────────────────────────────

    def _js(self, script: str) -> None:
        if self._window is None:
            return
        try:
            self._window.evaluate_js(script)
        except Exception:
            pass

    def _push_json(self, func: str, payload) -> None:
        self._js(f"AppBridge.{func}({json.dumps(payload, ensure_ascii=False)})")

    def _alert(self, kind: str, title: str, message: str) -> None:
        self._push_json("alert", [kind, title, message])

    def _set_step(self, idx: int, state: str, only_if: str | None = None) -> None:
        if not (0 <= idx < STEP_COUNT):
            return
        if only_if is not None and self._step_states[idx] != only_if:
            return
        self._step_states[idx] = state
        self._push_json("setStep", [idx, state])

    def _reset_steps(self) -> None:
        self._step_states = ["pending"] * STEP_COUNT

    # ── 初始化 ─────────────────────────────────────────────

    def init(self):
        self._push_json("setEngines", self._check_engines())
        self._push_json(
            "setOutdir", f"输出目录:{os.path.join(os.path.basename(PROJECT_DIR), 'kgm-vpr-out')}"
        )
        self._sync_files()
        return True

    def _check_engines(self) -> list[dict]:
        unlock_ok = os.path.isfile(UNLOCK_TOOL) or os.path.isfile(UNLOCK_TOOL_32)
        return [
            {"label": "unlockKuGoWin", "name": UNLOCK_TOOL, "ok": unlock_ok},
            {"label": "kgg-dec", "name": KGG_DEC, "ok": os.path.isfile(KGG_DEC)},
            {"label": "ffmpeg", "name": FFMPEG, "ok": os.path.isfile(FFMPEG)},
            {"label": "kgm.mask", "name": KGM_MASK, "ok": os.path.isfile(KGM_MASK)},
        ]

    # ── 功能 1:添加文件(暂存,不复制) ─────────────────────

    def pick_files(self):
        if self._running or self._window is None:
            return None
        exts = sorted((AUDIO_EXTS | KUGOU_EXTS) - {".wave"})
        filter_str = "*.kgg.flac;" + ";".join(f"*{e}" for e in exts)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=(f"音乐与加密文件 ({filter_str})", "所有文件 (*.*)"),
        )
        if result:
            self.add_paths(list(result))
        return None

    def pick_folder(self):
        if self._running or self._window is None:
            return None
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            self.add_paths(list(result))
        return None

    def add_paths(self, paths):
        """把文件/文件夹加入暂存列表(文件夹递归扫描音乐文件)"""
        if not isinstance(paths, (list, tuple)):
            paths = [paths]
        added, ignored = 0, 0
        with self._lock:
            for raw in paths:
                path = str(raw)
                if os.path.isdir(path):
                    for root, _dirs, names in os.walk(path):
                        for name in names:
                            if is_supported_music(name):
                                if self._add_file(os.path.join(root, name)):
                                    added += 1
                            else:
                                ignored += 1
                elif os.path.isfile(path):
                    if is_supported_music(os.path.basename(path)):
                        if self._add_file(path):
                            added += 1
                    else:
                        ignored += 1
                else:
                    ignored += 1
            total = len(self._files)
        self._sync_files()
        if added == 0:
            self._alert(
                "informational", "没有可添加的音乐文件",
                "本次选择的路径中未找到支持的音频/加密文件,已忽略。" if ignored else "",
            )
        return {"added": added, "ignored": ignored, "total": total}

    def _add_file(self, path: str) -> bool:
        key = os.path.normcase(os.path.abspath(path))
        if key in self._files:
            return False
        name = os.path.basename(path)
        self._files[key] = {
            "path": os.path.abspath(path),
            "name": name,
            "dir": os.path.dirname(os.path.abspath(path)),
            "size": os.path.getsize(path),
            "ext": os.path.splitext(name)[1].lower(),
            "encrypted": is_encrypted(name),
        }
        return True

    def remove_file(self, path: str):
        with self._lock:
            self._files.pop(os.path.normcase(str(path)), None)
        self._sync_files()
        return True

    def clear_files(self):
        with self._lock:
            self._files.clear()
        self._sync_files()
        return True

    def get_files(self):
        return self.list_files()

    def list_files(self) -> list[dict]:
        return sorted(self._files.values(), key=lambda f: (f["dir"].lower(), f["name"].lower()))

    def _sync_files(self) -> None:
        self._push_json("syncFiles", self.list_files())

    # ── 拖放(pywebview 在 Python 侧注册 drop 事件才有真实路径) ──

    def handle_drop(self, event):
        try:
            data = (event or {}).get("dataTransfer") or {}
            files = data.get("files") or []
            paths = [f["pywebviewFullPath"] for f in files if f.get("pywebviewFullPath")]
        except Exception:
            return None
        if paths:
            self.add_paths(paths)
        return None

    # ── 功能 2:开始处理 ───────────────────────────────────

    def start_processing(self):
        if self._running:
            return {"ok": False, "message": "已有任务正在处理"}
        with self._lock:
            snapshot = self.list_files()
        if not snapshot:
            return {"ok": False, "message": "请先添加文件"}
        self._running = True  # 同步置位,防止连续点击重复启动
        threading.Thread(target=self._run_flow, args=(snapshot,), daemon=True).start()
        return {"ok": True}

    def _run_flow(self, files: list[dict]) -> None:
        self._reset_steps()
        self._js("AppBridge.resetRun()")

        # 1. 复制暂存文件到 input/(这一步之前文件从未离开原位置)
        self._log("=== 开始处理:复制文件到 input/ ===", "log-step")
        copied, failed = self._copy_to_input(files)
        if copied:
            self._log(f"已复制/就绪 {copied} 个文件到 input/" + (f",失败 {failed} 个" if failed else ""), "log-ok" if not failed else "log-warn")
        if copied == 0:
            self._log("没有文件被复制到 input/,流程中止", "log-err")
            self._finish(ok=False, kind="error", title="处理失败",
                         message="没有文件被复制到 input/,请检查文件是否被占用后重试。")
            return

        # 2. 调用主程序执行完整流程
        self._log("=== 调用主程序执行完整流程 ===", "log-step")
        cmd = self._main_command()
        if cmd is None:
            self._log("找不到主程序(Kugo-Music-Converter.exe 或 main.py)", "log-err")
            self._finish(ok=False, kind="error", title="处理失败", message="找不到主程序。")
            return

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        try:
            self._proc = subprocess.Popen(
                cmd, cwd=PROJECT_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                env=env, creationflags=NO_WINDOW,
            )
        except Exception as e:
            self._log(f"启动主程序失败: {e}", "log-err")
            self._finish(ok=False, kind="error", title="处理失败", message=f"启动主程序失败:{e}")
            return

        # 逐行读取并推送日志(不读会导致管道写满、主程序卡死)
        returncode = 0
        try:
            for line in self._proc.stdout:
                self._handle_line(line)
        except Exception as e:
            self._log(f"读取主程序输出失败: {e}", "log-err")
        finally:
            returncode = self._proc.wait()
            self._proc = None

        ok = returncode == 0
        self._log(f"主程序退出,返回码: {returncode}", "log-ok" if ok else "log-warn")
        if ok:
            self._finish(ok=True, kind="success", title="处理完成",
                         message=f"全部流程执行完毕,输出在 kgm-vpr-out/({copied} 个文件已处理)。")
        else:
            self._finish(ok=False, kind="warning", title="处理结束(部分出错)",
                         message="主程序返回码非 0,部分步骤可能未成功,请查看日志。"
                                 "若 KGG 提示缺少密钥,请先用酷狗客户端播放一次该文件。")

    def _finish(self, ok: bool, kind: str, title: str, message: str) -> None:
        self._running = False
        self._push_json("runFinished", [ok, kind, title, message])

    def _main_command(self) -> list[str] | None:
        """优先使用打包后的主程序 exe,开发环境直接跑 main.py"""
        if getattr(sys, 'frozen', False):
            if os.path.isfile(MAIN_EXE):
                return [MAIN_EXE, "--auto"]
            return None
        if os.path.isfile(MAIN_PY):
            return [sys.executable, MAIN_PY, "--auto"]
        return None

    def _copy_to_input(self, files: list[dict]) -> tuple[int, int]:
        """复制暂存文件到 input/ 顶层(main.py 只扫描该目录顶层)"""
        os.makedirs(INPUT_DIR, exist_ok=True)
        copied, failed = 0, 0
        used = {n.lower() for n in os.listdir(INPUT_DIR)}
        for f in files:
            src, name = f["path"], f["name"]
            stem, ext = os.path.splitext(name)
            target = name
            # 与 input/ 中已有文件同名时不覆盖,自动追加序号
            n = 2
            while target.lower() in used:
                target = f"{stem} ({n}){ext}"
                n += 1
            dst = os.path.join(INPUT_DIR, target)
            try:
                shutil.copy2(src, dst)
                used.add(target.lower())
                if target != name:
                    self._log(f"  → 复制: {name} (重名,已改名 {target})", "log-warn")
                else:
                    self._log(f"  → 复制: {name}", "log-dim")
                copied += 1
            except Exception as e:
                self._log(f"  → 复制失败: {name} - {e}", "log-err")
                failed += 1
        return copied, failed

    # ── 主程序输出解析 → 看板/日志 ─────────────────────────

    def _log(self, line: str, cls: str | None = None) -> None:
        self._push_json("logLine", [line, cls])

    def _handle_line(self, raw: str) -> None:
        line = ANSI_RE.sub("", raw.rstrip("\r\n"))
        text = line.strip()
        if not text:
            self._log("")
            return

        cls = None
        if "===" in line and "步骤" in line:
            cls = "log-step"
            self._match_step_header(text)
        elif text.startswith("✓"):
            cls = "log-ok"
        elif text.startswith("⚠"):
            cls = "log-warn"
        elif text.startswith("✗"):
            cls = "log-err"

        self._match_progress_markers(text)

        m = re.search(r"\[(\d+)/(\d+)\]\s*正在转换[:：]?\s*(.*)", text)
        if m:
            idx, total = int(m.group(1)), int(m.group(2))
            ratio = idx / total * 100 if total else 0
            self._push_json("setProgress", ["determinate", ratio, f"正在转换 MP3:{idx}/{total} {m.group(3)}"])

        self._log(line, cls)

    def _match_step_header(self, text: str) -> None:
        if "=== 步骤 1" in text:
            self._set_step(0, "running")
        elif "=== 步骤 2" in text:
            self._set_step(0, "done", only_if="running")
            self._set_step(1, "running")
        elif "=== 步骤 3&4" in text:
            self._set_step(1, "done", only_if="running")
            self._set_step(2, "running")
            self._set_step(3, "running")
        elif "=== 步骤 4" in text:
            self._set_step(2, "done", only_if="running")
            self._set_step(3, "running")
        elif "=== 步骤 5" in text:
            self._set_step(2, "done", only_if="running")
            self._set_step(3, "done", only_if="running")
            self._set_step(4, "running")
        elif "=== 步骤 6" in text:
            self._set_step(4, "done", only_if="running")
            self._set_step(5, "running")

    def _match_progress_markers(self, text: str) -> None:
        """根据 main.py 的成功/跳过/警告输出更新看板状态"""
        if "复制完成:" in text:
            self._set_step(0, "done", only_if="running")
        elif "重命名完成:" in text:
            self._set_step(1, "done", only_if="running")
        elif "unlockKuGoWin 未找到" in text:
            self._set_step(2, "skip")
        elif "没有找到 .kgm/.kgma/.vpr 文件" in text:
            self._set_step(2, "skip")
        elif "KGG 处理完成" in text:
            self._set_step(3, "done", only_if="running")
        elif "没有找到 .kgg 文件" in text:
            self._set_step(3, "skip")
        elif "缺少 kgg-dec.exe" in text:
            self._set_step(3, "error")
        elif "批量转换完成" in text:
            self._set_step(4, "done", only_if="running")
        elif "没有 FLAC/OGG 文件" in text:
            self._set_step(4, "skip")
        elif "清理完成" in text:
            self._set_step(5, "done", only_if="running")

    # ── 功能 3:清理缓存 ───────────────────────────────────

    def cache_stats(self) -> dict:
        input_count = 0
        if os.path.isdir(INPUT_DIR):
            input_count = sum(
                1 for n in os.listdir(INPUT_DIR)
                if os.path.isfile(os.path.join(INPUT_DIR, n)) and is_supported_music(n)
            )
        out_count, out_bytes = self._scan_output_music()
        return {"input_count": input_count, "out_count": out_count, "out_bytes": out_bytes}

    def clear_cache(self) -> dict:
        """删除 input/ 与 kgm-vpr-out/ 中的音乐文件(保留 CLEAN_KEEP 与其他文件)"""
        deleted, freed, errors = 0, 0, []

        # input/:仅顶层(main.py 也只读取顶层)
        if os.path.isdir(INPUT_DIR):
            for name in os.listdir(INPUT_DIR):
                path = os.path.join(INPUT_DIR, name)
                if os.path.isfile(path) and is_supported_music(name):
                    try:
                        freed += os.path.getsize(path)
                        os.remove(path)
                        deleted += 1
                    except Exception as e:
                        errors.append(f"input/{name}: {e}")

        # kgm-vpr-out/:音乐文件(递归),排除 CLEAN_KEEP
        for root, _dirs, names in os.walk(OUTPUT_DIR):
            for name in names:
                if name in CLEAN_KEEP or not is_supported_music(name):
                    continue
                path = os.path.join(root, name)
                try:
                    freed += os.path.getsize(path)
                    os.remove(path)
                    deleted += 1
                except Exception as e:
                    errors.append(f"kgm-vpr-out/{name}: {e}")

        self._push_json("setCacheStats", [f"当前可清理:input/ 中 {self.cache_stats()['input_count']} 个,"
                                          f"kgm-vpr-out/ 中 {self.cache_stats()['out_count']} 个音乐文件"])
        if errors:
            self._alert("warning", "清理完成(部分失败)",
                        f"已删除 {deleted} 个文件,释放约 {freed / 1024 / 1024:.1f} MB。"
                        f"{len(errors)} 个文件删除失败:{errors[0]}")
        else:
            self._alert("success", "清理完成", f"已删除 {deleted} 个音乐文件,释放约 {freed / 1024 / 1024:.1f} MB。")
        return {"deleted": deleted, "bytes": freed, "errors": errors}

    def _scan_output_music(self) -> tuple[int, int]:
        count, total = 0, 0
        if os.path.isdir(OUTPUT_DIR):
            for root, _dirs, names in os.walk(OUTPUT_DIR):
                for name in names:
                    if name in CLEAN_KEEP or not is_supported_music(name):
                        continue
                    try:
                        total += os.path.getsize(os.path.join(root, name))
                        count += 1
                    except OSError:
                        pass
        return count, total

    # ── 退出清理 ───────────────────────────────────────────

    def shutdown(self) -> None:
        """窗口关闭时终止正在运行的主程序进程树"""
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True, timeout=10, creationflags=NO_WINDOW,
                )
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def main() -> None:
    # 确保 UTF-8 输出(避免 Windows GBK 编码问题)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    api = Api()

    window = webview.create_window(
        "酷狗音乐转换工具箱",
        os.path.join(ASSETS_DIR, "index.html"),
        js_api=api,
        width=1000,
        height=840,
        min_size=(780, 640),
        background_color="#F3F3F3",
    )
    api._window = window

    def _on_drop(event):
        api.handle_drop(event)

    def _on_loaded():
        # 拖放必须在 Python 侧通过 DOM API 注册,pywebview 才会回传真实文件路径
        window.dom.document.events.drop += DOMEventHandler(
            _on_drop, prevent_default=True, stop_propagation=True
        )

    def _on_closing():
        api.shutdown()
        return True

    window.events.loaded += _on_loaded
    window.events.closing += _on_closing

    webview.start()


if __name__ == "__main__":
    main()
