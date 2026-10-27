/* zlib-nas front-end: no framework, no build step. */

const I18N = {
  zh: {
    tab_saved: "收藏", tab_search: "搜索", tab_downloads: "下载",
    tab_library: "本地库", tab_settings: "设置",
    filter_saved: "在收藏里筛选…", sync_saved: "同步收藏",
    search_ph: "书名、作者、ISBN…", btn_search: "搜索",
    any_lang: "任意语言", any_format: "任意格式",
    resume: "继续队列", pause: "暂停队列",
    col_title: "书名", col_status: "状态", col_progress: "进度",
    col_file: "文件", col_size: "大小",
    st_done: "已完成", st_running: "下载中", st_queued: "排队中",
    st_paused: "已暂停", st_failed: "失败",
    settings_account: "账号",
    settings_hint: "填写 Z-Library 镜像域名并登录。密码只在登录时使用一次，不会被保存；保存下来的只有会话 Cookie。",
    label_domain: "镜像域名", label_email: "邮箱", label_password: "密码",
    advanced_cookie: "或直接粘贴 Cookie",
    btn_login: "登录", btn_logout: "退出",
    settings_about: "关于", export: "导出数据 JSON",
    about_text: "自用工具：把自己的 Z-Library 账号搬到 NAS 上，收藏同步、搜索、带额度守卫的下载队列。",
    empty: "这里还什么都没有",
    search_hint: "输入书名或作者，开始搜索",
    download: "下载", reload: "重试", prev: "上一页", next: "下一页",
    syncing: "同步中…", searching: "搜索中…",
    not_configured: "还没有配置账号，去「设置」登录",
    logged_in: "已登录", login_ok: "登录成功",
    owned: "已下载", in_queue: "队列中", quota: "今日额度",
    downloaded: "已加入队列", synced: "已同步 {n} 本",
    confirm_logout: "确定退出并清除本地会话？",
  },
  en: {
    tab_saved: "Wishlist", tab_search: "Search", tab_downloads: "Downloads",
    tab_library: "Library", tab_settings: "Settings",
    filter_saved: "Filter wishlist…", sync_saved: "Sync wishlist",
    search_ph: "Title, author, ISBN…", btn_search: "Search",
    any_lang: "Any language", any_format: "Any format",
    resume: "Resume queue", pause: "Pause queue",
    col_title: "Title", col_status: "Status", col_progress: "Progress",
    col_file: "File", col_size: "Size",
    st_done: "Done", st_running: "Downloading", st_queued: "Queued",
    st_paused: "Paused", st_failed: "Failed",
    settings_account: "Account",
    settings_hint: "Enter your Z-Library mirror domain and sign in. The password is used once and never stored; only the session cookie is kept.",
    label_domain: "Mirror domain", label_email: "Email", label_password: "Password",
    advanced_cookie: "Or paste cookies directly",
    btn_login: "Sign in", btn_logout: "Sign out",
    settings_about: "About", export: "Export data as JSON",
    about_text: "A personal tool: bring your Z-Library account to your NAS with wishlist sync, search and a quota-aware download queue.",
    empty: "Nothing here yet",
    search_hint: "Type a title or an author to start",
    download: "Download", reload: "Retry", prev: "Prev", next: "Next",
    syncing: "Syncing…", searching: "Searching…",
    not_configured: "Not configured yet — sign in under Settings",
    logged_in: "Signed in", login_ok: "Signed in",
    owned: "Owned", in_queue: "Queued", quota: "Today's quota",
    downloaded: "Queued", synced: "Synced {n} books",
    confirm_logout: "Sign out and clear the local session?",
  },
};

const state = {
  lang: localStorage.getItem("zl-lang") || "zh",
  status: null,
  savedBooks: [],
  searchResult: null,
  searchPage: 1,
  searchQuery: "",
  owned: new Map(),
  pollTimer: null,
};

/* Inline so the placeholder never depends on an emoji font being installed. */
const BOOK_ICON =
  '<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" ' +
  'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H19a1 1 0 0 1 1 1v13.5"/>' +
  '<path d="M4 4.5V19a2 2 0 0 0 2 2h14"/>' +
  '<path d="M8 7h8M8 11h6"/></svg>';

