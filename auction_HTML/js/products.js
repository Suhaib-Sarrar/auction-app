let user = null;

// logged-in users skip the intro: hide it right away (no flash)
if (getToken()) document.querySelectorAll(".intro").forEach((el) => (el.hidden = true));

// end_time arrives as "2026-12-30 06:00 PM" (UTC)
function parseEnd(s) {
  const m = /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}) (AM|PM)/.exec(s || "");
  if (!m) return null;
  let h = parseInt(m[4], 10) % 12;
  if (m[6] === "PM") h += 12;
  return Date.UTC(+m[1], +m[2] - 1, +m[3], h, +m[5]);
}

function countdown(end) {
  if (end === null) return "";
  let s = Math.floor((end - Date.now()) / 1000);
  if (s <= 0) return "Ended";
  const d = Math.floor(s / 86400); s %= 86400;
  const h = Math.floor(s / 3600); s %= 3600;
  const m = Math.floor(s / 60);
  return (d ? d + "d " : "") + h + "h " + m + "m " + (s % 60) + "s left";
}

function card(p) {
  const n = bidCount(p);
  const min = n === 0 ? p.current_price : (parseFloat(p.current_price) + 1).toFixed(2);
  let action = "";
  if (!user) action = `<a href="login.html">Login to bid</a>`;
  else if (user.role === "customer")
    action = `<form class="bid" data-id="${p.id}">
      <input type="number" step="0.01" min="${min}" placeholder="${min}" required>
      <button>Bid</button></form>`;

  const end = parseEnd(p.end_time);
  return `<div class="card"><div class="thumb">${esc((p.title || "?")[0].toUpperCase())}</div>
    <div class="info">
      <h3>${esc(p.title)}</h3>
      <div class="muted">${esc(p.name)} · by ${esc(p.owner_name)}</div>
      <div class="muted">${n} bid${n === 1 ? "" : "s"}</div>
      <div class="muted timer" data-end="${end ?? ""}">${countdown(end)}</div>
    </div>
    <div class="side"><div class="price">${esc(p.current_price)}</div>${action}</div>
  </div>`;
}

async function load() {
  const grid = document.getElementById("grid");
  try {
    const list = await api("/products/");
    grid.innerHTML = list.length
      ? list.map(card).join("")
      : `<div class="empty"><img src="img/empty.svg" alt=""><p>No open auctions yet.</p></div>`;
  } catch (e) {
    flash(e.message, true);
  }
}

document.getElementById("grid").addEventListener("submit", async (e) => {
  const form = e.target.closest("form.bid");
  if (!form) return;
  e.preventDefault();
  try {
    await api(`/products/${form.dataset.id}/bids`, {
      method: "POST",
      body: { amount: form.querySelector("input").value },
    });
    flash("Bid placed!", false);
    load();
  } catch (err) {
    flash(err.message, true);
  }
});

setInterval(() => {
  document.querySelectorAll(".timer[data-end]").forEach((el) => {
    if (el.dataset.end) el.textContent = countdown(+el.dataset.end);
  });
}, 1000);

(async () => {
  user = await currentUser();
  renderNav(user);
  document.querySelectorAll(".intro").forEach((el) => (el.hidden = !!user));   // intro for guests only
  document.getElementById("grid").classList.toggle("list", !!user);            // stacked list when logged in
  load();
})();