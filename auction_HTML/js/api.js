// Shared helpers. When FastAPI serves this folder (/app), the API is on the same origin.
const API_BASE = "";

const getToken = () => localStorage.getItem("token");
const setToken = (t) => localStorage.setItem("token", t);
const clearToken = () => localStorage.removeItem("token");

// number of bids on a product
const bidCount = (p) => p.the_number_of_auction ?? p.bid_count ?? 0;

async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  let payload;
  if (form) {
    payload = new URLSearchParams(form);            // /auth/login expects a form, not JSON
  } else if (body) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(API_BASE + path, { method, headers, body: payload });
  let data = null;
  try { data = await res.json(); } catch (e) { /* empty body */ }

  if (!res.ok) {
    if (res.status === 401 && token) clearToken();   // expired or invalid token
    const d = data && data.detail;
    throw new Error(Array.isArray(d) ? d.map((x) => x.msg).join(", ") : d || "Request failed");
  }
  return data;
}

// Needs GET /user/me on the backend. Returns null for guests.
async function currentUser() {
  if (!getToken()) return null;
  try { return await api("/user/me"); } catch (e) { return null; }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function flash(text, isError) {
  const el = document.getElementById("msg");
  if (!el) return;
  el.textContent = text;
  el.className = "msg " + (isError ? "error" : "ok");
  el.hidden = false;
}

function renderNav(user) {
  const nav = document.getElementById("nav");
  if (!nav) return;
  if (user) {
    const mine = user.role === "owner" || user.role === "admin"
      ? `<a href="my-products.html">My products</a>`
      : `<a href="my-bids.html">My bids</a>`;
    nav.innerHTML = `${mine}
      <span class="notif-wrap">
        <span id="bell">🔔 <b id="bell-count" hidden>0</b></span>
        <div id="notif-list" hidden></div>
      </span>
      <span class="who">${esc(user.name)} · ${esc(user.role)}</span><a href="#" id="logout">Logout</a>`;
    document.getElementById("logout").onclick = (e) => {
      e.preventDefault();
      clearToken();
      location.href = "index.html";
    };
    document.getElementById("bell").onclick = () => {
      const box = document.getElementById("notif-list");
      box.hidden = !box.hidden;
    };
    loadNotifications();
    setInterval(loadNotifications, 30000);
  } else {
    nav.innerHTML = `<a href="login.html">Login</a><a href="register.html" class="btn">Register</a>`;
  }
}

async function loadNotifications() {
  let list;
  try { list = await api("/notifications/me"); } catch (e) { return; }
  const unread = list.filter((n) => !n.is_read).length;
  const count = document.getElementById("bell-count");
  count.textContent = unread;
  count.hidden = unread === 0;
  const box = document.getElementById("notif-list");
  box.innerHTML = list.length
    ? list.map((n) => `<div class="notif${n.is_read ? "" : " unread"}" data-id="${n.id}">${esc(n.message)}</div>`).join("")
    : `<div class="notif">No notifications</div>`;
  box.querySelectorAll(".notif[data-id]").forEach((el) => {
    el.onclick = async () => {
      await api("/notifications/" + el.dataset.id + "/read", { method: "POST" });
      loadNotifications();
    };
  });
}