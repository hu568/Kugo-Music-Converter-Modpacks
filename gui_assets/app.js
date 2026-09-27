/*
 * 酷狗音乐转换工具箱 — 前端逻辑
 * Python(gui.py)通过 evaluate_js 调用 AppBridge.* 推送状态;
 * 页面通过 window.pywebview.api.* 调用 Python。
 */
'use strict';

// URL 参数 ?theme=light|dark 可强制主题(预览/测试用;实际运行跟随系统)
const __themeParam = new URLSearchParams(location.search).get('theme');
if (__themeParam === 'light' || __themeParam === 'dark') {
  document.documentElement.classList.add('theme-' + __themeParam);
}

const $ = (sel) => document.querySelector(sel);

const state = {
  files: [],      // [{path, name, dir, size, ext, encrypted}]
  running: false,
  usingMock: false,
};

/* ─── 工具 ──────────────────────────────────────────────── */

function fmtSize(bytes) {
  if (bytes === null || bytes === undefined || isNaN(bytes)) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
}

function esc(text) {
  const div = document.createElement('div');
  div.textContent = String(text ?? '');
  return div.innerHTML;
}

function callApi(method, ...args) {
  if (state.usingMock || !window.pywebview || !window.pywebview.api) {
    return mockApi(method, args);
  }
  return window.pywebview.api[method](...args);
}

/* ─── Python → JS 桥 ───────────────────────────────────── */

window.AppBridge = {
  syncFiles(files) {
    state.files = files || [];
    renderFileList();
  },

  setEngines(badges) {
    const box = $('#engine-badges');
    box.innerHTML = (badges || []).map(b =>
      `<span class="engine-badge${b.ok ? '' : ' missing'}" title="${esc(b.name)}">` +
      `<span class="engine-dot"></span>${esc(b.label)}</span>`
    ).join('');
  },

  setCacheStats(_text) {
    // 兼容 Python 推送:统计数字已直接展示在确认对话框中
  },

  setOutdir(text) {
    $('#footer-outdir').textContent = text;
  },

  resetRun() {
    state.running = true;
    setBusy(true);
    document.body.classList.add('is-running');
    switchTab('log'); // 处理开始后自动切到日志页签
    document.querySelectorAll('.kan-step').forEach(el => setStepClass(el, 'pending'));
    $('#log-view').innerHTML = '';
    $('#progress-wrap').classList.add('visible');
    window.AppBridge.setProgress('indeterminate', 0, '正在启动主程序…');
    $('#btn-start-text').textContent = '处理中…';
  },

  logLine(text, cls) {
    const log = $('#log-view');
    const line = document.createElement('span');
    line.className = 'log-line' + (cls ? ' ' + cls : '');
    line.textContent = text;
    log.appendChild(line);
    while (log.childElementCount > 600) log.removeChild(log.firstChild);
    log.scrollTop = log.scrollHeight;
  },

  setStep(idx, stepState) {
    const el = document.querySelector(`.kan-step[data-step="${idx}"]`);
    if (el) setStepClass(el, stepState);
  },

  setProgress(mode, ratio, text) {
    const bar = $('#progress-bar');
    if (mode === 'hide') {
      $('#progress-wrap').classList.remove('visible');
      return;
    }
    $('#progress-wrap').classList.add('visible');
    if (mode === 'indeterminate') {
      bar.classList.add('is-indeterminate', 'state-Indeterminate');
      $('#progress-indicator').style.width = '0%';
    } else {
      bar.classList.remove('is-indeterminate', 'state-Indeterminate');
      const r = Math.max(0, Math.min(100, Number(ratio) || 0));
      $('#progress-indicator').style.width = r + '%';
    }
    if (text !== undefined && text !== null) $('#progress-text').textContent = text;
  },

  runFinished(ok, kind, title, message) {
    state.running = false;
    setBusy(false);
    document.body.classList.remove('is-running');
    $('#btn-start-text').textContent = '开始处理';
    // 收尾:仍在运行的步骤按结果标记
    const finalState = ok ? 'done' : 'error';
    document.querySelectorAll('.kan-step.is-running').forEach(el => setStepClass(el, finalState));
    window.AppBridge.setProgress('determinate', 100, ok ? '处理完成' : '处理结束(有错误,详见日志)');
    showInfo(kind || (ok ? 'success' : 'error'), title, message);
  },

  alert(kind, title, message) {
    showInfo(kind, title, message);
  },
};

