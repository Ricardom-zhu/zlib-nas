/* Sign-in page logic. Deliberately its own file: the app shell (app.js) only
   runs once the session cookie exists, and this page must not depend on it. */

const $ = (id) => document.getElementById(id);

const state = { configured: false };

const submitBtn = $("authSubmit");

function setNotice(message, kind) {
  const notice = $("authNotice");
  notice.textContent = message || "";
  notice.className = "notice" + (kind ? " " + kind : "");
}

function applyMode(configured) {
  state.configured = configured;
  document.documentElement.dataset.mode = configured ? "login" : "register";
  if (configured) {
    $("authTitle").textContent = "登录";
    $("authHint").textContent = "输入访问密码以进入 zlib-nas。";
    $("pwLabel").textContent = "密码";
    // hide the label too, or the form still reads "再输一次" with nothing under it
    $("confirmLabel").style.display = "none";
    $("confirm").hidden = true;
    $("confirm").value = "";
    $("password").autocomplete = "current-password";
    submitBtn.textContent = "登录";
  } else {
    $("authTitle").textContent = "设置访问密码";
    $("authHint").textContent = "这台机器上还没有账号。请设置一个密码，之后进入本页都需要它。";
    $("pwLabel").textContent = "密码（至少 8 位）";
    $("confirmLabel").style.display = "";
    $("confirm").hidden = false;
    $("password").autocomplete = "new-password";
    submitBtn.textContent = "设置密码";
  }
}

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  let data = {};
  try {
    data = await response.json();
  } catch (_) {
    /* non-JSON (e.g. proxy error page) — fall through with empty data */
  }
  return { response, data };
}

$("authForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const password = $("password").value;
  if (!password) {
    setNotice("请输入密码", "err");
    return;
  }
  if (!state.configured) {
    if (password.length < 8) {
      setNotice("密码至少 8 位", "err");
      return;
    }
    if (password !== $("confirm").value) {
      setNotice("两次输入的密码不一致", "err");
      return;
    }
  }

  submitBtn.disabled = true;
  setNotice("", "");
  try {
    const path = state.configured ? "/api/local/login" : "/api/local/register";
    const { response, data } = await post(path, { password });
    if (response.ok) {
      setNotice("好了，正在进入…", "ok");
      window.location.replace("/");
      return;
    }
    if (response.status === 401) {
      setNotice("密码不对", "err");
    } else if (response.status === 409) {
      // Someone else set it up while this page was open — switch to login.
      applyMode(true);
      setNotice("账号已存在，请直接登录", "err");
    } else {
      setNotice((data && data.detail) || "操作失败，请重试", "err");
    }
  } catch (error) {
    setNotice("网络异常，请重试", "err");
  } finally {
    submitBtn.disabled = false;
  }
});

(async () => {
  try {
    const response = await fetch("/api/local/status", { headers: { Accept: "application/json" } });
    const status = await response.json();
    applyMode(Boolean(status.configured));
    if (status.authed) {
      window.location.replace("/");
      return;
    }
    if (state.configured) {
      $("password").autocomplete = "current-password";
    }
  } catch (_) {
    applyMode(false);
  }
  $("password").focus();
})();
