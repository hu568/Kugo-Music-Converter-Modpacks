# kgg-dec

酷狗 `kgg` 文件解密工具。

请尽量在下载文件的设备上操作，避免密钥丢失。

## 使用方法 (快捷)

1. 双击 `kgg-dec.exe` 开始解密当前目录。

## 使用方法 (命令行)

1. 启动 `kgg-dec.exe`，其中第一个参数为含有 `kgg` 文件的目录。
2. 你也可以使用 `--` 来将参数后的 `-` 开头的参数视为输入文件或目录。
3. 你可以指定多项输入文件或目录。

### 其它参数

* `--scan-all-file-ext` (可选，`0` 或 `1`): 是否扫描所有文件后缀名。默认为 `0`，只扫描 `kgg` 文件。
* `--db` (可选): 指定 `KGMusicV3.db` 的路径。默认为 `%AppData%/Kugou8/KGMusicV3.db`。
* `--suffix` (可选): 指定解密后文件的后缀。默认为 `_kgg-dec`。

### 使用示例

* `kgg-dec.exe "D:\Music"`: 解密 `D:\Music` 目录下的所有 `*.kgg` 文件。
* `kgg-dec.exe "D:\Music" "D:\KGG\1.kgg"`: 解密 `D:\Music` 目录下的所有 `*.kgg` 文件，以及 `1.kgg`。
* `kgg-dec.exe "D:\Music" --scan-all-file-ext 1`: 尝试将 `D:\Music` 目录下的所有文件视为 `kgg` 文件来解密。
* `kgg-dec.exe "D:\Music" --suffix ""`: 解密后不添加额外的后缀。

指定完参数后可以指定任意数量的文件或目录。

## 错误排查

1. 需要至少播放一次 `kgg` 文件，并确保酷狗能正常播放。
    - 如果还是无效，请尝试使用酷狗重新下载，在同一个设备上进行下载与解密操作。
2. 文件后缀名嗅探代码只支持：`ogg` / `flac`。
    * 其他格式会被识别为 `mp3`。

## 构建

在 Windows 下使用 CMake + Visual Studio 2022 构建。

第一次构建前请到 `third-party/sqlite3` 目录下执行 `fetch_sqlite3.sh`，或手动下载源码放置到对应的位置。

然后就可以利用 CMake 构建了：

```cmd
cmake --preset vs -DCMAKE_BUILD_TYPE=Release
cmake --build --preset vs-release --config Release
copy /y README.MD .\\build\\vs2022\\
```

### CMake 参数

CMake 支持以下参数：

- `USE_WIN_SQLITE3` - 使用 Windows 内置的 SQLite3 链接库（仅限 Windows + MSVC 编译环境）。
- `USE_WIN_CRYPTO` - 使用 Windows 内置的加密/哈希实现，而非软件实现（仅限 Windows 目标）。
- `USE_SYSTEM_SQLITE3` - 使用外部的 SQLite3 实现 (Debian: `libsqlite3-dev`)，找不到时会报错。
- `USE_OpenSSL` - 使用 OpenSSL 的加密/哈希实现 (Debian: `libssl-dev`)，找不到时会报错。

Ubuntu 下编译发布版，不使用外部库：

```sh
cmake -G "Ninja Multi-Config" -B build/linux-all -DUSE_SYSTEM_SQLITE3=0 -DUSE_OPENSSL=0
cmake --build build/linux-all --config Release -j
```

Ubuntu 下编译发布版，链接到现有的库：

```sh
cmake -G "Ninja Multi-Config" -B build/linux-ext -DUSE_SYSTEM_SQLITE3=1 -DUSE_OPENSSL=1
cmake --build build/linux-ext --config Release -j
```

### 第三方软件

该程序用到了以下第三方软件：

- [SQLite3](https://www.sqlite.org/) (Public Domain)
- [Tiny AES in C](https://github.com/kokke/tiny-AES-c) (Public Domain)
- [MD5.c](https://github.com/freebsd/freebsd-src/blob/release/14.2.0/sys/kern/md5c.c) (from FreeBSD)
    - Derived from the "RSA Data Security, Inc. MD5 Message-Digest Algorithm".

### Windows 7 用户注意

请从 SQLite 官网下载 [`sqlite-dll-win-x64-*.zip`](https://www.sqlite.org/download.html#win32)
并将压缩包内的 `sqlite3.dll` 放置到 `kgg-dec.exe` 同目录下，并更名为 `winsqlite3.dll`。

Windows 10 或更新版本不需要此操作，因为 Windows 10 或以上的版本内置该文件。 