function setStepClass(el, stepState) {
  el.classList.remove('is-running', 'is-done', 'is-skip', 'is-error');
  if (stepState === 'running') el.classList.add('is-running');
  else if (stepState === 'done') el.classList.add('is-done');
  else if (stepState === 'skip') el.classList.add('is-skip');
  else if (stepState === 'error') el.classList.add('is-error');
}

/* ─── InfoBar ───────────────────────────────────────────── */

const INFO_GLYPH = { informational: '\uF167', success: '\uEC61', warning: '\uE814', error: '\uEB90' };

function showInfo(kind, title, message) {
  const slot = $('#infobar-slot');
  const k = INFO_GLYPH[kind] ? kind : 'informational';
  const bar = document.createElement('div');
  bar.className = `win-infobar win-infobar-${k}`;
  bar.innerHTML = `
    <div class="win-infobar-layout">
      <div class="win-infobar-standard-icon-area" aria-hidden="true">
        <span class="win-font-icon win-infobar-standard-icon">${INFO_GLYPH[k]}</span>
      </div>
      <div class="win-infobar-content-area">
        ${title ? `<div class="win-infobar-title">${esc(title)}</div>` : ''}
        <div class="win-infobar-message">${esc(message || '')}</div>
      </div>
      <button class="win-btn win-infobar-close-button uses-default-close-button-style" title="关闭">
        <span class="win-font-icon win-infobar-close-glyph">\uE711</span>
      </button>
    </div>`;
  bar.querySelector('.win-infobar-close-button').addEventListener('click', () => bar.remove());
  slot.innerHTML = '';
  slot.appendChild(bar);
}

/* ─── 文件列表渲染 ──────────────────────────────────────── */

function renderFileList() {
  const list = $('#file-list');
  const files = state.files;
  $('#file-count').textContent = `共 ${files.length} 个文件`;
  $('#btn-clear-list').disabled = files.length === 0 || state.running;
  $('#btn-start').disabled = files.length === 0 || state.running;

  $('#file-empty') && $('#file-empty').remove();
  list.innerHTML = '';
  if (!files.length) {
    const empty = document.createElement('div');
    empty.className = 'file-empty';
    empty.id = 'file-empty';
    empty.innerHTML = '<span class="win-font-icon" aria-hidden="true">\uE8D6</span><span>还没有添加文件</span>';
    list.appendChild(empty);
    return;
  }

  for (const f of files) {
    const item = document.createElement('div');
    item.className = 'file-row';
    const icon = f.encrypted ? '\uE72E' : '\uE8D6';
    const extText = String(f.ext || '').replace(/^\./, '').toUpperCase();
    item.innerHTML = `
      <span class="win-font-icon file-icon${f.encrypted ? ' encrypted' : ''}" title="${f.encrypted ? '酷狗加密格式' : '普通音频'}">${icon}</span>
      <div class="file-info">
        <span class="file-name">${esc(f.name)}</span>
        <span class="file-dir">${esc(f.dir)}</span>
      </div>
      <span class="file-ext-chip${f.encrypted ? ' encrypted' : ''}" title="${f.encrypted ? '酷狗加密格式' : '普通音频'}">${esc(extText)}</span>
      <span class="file-meta">${fmtSize(f.size)}</span>
      <button class="win-btn SubtleButtonStyle file-remove" title="移除">
        <span class="win-font-icon">\uE711</span>
      </button>`;
    item.querySelector('.file-remove').addEventListener('click', (e) => {
      e.stopPropagation();
      callApi('remove_file', f.path);
    });
    list.appendChild(item);
  }
}