const $ = (id) => document.getElementById(id);
const t = (key) => (I18N[state.lang] && I18N[state.lang][key]) || I18N.zh[key] || key;

/* ------------------------------------------------------------------ helpers */

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

function bytes(size) {
  if (!size) return "";
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let value = Number(size);
  while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1; }
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => node.classList.remove("show"), 2600);
}

async function api(path, options = {}) {
  const init = { headers: {}, ...options };
  if (init.body && typeof init.body !== "string") {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(init.body);
  }
  const response = await fetch(path, init);
  const type = response.headers.get("content-type") || "";
  const payload = type.includes("json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
  }
  return payload;
}

function applyLanguage() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[i18n]").forEach((node) => {
    node.textContent = t(node.getAttribute("i18n"));
  });
  document.querySelectorAll("[i18n-ph]").forEach((node) => {
    node.placeholder = t(node.getAttribute("i18n-ph"));
  });
  $("btnLang").textContent = state.lang === "zh" ? "EN" : "中";
  renderSaved();
  renderDownloads(state.lastDownloads || []);
  renderLibrary(state.lastLibrary || []);
  if (state.searchResult) renderSearch(state.searchResult);
}

/* -------------------------------------------------------------------- quota */

function renderQuota() {
  const panel = $("quota");
  const configured = !!(state.status && state.status.configured);
  panel.style.display = configured ? "flex" : "none";

  const quota = state.status && state.status.quota;
  const bar = $("quotaFill");
  const text = $("quotaText");
  if (!quota || !quota.limit) {
    bar.style.width = "0%";
    text.textContent = quota ? `${quota.today}/${quota.limit}` : "—";
    return;
  }
  const ratio = Math.max(0, Math.min(1, quota.left / quota.limit));
  bar.style.width = `${ratio * 100}%`;
  bar.className = "quota-fill" + (quota.left === 0 ? " empty" : quota.left <= 2 ? " low" : "");
  text.textContent = `${t("quota")} ${quota.left}/${quota.limit}`;
  $("account").textContent = (state.status.account && state.status.account.name) || "";
}

/* -------------------------------------------------------------------- books */

function bookCard(book) {
  const cover = book.cover
    ? `<img class="cover" loading="lazy" src="/api/cover?u=${encodeURIComponent(book.cover)}" alt="">`
    : `<div class="cover placeholder">${BOOK_ICON}</div>`;
  const known = state.owned.get(`${book.id}:${book.hash}`) || state.owned.get(book.sha256);
  const owned = known === "done";
  const queued = !!known && !owned;
  const meta = [book.author, book.year, book.filesize_text || bytes(book.filesize)]
    .filter(Boolean).map(esc).join(" · ");

  return `
    <div class="card-book">
      ${cover}
      <div class="book-body">
        <div class="book-title" title="${esc(book.title)}">${esc(book.title)}</div>
        <div class="book-meta" title="${esc(book.author)}">${meta}</div>
        <div class="book-actions">
          <span class="badge">${esc(book.extension || "")}</span>
          ${owned ? `<span class="badge owned">${t("owned")}</span>` : ""}
          ${queued ? `<span class="badge queued">${t("in_queue")}</span>` : ""}
          <button class="btn small primary" data-download="${esc(book.id)}"
            data-hash="${esc(book.hash)}" data-title="${esc(book.title)}"
            data-author="${esc(book.author)}" data-ext="${esc(book.extension || "")}"
            ${known ? "disabled" : ""}>${t("download")}</button>
        </div>
      </div>
    </div>`;
}

function renderSaved() {
  const query = ($("savedFilter").value || "").toLowerCase();
  const books = state.savedBooks.filter((book) =>
    !query || `${book.title} ${book.author}`.toLowerCase().includes(query)
  );
  const grid = $("savedGrid");
  grid.innerHTML = books.length
    ? books.map(bookCard).join("")
    : `<div class="empty">${t("empty")}</div>`;
  $("savedCount").textContent = state.savedBooks.length
    ? `${books.length} / ${state.savedBooks.length}`
    : "";
}

