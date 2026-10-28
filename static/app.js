/* zlib-nas front-end: no framework, no build step. */

const I18N = {
  zh: {
    tab_history: "远端历史", history_refresh: "刷新远端历史", history_hint: "来自账号的远端下载记录，不代表文件已保存在这台 NAS；日期按远端原样显示。", history_total: "远端共 {n} 条", remote_downloaded: "远端下载日期",
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
    settings_about: "关于",
    local_auth_title: "本地账号", local_auth_hint: "本地账号，只存在这台 NAS 上；与本工具里的 Z-Library 账号是两回事。",
    local_auth_username: "本地用户名",
    local_auth_current: "当前密码", local_auth_new: "新密码（至少 8 位，留空则不改）",
    local_auth_submit: "保存修改", local_auth_logout: "退出登录",
    local_auth_saved: "已保存，其他设备需要重新登录。", local_auth_wrong: "当前密码不对",
    local_auth_short: "新密码至少 8 位", local_auth_logged_out: "已退出，请重新登录。",
    about_text: "由 Ricardo 与他的大肥鱼阿静一同开发。",
    empty: "这里还什么都没有",
    search_hint: "输入书名或作者，开始搜索",
    download: "下载", reload: "重试", prev: "上一页", next: "下一页",
    syncing: "同步中…", searching: "搜索中…",
    not_configured: "还没有配置账号，去「设置」登录",
    logged_in: "已登录", login_ok: "登录成功",
    owned: "已下载", in_queue: "队列中", quota: "今日额度",
    downloaded: "已加入队列", synced: "已同步 {n} 本",
    detail_title: "书籍详情", close: "关闭", detail_back: "返回",
    loading: "加载中…", detail_error: "详情加载失败", unavailable: "缺少书籍 hash，详情、收藏和下载不可用。",
    author: "作者", publisher: "出版社", year: "年份", language: "语言", format: "格式", pages: "页数",
    description: "简介", no_description: "暂无简介", save: "加入收藏", unsave: "取消收藏", saving: "保存中…",
    saved_ok: "已加入收藏", unsaved_ok: "已取消收藏", saved_refresh_error: "收藏已更新，但本地列表刷新失败，请重试刷新。",
    author_search: "搜索作者", author_results: "作者名称搜索结果", collapse: "收起", expand: "展开",
    similar: "相关推荐", similar_error: "相关推荐加载失败",
    author_error: "作者搜索失败", download_error: "下载操作失败", save_error: "收藏操作失败",
    confirm_logout: "确定退出并清除本地会话与本机收藏镜像？",
  },
  en: {
    tab_history: "Remote history", history_refresh: "Refresh remote history", history_hint: "Account download history does not mean the files are on this NAS. Dates are shown as returned by the service.", history_total: "{n} remote records", remote_downloaded: "Remote download date",
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
    settings_about: "About",
    local_auth_title: "Local account", local_auth_hint: "A local account stored only on this NAS — unrelated to the Z-Library account this tool uses.",
    local_auth_username: "Local username",
    local_auth_current: "Current password", local_auth_new: "New password (at least 8 characters, blank to keep)",
    local_auth_submit: "Save changes", local_auth_logout: "Sign out",
    local_auth_saved: "Saved — other devices must sign in again.", local_auth_wrong: "Current password is wrong",
    local_auth_short: "New password must be at least 8 characters", local_auth_logged_out: "Signed out. Please sign in again.",
    about_text: "Built by Ricardo and his 大肥鱼阿静.",
    empty: "Nothing here yet",
    search_hint: "Type a title or an author to start",
    download: "Download", reload: "Retry", prev: "Prev", next: "Next",
    syncing: "Syncing…", searching: "Searching…",
    not_configured: "Not configured yet — sign in under Settings",
    logged_in: "Signed in", login_ok: "Signed in",
    owned: "Owned", in_queue: "Queued", quota: "Today's quota",
    downloaded: "Queued", synced: "Synced {n} books",
    detail_title: "Book details", close: "Close", detail_back: "Back",
    loading: "Loading…", detail_error: "Unable to load details", unavailable: "Book hash is missing. Details, wishlist and download are unavailable.",
    author: "Author", publisher: "Publisher", year: "Year", language: "Language", format: "Format", pages: "Pages",
    description: "Description", no_description: "No description available", save: "Add to wishlist", unsave: "Remove from wishlist", saving: "Saving…",
    saved_ok: "Added to wishlist", unsaved_ok: "Removed from wishlist", saved_refresh_error: "Wishlist updated, but refreshing the local list failed. Please refresh again.",
    author_search: "Search author", author_results: "Author name search results", collapse: "Hide", expand: "Show",
    similar: "Recommendations", similar_error: "Could not load recommendations",
    author_error: "Author search failed", download_error: "Download failed", save_error: "Wishlist update failed",
    confirm_logout: "Sign out and clear the local session and wishlist mirror?",
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
  renderHistory();
  if ($("bookDialog").open) renderDetail();
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

function miniCard(book) {
  // Shelf layout for the in-dialog lists: cover on top, two columns, so a long
  // list of recommendations stays scannable on a phone.
  const raw = book.cover || "";
  const src = raw.startsWith("/api/") ? raw : /^https?:/i.test(raw) ? `/api/cover?u=${encodeURIComponent(raw)}` : "";
  const cover = src
    ? `<img class="mini-cover" loading="lazy" src="${esc(src)}" alt="">`
    : `<div class="mini-cover placeholder">${BOOK_ICON}</div>`;
  return `<button type="button" class="mini-book" data-detail="${esc(book.id)}" data-hash="${esc(book.hash)}" data-title="${esc(book.title)}">
    ${cover}<span class="mini-title">${esc(book.title)}</span><span class="mini-author">${esc(book.author || "")}</span></button>`;
}

function bookCard(book) {
  // The mirror sometimes reports a relative placeholder path instead of a URL;
  // asking the proxy for it would only produce a 400 on every render.
  // Remote-history rows instead come back pointing at our own proxy (the real
  // cover URL needs a server-side lookup), so those are used as-is.
  const raw = book.cover || "";
  const local = raw.startsWith("/api/");
  const remote = /^https?:/i.test(raw);
  const cover = local
    ? `<img class="cover" loading="lazy" src="${esc(raw)}" alt="">`
    : remote
      ? `<img class="cover" loading="lazy" src="/api/cover?u=${encodeURIComponent(raw)}" alt="">`
      : `<div class="cover placeholder">${BOOK_ICON}</div>`;
  const known = state.owned.get(`${book.id}:${book.hash}`) || state.owned.get(book.sha256);
  const owned = known === "done";
  const queued = !!known && !owned;
  const meta = [book.author, book.year, book.filesize_text || bytes(book.filesize)]
    .filter(Boolean).map(esc).join(" · ");

  return `
    <div class="card-book">
      <button type="button" class="book-cover-button" data-detail="${esc(book.id)}" data-hash="${esc(book.hash)}" data-title="${esc(book.title)}" aria-label="${esc(t("detail_title") + ': ' + book.title)}">${cover}</button>
      <div class="book-body">
        <button type="button" class="book-title book-title-button" data-detail="${esc(book.id)}" data-hash="${esc(book.hash)}" data-title="${esc(book.title)}" title="${esc(book.title)}">${esc(book.title)}</button>
        <div class="book-meta" title="${esc(book.author)}">${meta}</div>
        <div class="book-actions">
          <span class="badge">${esc(book.extension || "")}</span>
          ${owned ? `<span class="badge owned">${t("owned")}</span>` : ""}
          ${queued ? `<span class="badge queued">${t("in_queue")}</span>` : ""}
          <button class="btn small primary" data-download="${esc(book.id)}"
            data-hash="${esc(book.hash)}" data-title="${esc(book.title)}"
            data-author="${esc(book.author)}" data-ext="${esc(book.extension || "")}"
            ${known || !book.hash ? "disabled" : ""} title="${!book.hash ? esc(t("unavailable")) : ""}">${t("download")}</button>
        </div>
      </div>
    </div>`;
}

/* Mark fetched / queued books in place.
   Rebuilding the grid on every poll used to re-create every <img>, which made the
   browser fetch the whole shelf of covers again — the mirror and its CDN should
   not see that traffic just because a tab is open. */
function updateOwnedBadges() {
  document.querySelectorAll("[data-download]").forEach((button) => {
    const key = `${button.dataset.download}:${button.dataset.hash}`;
    const status = state.owned.get(key);
    const card = button.closest(".card-book");
    if (!card) return;
    const actions = button.parentNode;
    const done = status === "done";
    const queued = !!status && !done;

    let badge = card.querySelector(".badge.owned");
    if (done && !badge) {
      badge = document.createElement("span");
      badge.className = "badge owned";
      badge.textContent = t("owned");
      actions.insertBefore(badge, button);
    } else if (!done && badge) {
      badge.remove();
    }

    let pending = card.querySelector(".badge.queued");
    if (queued && !pending) {
      pending = document.createElement("span");
      pending.className = "badge queued";
      pending.textContent = t("in_queue");
      actions.insertBefore(pending, button);
    } else if (!queued && pending) {
      pending.remove();
    }

    button.disabled = !!status || !button.dataset.hash || downloadPending.has(key);
  });
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

async function refreshStatus(fresh = false) {
  try {
    state.status = await api(`/api/status${fresh ? "?fresh=1" : ""}`);
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
  updateOwnedBadges();
  updateDetailActions();
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

const downloadPending = new Set();
const savePending = new Set();
const detail = { view: null, stack: [], sequence: 0, controller: null, opener: null, origin: null };
const bookKey = (book) => `${book.id}:${book.hash}`;

async function queueDownload(button) {
  const payload = {
    id: Number(button.dataset.download), hash: button.dataset.hash,
    title: button.dataset.title, author: button.dataset.author, extension: button.dataset.ext,
  };
  const key = bookKey(payload);
  if (!payload.hash) { toast(t("unavailable")); return; }
  if (button.disabled || downloadPending.has(key)) return;
  downloadPending.add(key);
  button.disabled = true;
  updateDetailActions();
  try {
    await api("/api/download", { method: "POST", body: payload });
    state.owned.set(key, "queued");
    for (const view of [detail.view, ...detail.stack]) {
      if (view && bookKey(view.book) === key && view.data) view.data.in_queue = true;
    }
    toast(t("downloaded"));
    try { await refreshDownloads(); } catch (error) { toast(error.message); }
  } catch (error) {
    if (detail.view && bookKey(detail.view.book) === key) {
      detail.view.notice = `${t("download_error")}: ${error.message}`;
    }
    toast(error.message);
  } finally {
    downloadPending.delete(key);
    button.disabled = !!state.owned.get(key);
    updateOwnedBadges();
    updateDetailActions();
  }
}

function cancelDetailRequest() {
  detail.sequence += 1;
  if (detail.controller) detail.controller.abort();
  detail.controller = null;
}

function openDetail(book, opener) {
  const dialog = $("bookDialog");
  if (!dialog.open) {
    detail.opener = opener;
    detail.origin = { id: String(book.id), hash: book.hash || "", panel: opener.closest(".panel")?.id };
    detail.stack = [];
    dialog.showModal();
  } else if (detail.view) {
    detail.stack.push(detail.view);
  }
  cancelDetailRequest();
  detail.view = { book, data: null, loading: false, error: "", notice: "", authorResult: null, authorLoading: false, authorError: "" };
  loadDetail();
  $("detailClose").focus();
}

async function loadDetail() {
  cancelDetailRequest();
  const view = detail.view;
  if (!view) return;
  if (!view.book.hash) { renderDetail(); return; }
  const sequence = detail.sequence;
  const controller = detail.controller = new AbortController();
  view.loading = true;
  view.error = "";
  renderDetail();
  try {
    const data = await api(`/api/book/${encodeURIComponent(view.book.id)}?hash=${encodeURIComponent(view.book.hash)}`, { signal: controller.signal });
    if (sequence !== detail.sequence || !$("bookDialog").open) return;
    if (!data || !data.book) throw new Error(t("detail_error"));
    // Retain the exact ID/hash from the clicked card, never infer a missing hash.
    view.book = { ...data.book, id: view.book.id, hash: view.book.hash };
    view.data = data;
  } catch (error) {
    if (sequence !== detail.sequence) return;
    view.error = error.message;
  } finally {
    if (sequence === detail.sequence && $("bookDialog").open) {
      view.loading = false;
      renderDetail();
    }
  }
}

function renderDetail() {
  const view = detail.view;
  if (!view) return;
  const content = $("detailContent");
  $("detailBack").hidden = !detail.stack.length;
  content.setAttribute("aria-busy", String(view.loading));
  if (!view.book.hash) {
    content.innerHTML = `<p class="notice">${esc(t("unavailable"))}</p>`;
    return;
  }
  if (view.loading) { content.innerHTML = `<p class="empty">${t("loading")}</p>`; return; }
  if (view.error) {
    content.innerHTML = `<p role="alert">${t("detail_error")}: ${esc(view.error)}</p><button class="btn" id="detailRetry">${t("reload")}</button>`;
    $("detailRetry").onclick = loadDetail;
    return;
  }
  if (!view.data) return;
  const book = view.book;
  const meta = [["author", book.author], ["publisher", book.publisher], ["year", book.year],
    ["language", book.language], ["format", book.extension], ["col_size", book.filesize_text || bytes(book.filesize)],
    ["pages", book.pages], ["ISBN", book.isbn]].filter(([, value]) => value !== undefined && value !== null && value !== "");
  const cover = /^https?:/i.test(book.cover || "")
    ? `<img class="detail-cover" src="/api/cover?u=${encodeURIComponent(book.cover)}" alt="">`
    : `<div class="detail-cover placeholder">${BOOK_ICON}</div>`;
  content.innerHTML = `<div class="detail-summary">${cover}<div class="detail-info"><h3>${esc(book.title)}</h3>
    <dl class="detail-meta">${meta.map(([label, value]) => `<dt>${esc(t(label))}</dt><dd>${esc(value)}</dd>`).join("")}</dl></div></div>
    <div class="detail-actions"><button class="btn primary" id="detailDownload" data-download="${esc(book.id)}" data-hash="${esc(book.hash)}"
      data-title="${esc(book.title)}" data-author="${esc(book.author)}" data-ext="${esc(book.extension)}"></button>
      <button class="btn" id="detailSave"></button></div><p class="notice" id="detailNotice" role="status"></p>
    <h3>${t("description")}</h3><div class="detail-description" id="detailDescription"></div>
    <div class="detail-tools">${book.author ? `<button class="btn" id="detailAuthorSearch"></button>` : ""}
      <button class="btn" id="detailSimilar"></button></div>
    <div id="detailAuthorResults" hidden></div>
    <div id="detailSimilarResults" hidden></div>`;
  // This is the sole rich-text source: the detail API's server-whitelisted HTML.
  if (typeof book.description_html === "string" && book.description_html) {
    $("detailDescription").innerHTML = book.description_html;
  } else {
    $("detailDescription").textContent = t("no_description");
  }
  $("detailSave").onclick = toggleDetailSaved;
  if ($("detailAuthorSearch")) $("detailAuthorSearch").onclick = toggleAuthorResults;
  if ($("detailSimilar")) $("detailSimilar").onclick = toggleSimilarResults;
  updateDetailActions();
  renderAuthorResults();
  renderSimilar();
}

function updateDetailActions() {
  const view = detail.view;
  if (!$("bookDialog").open || !view?.data || !$("detailDownload")) return;
  const key = bookKey(view.book);
  const known = state.owned.get(key);
  const record = (state.lastDownloads || []).find((item) => `${item.zlib_id}:${item.hash}` === key);
  if (record) {
    view.data.downloaded = record.status === "done";
    view.data.in_queue = ["running", "queued", "paused"].includes(record.status);
  }
  const owned = known === "done" || view.data.downloaded;
  const queued = !!known || view.data.in_queue;
  const download = $("detailDownload");
  download.textContent = t(owned ? "owned" : queued ? "in_queue" : downloadPending.has(key) ? "loading" : "download");
  download.disabled = owned || queued || downloadPending.has(key);
  const save = $("detailSave");
  save.textContent = t(savePending.has(key) ? "saving" : view.data.saved ? "unsave" : "save");
  save.disabled = savePending.has(key);
  save.setAttribute("aria-pressed", String(!!view.data.saved));
  $("detailNotice").textContent = view.notice;
}

async function toggleDetailSaved() {
  const view = detail.view;
  if (!view?.data || !view.book.hash) return;
  const key = bookKey(view.book);
  if (savePending.has(key)) return;
  savePending.add(key);
  view.notice = "";
  updateDetailActions();
  try {
    const result = await api(`/api/book/${encodeURIComponent(view.book.id)}/saved`, {
      method: "POST", body: { hash: view.book.hash, saved: !view.data.saved },
    });
    if (!result.ok || typeof result.saved !== "boolean") throw new Error(t("save_error"));
    for (const item of [view, detail.view, ...detail.stack]) {
      if (item?.data && bookKey(item.book) === key) item.data.saved = result.saved;
    }
    view.notice = t(result.saved ? "saved_ok" : "unsaved_ok");
    try { await refreshSaved(); } catch (error) { view.notice = t("saved_refresh_error"); }
  } catch (error) {
    view.notice = `${t("save_error")}: ${error.message}`;
  } finally {
    savePending.delete(key);
    updateDetailActions();
  }
}

function toggleAuthorResults() {
  const view = detail.view;
  if (!view || view.authorLoading) return;
  // The button is both the entry point and the collapse control: first click
  // runs the search, later clicks fold the results away and back.
  if (view.authorResult || view.authorError) {
    view.authorOpen = !view.authorOpen;
    renderAuthorResults();
  } else {
    searchDetailAuthor(1);
  }
}

async function searchDetailAuthor(page) {
  const view = detail.view;
  if (!view?.book.author || view.authorLoading) return;
  const sequence = detail.sequence;
  view.authorLoading = true;
  view.authorOpen = true;
  view.authorError = "";
  renderAuthorResults();
  try {
    const result = await api("/api/search", { method: "POST", signal: detail.controller?.signal,
      body: { query: view.book.author, page, limit: 20, languages: null, extensions: null } });
    if (sequence !== detail.sequence || detail.view !== view) return;
    view.authorResult = result;
  } catch (error) {
    if (sequence === detail.sequence) view.authorError = error.message;
  } finally {
    view.authorLoading = false;
    if (sequence === detail.sequence && detail.view === view) renderAuthorResults();
  }
}

function renderAuthorResults() {
  const view = detail.view;
  const button = $("detailAuthorSearch");
  if (!view || !button) return;
  button.disabled = view.authorLoading;
  // The label always names the section, so two collapsed buttons stacked on top
  // of each other stay tellable apart.
  button.textContent = view.authorLoading ? t("searching")
    : view.authorError ? `${t("author_search")} · ${t("reload")}`
    : view.authorResult ? `${t("author_search")} · ${t(view.authorOpen ? "collapse" : "expand")}`
    : t("author_search");
  const result = view.authorResult;
  const target = $("detailAuthorResults");
  if (!target) return;
  const visible = view.authorOpen && (!!result || !!view.authorError);
  button.setAttribute("aria-expanded", String(visible));
  target.hidden = !visible;
  target.innerHTML = view.authorError ? `<p role="alert">${t("author_error")}: ${esc(view.authorError)}</p>` : "";
  if (!result) return;
  target.insertAdjacentHTML("beforeend", `<div class="book-shelf">${result.books?.length ? result.books.map(miniCard).join("") : `<p class="empty">${t("empty")}</p>`}</div>
    <div class="pager"><button class="btn" id="authorPrev">${t("prev")}</button><span>${esc(result.page || 1)} / ${esc(result.pages || 1)}</span><button class="btn" id="authorNext">${t("next")}</button></div>`);
  $("authorPrev").disabled = view.authorLoading || (result.page || 1) <= 1;
  $("authorNext").disabled = view.authorLoading || !result.has_next;
  $("authorPrev").onclick = () => searchDetailAuthor((result.page || 1) - 1);
  $("authorNext").onclick = () => searchDetailAuthor((result.page || 1) + 1);
}

function toggleSimilarResults() {
  const view = detail.view;
  if (!view || view.similarLoading) return;
  if (view.similar || view.similarError) {
    view.similarOpen = !view.similarOpen;
    renderSimilar();
  } else {
    loadSimilar();
  }
}

async function loadSimilar() {
  const view = detail.view;
  if (!view?.book.hash || view.similarLoading) return;
  const sequence = detail.sequence;
  view.similarLoading = true;
  view.similarOpen = true;
  view.similarError = "";
  renderSimilar();
  try {
    const result = await api(`/api/book/${encodeURIComponent(view.book.id)}/similar?hash=${encodeURIComponent(view.book.hash)}`,
      { signal: detail.controller?.signal });
    if (sequence !== detail.sequence || detail.view !== view) return;
    view.similar = result.books || [];
  } catch (error) {
    if (sequence === detail.sequence) view.similarError = error.message;
  } finally {
    view.similarLoading = false;
    if (sequence === detail.sequence && detail.view === view) renderSimilar();
  }
}

function renderSimilar() {
  const view = detail.view;
  const button = $("detailSimilar");
  if (!view || !button) return;
  button.disabled = view.similarLoading;
  button.textContent = view.similarLoading ? t("searching")
    : view.similarError ? `${t("similar")} · ${t("reload")}`
    : view.similar ? `${t("similar")} · ${t(view.similarOpen ? "collapse" : "expand")}`
    : t("similar");
  const target = $("detailSimilarResults");
  if (!target) return;
  const visible = view.similarOpen && (!!view.similar || !!view.similarError);
  button.setAttribute("aria-expanded", String(visible));
  target.hidden = !visible;
  target.innerHTML = view.similarError ? `<p role="alert">${t("similar_error")}: ${esc(view.similarError)}</p>` : "";
  if (!view.similar) return;
  target.insertAdjacentHTML("beforeend", view.similar.length
    ? `<div class="book-shelf">${view.similar.map(miniCard).join("")}</div>`
    : `<p class="empty">${t("empty")}</p>`);
}

let historyPage = 1, historyResult = null, historySequence = 0;
function renderHistory() {
  if (!historyResult) return;
  $("historyCount").textContent = t("history_total").replace("{n}", historyResult.total);
  $("historyGrid").innerHTML = historyResult.books.length ? historyResult.books.map(book =>
    `<div><div class="history-date">${t("remote_downloaded")}: ${esc(book.date_download || "—")}</div>${bookCard(book)}</div>`).join("") : `<p class="empty">${t("empty")}</p>`;
  $("historyPager").innerHTML = `<button class="btn" id="historyPrev" ${historyPage <= 1 ? "disabled" : ""}>${t("prev")}</button><span>${historyPage} / ${historyResult.pages}</span><button class="btn" id="historyNext" ${!historyResult.has_next ? "disabled" : ""}>${t("next")}</button>`;
  $("historyPrev").onclick = () => loadHistory(historyPage - 1);
  $("historyNext").onclick = () => loadHistory(historyPage + 1);
}
async function loadHistory(page = 1, fresh = false) {
  const sequence = ++historySequence;
  $("historyNotice").textContent = t("loading");
  $("historyRefresh").disabled = true;
  try {
    const result = await api(`/api/history?page=${page}${fresh ? "&fresh=1" : ""}`);
    if (sequence !== historySequence) return;
    historyPage = page; historyResult = result;
    result.books.forEach(book => {
      if (book.downloaded) state.owned.set(bookKey(book), "done");
      else if (book.in_queue) state.owned.set(bookKey(book), "queued");
    });
    renderHistory(); $("historyNotice").textContent = "";
  } catch (error) { if (sequence === historySequence) $("historyNotice").textContent = error.message; }
  finally { if (sequence === historySequence) $("historyRefresh").disabled = false; }
}
$("historyRefresh").onclick = () => loadHistory(historyPage, true);

/* -------------------------------------------------------------------- wiring */

document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((node) => node.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((node) => node.classList.remove("active"));
    tab.classList.add("active");
    $(`panel-${tab.dataset.tab}`).classList.add("active");
    if (tab.dataset.tab === "downloads") { refreshDownloads(); refreshStatus(); }
    if (tab.dataset.tab === "library") refreshLibrary();
    if (tab.dataset.tab === "history") loadHistory(historyPage);
    if (tab.dataset.tab === "settings") fillLocalAccount();
  };
});

document.addEventListener("click", (event) => {
  const detailButton = event.target.closest("[data-detail]");
  if (detailButton) {
    openDetail({ id: detailButton.dataset.detail, hash: detailButton.dataset.hash, title: detailButton.dataset.title }, detailButton);
    return;
  }
  const downloadButton = event.target.closest("[data-download]");
  if (downloadButton) { queueDownload(downloadButton); return; }
  const retryButton = event.target.closest("[data-retry]");
  if (retryButton) {
    api(`/api/downloads/${retryButton.dataset.retry}/retry`, { method: "POST" })
      .then(refreshDownloads)
      .catch((error) => toast(error.message));
  }
});

$("detailClose").onclick = () => $("bookDialog").close();
$("detailBack").onclick = () => {
  if (!detail.stack.length) return;
  cancelDetailRequest();
  detail.view = detail.stack.pop();
  detail.view.authorLoading = false;
  if (detail.view.loading || !detail.view.data) loadDetail();
  else renderDetail();
  $("detailClose").focus();
};
let backdropPressed = false;
function outsideDialog(event) {
  const rect = $("bookDialog").getBoundingClientRect();
  return event.target === $("bookDialog") && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom);
}
$("bookDialog").addEventListener("pointerdown", (event) => { backdropPressed = outsideDialog(event); });
$("bookDialog").addEventListener("click", (event) => {
  if (backdropPressed && outsideDialog(event)) $("bookDialog").close();
  backdropPressed = false;
});
$("bookDialog").addEventListener("close", () => {
  cancelDetailRequest();
  const origin = detail.origin;
  const replacement = [...document.querySelectorAll("[data-detail]")].find((node) =>
    !node.closest("dialog") && node.dataset.detail === origin?.id && node.dataset.hash === origin?.hash);
  const target = detail.opener?.isConnected ? detail.opener : replacement || document.querySelector(`.tab[data-tab="${origin?.panel?.replace("panel-", "") || "saved"}"]`);
  target?.focus();
  detail.view = null;
  detail.stack = [];
});

$("btnRefresh").onclick = () => {
  refreshStatus(true);  // the one place that bypasses the server-side cache
  if ($("panel-saved").classList.contains("active")) refreshSaved();
};
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

// ---------------------------------------------------------------- local auth
$("localPasswordForm").onsubmit = async (event) => {
  event.preventDefault();
  const notice = $("localAuthNotice");
  const current = $("localCurrent").value;
  // Blank means "keep the current password" so the username alone can be edited.
  const next = $("localNew").value || current;
  const username = $("localUsername").value.trim();
  notice.className = "notice";
  if (next.length < 8) {
    notice.textContent = t("local_auth_short");
    notice.classList.add("err");
    return;
  }
  try {
    const response = await fetch("/api/local/password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current, password: next, username }),
    });
    if (response.status === 401) {
      notice.textContent = t("local_auth_wrong");
      notice.classList.add("err");
      return;
    }
    if (!response.ok) throw new Error((await response.json()).detail || "failed");
    notice.textContent = t("local_auth_saved");
    notice.classList.add("ok");
    $("localCurrent").value = "";
    $("localNew").value = "";
  } catch (error) {
    notice.textContent = error.message;
    notice.classList.add("err");
  }
};

async function fillLocalAccount() {
  try {
    const status = await (await fetch("/api/local/status")).json();
    if (status.username) $("localUsername").value = status.username;
  } catch (_) {
    /* the field stays as-is; it is only a label */
  }
}

$("btnLocalLogout").onclick = async () => {
  try {
    await fetch("/api/local/logout", { method: "POST" });
  } catch (_) {
    /* fall through to the redirect: the cookie is dropped server-side anyway */
  }
  window.location.replace("/login");
};

$("btnLogout").onclick = async () => {
  if (!confirm(t("confirm_logout"))) return;
  try {
    await api("/api/logout", { method: "POST" });
    // The server drops its wishlist mirror on logout, so the page must not keep
    // showing the previous account's books either.
    state.savedBooks = [];
    renderSaved();
    if ($("bookDialog").open) $("bookDialog").close();
    await refreshStatus();
  } catch (error) { toast(error.message); }
};

/* --------------------------------------------------------------------- boot */

(async function boot() {
  applyLanguage();
  await refreshStatus();
  try { await refreshSaved(); } catch (error) { /* not configured yet */ }
  try { await refreshDownloads(); } catch (error) { /* ignore */ }
  // Keep the quota and the queue live without a manual refresh.
  state.pollTimer = setInterval(() => {
    // Nothing to poll in a background tab, and every poll costs a request to the
    // mirror once the server-side cache has expired.
    if (document.hidden) return;
    refreshStatus();
    if ($("panel-downloads").classList.contains("active") || $("bookDialog").open) refreshDownloads().catch(() => {});
  }, 30000);
})();