/* ─── 忙碌状态 ──────────────────────────────────────────── */

function setBusy(busy) {
  for (const id of ['btn-add-files', 'btn-add-folder', 'btn-clear-list', 'btn-start', 'btn-clean']) {
    const el = $('#' + id);
    if (id === 'btn-clear-list' || id === 'btn-start') {
      el.disabled = busy || state.files.length === 0;
    } else {
      el.disabled = busy;
    }
  }
  $('#drop-zone').classList.toggle('disabled', busy);
  $('#card-files').classList.toggle('disabled', busy);
}

/* ─── 对话框 ────────────────────────────────────────────── */

let dialogOkHandler = null;

function openDialog(title, bodyHtml, okText, onOk) {
  $('#dialog-title').textContent = title;
  $('#dialog-body').innerHTML = bodyHtml;
  $('#dialog-ok').textContent = okText || '确认';
  dialogOkHandler = onOk;
  $('#dialog-overlay').hidden = false;
  $('#dialog-ok').focus();
}

function closeDialog() {
  $('#dialog-overlay').hidden = true;
  dialogOkHandler = null;
}

$('#dialog-ok').addEventListener('click', () => {
  const h = dialogOkHandler;
  closeDialog();
  if (h) h();
});
$('#dialog-cancel').addEventListener('click', closeDialog);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$('#dialog-overlay').hidden) closeDialog();
});

/* ─── 页签切换 ──────────────────────────────────────────── */

function switchTab(name) {
  const isMain = name === 'main';
  $('#tab-main').hidden = !isMain;
  $('#tab-log').hidden = isMain;
  $('#tab-btn-main').classList.toggle('is-selected', isMain);
  $('#tab-btn-main').setAttribute('aria-selected', String(isMain));
  $('#tab-btn-log').classList.toggle('is-selected', !isMain);
  $('#tab-btn-log').setAttribute('aria-selected', String(!isMain));
}

$('#tab-btn-main').addEventListener('click', () => switchTab('main'));
$('#tab-btn-log').addEventListener('click', () => switchTab('log'));

// 清空日志仅清空界面显示,不影响正在进行的处理
$('#btn-clear-log').addEventListener('click', () => {
  $('#log-view').innerHTML = '';
});

/* ─── 拖放反馈(真实文件路径由 Python 侧注册的 drop 事件接收) ── */

let dragDepth = 0;

window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('dragenter', (e) => {
  e.preventDefault();
  dragDepth++;
  $('#drop-zone').classList.add('drag-over');
});
window.addEventListener('dragleave', (e) => {
  e.preventDefault();
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) $('#drop-zone').classList.remove('drag-over');
});
window.addEventListener('drop', (e) => {
  e.preventDefault();
  dragDepth = 0;
  $('#drop-zone').classList.remove('drag-over');
});

/* ─── 按钮事件 ──────────────────────────────────────────── */

$('#drop-zone').addEventListener('click', () => callApi('pick_files'));
$('#btn-add-files').addEventListener('click', () => callApi('pick_files'));
$('#btn-add-folder').addEventListener('click', () => callApi('pick_folder'));
$('#btn-clear-list').addEventListener('click', () => callApi('clear_files'));
$('#btn-start').addEventListener('click', () => {
  if (state.running || !state.files.length) return;
  callApi('start_processing');
});
$('#btn-clean').addEventListener('click', async () => {
  try {
    const stats = await callApi('cache_stats');
    const body = `
      <p style="margin:0 0 8px">此操作会删除以下音乐文件,且<b>无法恢复</b>:</p>
      <ul style="margin:0; padding-left:20px">
        <li>input/ 中的 ${stats.input_count} 个音乐文件</li>
        <li>kgm-vpr-out/ 中的 ${stats.out_count} 个音乐文件(约 ${fmtSize(stats.out_bytes)})</li>
      </ul>
      <p style="margin:8px 0 0">保留:ffmpeg.exe、批量转MP3.bat 及其他非音乐文件。</p>`;
    openDialog('确认清理缓存?', body, '清空缓存', async () => {
      try {
        await callApi('clear_cache'); // 结果 InfoBar 与统计由 Python 侧推送
      } catch (err) {
        showInfo('error', '清理失败', String(err));
      }
    });
  } catch (err) {
    showInfo('error', '无法获取缓存信息', String(err));
  }
});

