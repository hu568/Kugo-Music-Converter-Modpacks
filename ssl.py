# 打包体积优化桩:真正的 ssl 模块会连带引入 libssl-3.dll / libcrypto-3.dll(约 5.7MB)。
# 本 GUI 通过 pywebview 内置 HTTP 服务加载本地页面,永远走不到 https 分支;
# webview/http.py 顶层 `import ssl` 只是为了其中的 ssl.SSLContext()(仅 https 分支调用)。
# 此桩让 PyInstaller 用它顶替标准库 ssl,从而不打进 OpenSSL 全家桶。
# 注意:它同时影响源码方式运行(python gui.py),同样安全;若将来需要 https 再删除本文件。
def SSLContext(*args, **kwargs):
    raise NotImplementedError("本工具不使用 ssl,真模块已被打包体积桩替换")