function renderSearch(result) {
  const grid = $("searchGrid");
  if (!result || !result.books || !result.books.length) {
    grid.innerHTML = `<div class="empty">${t("empty")}</div>`;
    $("searchPager").innerHTML = "";
    return;
  }
  grid.innerHTML = result.books.map(bookCard).join("");
  const pager = $("searchPager");
  pager.innerHTML = "";
  if (result.pages > 1) {
    const prev = document.createElement("button");
    prev.className = "btn ghost";
    prev.textContent = t("prev");
    prev.disabled = state.searchPage <= 1;
    prev.onclick = () => runSearch(state.searchPage - 1);
    const label = document.createElement("span");
    label.className = "muted";
    label.textContent = `${result.page} / ${result.pages}`;
    const next = document.createElement("button");
    next.className = "btn ghost";
    next.textContent = t("next");
    next.disabled = !result.has_next;
    next.onclick = () => runSearch(state.searchPage + 1);
    pager.append(prev, label, next);
  }
}

/* The CSS class keeps the English status name; only the label is translated. */
const STATUS_CLASS = ["queued", "running", "done", "paused", "failed"];

function statusLabel(status) {
  const dictionary = I18N[state.lang] || I18N.zh;
  return dictionary["st_" + status] || status;
}

function renderDownloads(records) {
  state.lastDownloads = records;
  const body = $("downloadsBody");
  if (!records.length) {
    body.innerHTML = `<tr><td colspan="4" class="muted">${t("empty")}</td></tr>`;
    return;
  }
  body.innerHTML = records.map((record) => {
    const percent = record.bytes_total
      ? Math.min(100, (record.bytes_done / record.bytes_total) * 100)
      : 0;
    const progress = record.status === "running"
      ? `<div class="progress"><i style="width:${percent}%"></i></div>`
      : record.status === "done" ? bytes(record.bytes_done) : "";
    return `
      <tr>
        <td>
          <div>${esc(record.title)}</div>
          <div class="muted">${esc(record.author || "")}</div>
          ${record.error ? `<div class="muted" style="color:var(--err)">${esc(record.error)}</div>` : ""}
        </td>
        <td><span class="status ${STATUS_CLASS.includes(record.status) ? record.status : ""}">${esc(statusLabel(record.status))}</span></td>
        <td>${progress}</td>
        <td>${record.status === "failed"
          ? `<button class="btn small" data-retry="${record.id}">${t("reload")}</button>` : ""}</td>
      </tr>`;
  }).join("");
}

function renderLibrary(files) {
  state.lastLibrary = files;
  const body = $("libraryBody");
  if (!files.length) {
    body.innerHTML = `<tr><td colspan="3" class="muted">${t("empty")}</td></tr>`;
    return;
  }
  body.innerHTML = files.map((file) => `
    <tr>
      <td>${esc(file.name)}</td>
      <td class="muted">${bytes(file.size)}</td>
      <td><a class="btn small ghost" href="/api/library/${encodeURIComponent(file.name)}">↓</a></td>
    </tr>`).join("");
}

/* --------------------------------------------------------------------- data */

async function refreshStatus() {
  try {
    state.status = await api("/api/status");
  } catch (error) {
    state.status = { configured: false, error: error.message };
  }
  renderQuota();

  const queue = state.status.queue || {};
  $("queueNotice").textContent = queue.paused ? queue.paused_reason : "";
  if (!state.status.configured) toast(t("not_configured"));
}

async function refreshSaved() {
  const result = await api("/api/saved?limit=500");
  state.savedBooks = result.books || [];
  renderSaved();
}

async function refreshDownloads() {
  const records = await api("/api/downloads?limit=100");
  const owned = new Map();
  records.forEach((record) => {
    if (["done", "running", "queued", "paused"].includes(record.status)) {
      owned.set(`${record.zlib_id}:${record.hash}`, record.status);
    }
  });
  state.owned = owned;
  renderDownloads(records);
  // The wishlist shows a badge for books already fetched, so it has to be
  // re-drawn once we know which ones those are.
  renderSaved();
}

async function refreshLibrary() {
  const result = await api("/api/library");
  $("libraryDir").textContent = result.dir || "";
  renderLibrary(result.files || []);
}

