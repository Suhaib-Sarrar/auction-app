let editing = null;      // the product being edited, or null when adding
let products = [];
let importRows = [];
 
const pform = document.getElementById("pform");
const iform = document.getElementById("iform");
 
// end_time arrives as "2026-12-30 06:00 PM" (UTC)
function parseEnd(s) {
  const m = /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}) (AM|PM)/.exec(s || "");
  if (!m) return null;
  let h = parseInt(m[4], 10) % 12;
  if (m[6] === "PM") h += 12;
  return Date.UTC(+m[1], +m[2] - 1, +m[3], h, +m[5]);
}
 
const fmt = (ms) => (ms === null ? "-" : new Date(ms).toLocaleString());
 
// value for <input type="datetime-local"> (local time)
function toLocalInput(ms) {
  return new Date(ms - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
 
function row(p) {
  const canEdit = p.status === "draft" || p.status === "open";
  const canDelete = p.status !== "sold";
  return `<tr>
    <td>${esc(p.title)}<div class="muted">${esc(p.name)}</div></td>
    <td><span class="tag ${esc(p.status)}">${esc(p.status)}</span></td>
    <td>${esc(p.start_price)}</td>
    <td>${esc(p.current_price)}</td>
    <td>${bidCount(p)}</td>
    <td>${fmt(parseEnd(p.end_time))}</td>
    <td class="acts"><a class="btn small" href="product-bids.html?id=${p.id}">Bids</a>
      ${canEdit ? `<button class="secondary" data-edit="${p.id}">Edit</button>` : ""}
      ${canDelete ? `<button class="danger" data-del="${p.id}">Delete</button>` : ""}
    </td></tr>`;
}
 
async function load() {
  try {
    products = await api("/products/mine");
    document.getElementById("rows").innerHTML = products.length
      ? products.map(row).join("")
      : `<tr><td colspan="7" class="muted">No products yet.</td></tr>`;
  } catch (e) {
    flash(e.message, true);
  }
}
 
function resetForm() {
  pform.reset();
  editing = null;
  pform.elements["start_price"].disabled = false;
  document.getElementById("ptitle").textContent = "Add product";
  document.getElementById("save").textContent = "Add product";
  document.getElementById("cancel").hidden = true;
}
 
function startEdit(p) {
  editing = p;
  pform.elements["name"].value = p.name;
  pform.elements["title"].value = p.title;
  pform.elements["start_price"].value = p.start_price;
  pform.elements["start_price"].disabled = bidCount(p) > 0;   // locked once bids exist
  pform.elements["status"].value = p.status;
  const end = parseEnd(p.end_time);
  pform.elements["end_time"].value = end === null ? "" : toLocalInput(end);
  document.getElementById("ptitle").textContent = "Edit product";
  document.getElementById("save").textContent = "Save changes";
  document.getElementById("cancel").hidden = false;
  pform.scrollIntoView({ behavior: "smooth" });
}
 
pform.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(pform);
  const body = {
    name: fd.get("name").trim(),
    title: fd.get("title").trim(),
    status: fd.get("status"),
  };
  const end = fd.get("end_time");
  if (end) body.end_time = new Date(end).toISOString();          // local time -> UTC
  if (!editing || bidCount(editing) === 0) body.start_price = fd.get("start_price");
 
  try {
    if (editing) await api(`/products/${editing.id}`, { method: "PUT", body });
    else await api("/products/", { method: "POST", body });
    flash(editing ? "Product updated." : "Product added.", false);
    resetForm();
    load();
  } catch (err) {
    flash(err.message, true);
  }
});
 
document.getElementById("cancel").addEventListener("click", resetForm);
 
document.getElementById("rows").addEventListener("click", async (e) => {
  const edit = e.target.closest("[data-edit]");
  const del = e.target.closest("[data-del]");
  if (edit) {
    startEdit(products.find((p) => p.id === +edit.dataset.edit));
  } else if (del && confirm("Delete this product?")) {
    try {
      await api(`/products/${del.dataset.del}`, { method: "DELETE" });
      flash("Product deleted.", false);
      load();
    } catch (err) {
      flash(err.message, true);
    }
  }
});
 
iform.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const res = await fetch(API_BASE + "/products/import/preview", {
      method: "POST",
      headers: { Authorization: "Bearer " + getToken() },
      body: new FormData(iform),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Preview failed");

    importRows = data.rows;
    document.getElementById("import-preview-rows").innerHTML = importRows.map((row, i) => `<tr>
      <td><input type="checkbox" class="import-row-select" data-index="${i}" ${row.valid ? "checked" : "disabled"}></td>
      <td>${row.row}</td>
      <td>${esc(row.name)}</td>
      <td>${esc(row.title)}</td>
      <td>${esc(row.start_price)}</td>
      <td>${esc(row.status)}</td>
      <td class="${row.valid ? "" : "muted"}">${row.valid ? "Valid" : esc(row.error)}</td>
    </tr>`).join("");

    document.getElementById("import-select-all").checked = false;
    document.getElementById("import-preview").hidden = false;
    flash(`${data.valid} valid product(s), ${data.invalid} invalid.`, data.valid === 0);
  } catch (err) {
    flash(err.message, true);
  }
});

function resetImportPreview() {
  importRows = [];
  document.getElementById("import-preview").hidden = true;
  document.getElementById("import-preview-rows").innerHTML = "";
  iform.reset();
}

document.getElementById("import-select-all").addEventListener("change", (e) => {
  document.querySelectorAll(".import-row-select:not(:disabled)").forEach((box) => {
    box.checked = e.target.checked;
  });
});

document.getElementById("cancel-import").addEventListener("click", resetImportPreview);

document.getElementById("confirm-import").addEventListener("click", async () => {
  const selected = [...document.querySelectorAll(".import-row-select:checked")]
    .map((box) => importRows[+box.dataset.index]);
  if (!selected.length) {
    flash("Select at least one valid product.", true);
    return;
  }

  try {
    const data = await api("/products/import/confirm", { method: "POST", body: selected });
    let text = `Imported ${data.saved} product(s), ${data.failed} failed.`;
    if (data.errors.length) text += " " + data.errors.map((x) => `Row ${x.row}: ${x.error}`).join("; ");
    flash(text, data.saved === 0);
    resetImportPreview();
    load();
  } catch (err) {
    flash(err.message, true);
  }
});
 
(async () => {
  const user = await currentUser();
  renderNav(user);
  if (!user) { location.href = "login.html"; return; }
  if (user.role !== "owner" && user.role !== "admin") {
    flash("Only owners can manage products.", true);
    return;
  }
  document.getElementById("content").hidden = false;
  load();
})();