/* ─── 浏览器预览用的 Mock(pywebview 不存在时) ───────────── */

function mockApi(method, args) {
  console.warn('[mock] pywebview 桥不可用,使用 mock 数据:', method, args);
  const mock = {
    pick_files: () => {},
    pick_folder: () => {},
    remove_file: () => {},
    clear_files: () => window.AppBridge.syncFiles([]),
    cache_stats: () => ({ input_count: 3, out_count: 5, out_bytes: 68 * 1024 * 1024 }),
    start_processing: () => {},
    clear_cache: () => {},
    init: () => {},
  };
  return Promise.resolve(mock[method] ? mock[method](...args) : null);
}

function applyMockState() {
  state.usingMock = true;
  window.__appReady = true;   // 测试哨兵:mock 状态已就绪
  window.AppBridge.setEngines([
    { label: 'unlockKuGoWin', ok: true },
    { label: 'kgg-dec', ok: true },
    { label: 'ffmpeg', ok: true },
  ]);
  window.AppBridge.setOutdir('输出目录:kgm-vpr-out/(浏览器预览模式)');
  window.AppBridge.syncFiles([
    { path: 'C:\\Music\\歌1.kgm', name: '歌1.kgm', dir: 'C:\\Music', size: 8388608, ext: '.kgm', encrypted: true },
    { path: 'C:\\Music\\歌2.kgg.flac', name: '歌2.kgg.flac', dir: 'C:\\Music', size: 5242880, ext: '.kgg.flac', encrypted: true },
    { path: 'D:\\下载\\歌3.flac', name: '歌3.flac', dir: 'D:\\下载', size: 31457280, ext: '.flac', encrypted: false },
  ]);
  window.AppBridge.setCacheStats('当前可清理:input/ 中 3 个,kgm-vpr-out/ 中 5 个音乐文件(浏览器预览模式)');
  showInfo('informational', '浏览器预览模式', '未检测到 pywebview 桥,当前仅展示界面,按钮不会执行真实操作。');
}

/* ─── 初始化 ────────────────────────────────────────────── */

let bootstrapped = false;

function init() {
  if (bootstrapped) return;
  bootstrapped = true;
  window.__appReady = true;   // 测试哨兵:pywebview 桥初始化完成
  callApi('init').catch(err => showInfo('error', '初始化失败', String(err)));
}

function applyMockStateSafe() {
  if (bootstrapped) return;
  bootstrapped = true;
  applyMockState();
}

// pywebview 桥就绪事件 + 轮询兜底(后台窗口定时器可能被节流);
// URL 带 ?mock=1 时立即进入浏览器预览模式,便于在不支持桥的环境里查看界面
if (window.pywebview && window.pywebview.api) {
  init();
} else if (new URLSearchParams(location.search).has('mock')) {
  applyMockStateSafe();
} else {
  window.addEventListener('pywebviewready', init);
  (function waitForBridge(tries) {
    if (window.pywebview && window.pywebview.api) {
      init();
    } else if (tries > 19) {
      applyMockStateSafe();
    } else {
      setTimeout(() => waitForBridge(tries + 1), 100);
    }
  })(0);
}