async function syncSaved() {
  const button = $("btnSync");
  button.disabled = true;
  const original = button.textContent;
  button.textContent = t("syncing");
  try {
    const result = await api("/api/sync/saved", { method: "POST" });
    await refreshSaved();
    toast(t("synced").replace("{n}", result.synced));
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

async function runSearch(page = 1) {
  const query = $("query").value.trim();
  if (!query) { $("query").focus(); return; }
  state.searchQuery = query;
  state.searchPage = page;
  const button = $("btnSearch");
  button.disabled = true;
  const original = button.textContent;
  button.textContent = t("searching");
  try {
    const result = await api("/api/search", {
      method: "POST",
      body: {
        query,
        page,
        limit: 20,
        languages: $("lang").value ? [$("lang").value] : null,
        extensions: $("format").value ? [$("format").value] : null,
      },
    });
    state.searchResult = result;
    renderSearch(result);
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

async function queueDownload(button) {
  const payload = {
    id: Number(button.dataset.download),
    hash: button.dataset.hash,
    title: button.dataset.title,
    author: button.dataset.author,
    extension: button.dataset.ext,
  };
  button.disabled = true;
  try {
    await api("/api/download", { method: "POST", body: payload });
    toast(t("downloaded"));
    await refreshDownloads();
  } catch (error) {
    toast(error.message);
    button.disabled = false;
  }
}

/* -------------------------------------------------------------------- wiring */

document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((node) => node.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((node) => node.classList.remove("active"));
    tab.classList.add("active");
    $(`panel-${tab.dataset.tab}`).classList.add("active");
    if (tab.dataset.tab === "downloads") { refreshDownloads(); refreshStatus(); }
    if (tab.dataset.tab === "library") refreshLibrary();
  };
});

document.addEventListener("click", (event) => {
  const downloadButton = event.target.closest("[data-download]");
  if (downloadButton) { queueDownload(downloadButton); return; }
  const retryButton = event.target.closest("[data-retry]");
  if (retryButton) {
    api(`/api/downloads/${retryButton.dataset.retry}/retry`, { method: "POST" })
      .then(refreshDownloads)
      .catch((error) => toast(error.message));
  }
});

$("btnRefresh").onclick = () => { refreshStatus(); if ($("panel-saved").classList.contains("active")) refreshSaved(); };
$("btnLang").onclick = () => {
  state.lang = state.lang === "zh" ? "en" : "zh";
  localStorage.setItem("zl-lang", state.lang);
  applyLanguage();
  renderQuota();
};
$("btnSync").onclick = syncSaved;
$("btnSearch").onclick = () => runSearch(1);
$("query").addEventListener("keydown", (event) => { if (event.key === "Enter") runSearch(1); });
$("savedFilter").addEventListener("input", renderSaved);

$("btnResume").onclick = async () => {
  try { await api("/api/queue/resume", { method: "POST" }); await refreshStatus(); await refreshDownloads(); }
  catch (error) { toast(error.message); }
};

$("btnPause").onclick = async () => {
  try { await api("/api/queue/pause", { method: "POST" }); await refreshStatus(); }
  catch (error) { toast(error.message); }
};

$("btnLogin").onclick = async () => {
  const notice = $("loginNotice");
  notice.textContent = "";
  const body = { domain: $("domain").value.trim() };
  const cookieUid = $("cookieUid").value.trim();
  const cookieKey = $("cookieKey").value.trim();
  if (cookieUid && cookieKey) {
    body.cookies = { remix_userid: cookieUid, remix_userkey: cookieKey };
  } else {
    body.email = $("email").value.trim();
    body.password = $("password").value;
  }
  try {
    await api("/api/login", { method: "POST", body });
    $("password").value = "";
    toast(t("login_ok"));
    await refreshStatus();
    await refreshSaved();
  } catch (error) {
    notice.textContent = error.message;
  }
};

$("btnLogout").onclick = async () => {
  if (!confirm(t("confirm_logout"))) return;
  try { await api("/api/logout", { method: "POST" }); await refreshStatus(); }
  catch (error) { toast(error.message); }
};

/* --------------------------------------------------------------------- boot */

(async function boot() {
  applyLanguage();
  await refreshStatus();
  try { await refreshSaved(); } catch (error) { /* not configured yet */ }
  try { await refreshDownloads(); } catch (error) { /* ignore */ }
  // Keep the quota and the queue live without a manual refresh.
  state.pollTimer = setInterval(() => {
    refreshStatus();
    if ($("panel-downloads").classList.contains("active")) refreshDownloads();
  }, 8000);
})();
