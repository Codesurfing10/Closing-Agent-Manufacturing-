/* ── Config ──────────────────────────────────────────────────── */
// UPDATE this to your Render service URL after deployment
const API_BASE = (window.API_BASE || "https://closing-agent-pet.onrender.com").replace(/\/$/, "");

/* ── Utility helpers ─────────────────────────────────────────── */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function post(path, body) {
  return api(path, { method: "POST", body: JSON.stringify(body) });
}
function put(path, body) {
  return api(path, { method: "PUT", body: JSON.stringify(body) });
}
function del(path) {
  return api(path, { method: "DELETE" });
}

function showToast(msg, type = "success") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = `toast ${type}`;
  setTimeout(() => (t.className = "toast hidden"), 3500);
}

function fmt(val) {
  if (val == null) return "–";
  return val;
}

function fmtDate(iso) {
  if (!iso) return "–";
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function fmtUSD(n) {
  if (n == null || isNaN(n)) return "–";
  return "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

/* ── Modal helpers ───────────────────────────────────────────── */
function openModal(html) {
  $("#modal-content").innerHTML = html;
  $("#modal-overlay").classList.remove("hidden");
  feather.replace();
}
function closeModal() {
  $("#modal-overlay").classList.add("hidden");
  $("#modal-content").innerHTML = "";
}
$("#modal-close-btn").addEventListener("click", closeModal);
$("#modal-overlay").addEventListener("click", (e) => { if (e.target === $("#modal-overlay")) closeModal(); });

/* ── Stage pill helper ───────────────────────────────────────── */
function stagePill(stage) {
  const cls = "stage-" + (stage || "").replace(/\s+/g, "-");
  return `<span class="stage-pill ${cls}">${stage || "–"}</span>`;
}
function statusPill(status) {
  const cls = "status-" + (status || "").replace(/\s+/g, "-");
  return `<span class="status-pill ${cls}">${status || "–"}</span>`;
}

/* ── Navigation ──────────────────────────────────────────────── */
let _currentView = "dashboard";

function navigate(view) {
  $$(".view").forEach((v) => v.classList.remove("active"));
  $$(".nav-item").forEach((a) => a.classList.remove("active"));
  const el = $(`#view-${view}`);
  if (el) el.classList.add("active");
  const nav = $(`.nav-item[data-view="${view}"]`);
  if (nav) nav.classList.add("active");
  _currentView = view;
  loadView(view);
}

$$(".nav-item").forEach((a) => {
  a.addEventListener("click", (e) => {
    e.preventDefault();
    navigate(a.dataset.view);
  });
});

/* ── API health check ────────────────────────────────────────── */
async function checkHealth() {
  const el = $("#api-status");
  try {
    await api("/health");
    el.className = "api-status online";
    el.innerHTML = '<span class="status-dot"></span> Connected';
  } catch {
    el.className = "api-status offline";
    el.innerHTML = '<span class="status-dot"></span> Offline';
  }
}

/* ── View loaders ────────────────────────────────────────────── */
async function loadView(view) {
  switch (view) {
    case "dashboard": return loadDashboard();
    case "contacts": return loadContacts();
    case "emails": return loadEmails();
    case "meetings": return loadMeetings();
    case "orders": return loadOrders();
    case "feedback": return loadFeedback();
    case "leads": return loadLeads();
    case "agent": return loadAgent();
  }
}

/* ── Dashboard ───────────────────────────────────────────────── */
async function loadDashboard() {
  try {
    const data = await api("/funnel");
    const s = data.stats;
    $("#stat-contacts").textContent = s.contacts ?? 0;
    $("#stat-emails").textContent = s.emails_sent ?? 0;
    $("#stat-meetings").textContent = s.meetings ?? 0;
    $("#stat-pipeline").textContent = fmtUSD(s.pipeline_usd);
    if ($("#stat-new-leads")) $("#stat-new-leads").textContent = s.new_leads ?? 0;

    const funnel = data.funnel;
    const max = Math.max(...funnel.map((f) => f.count), 1);
    const colors = ["#58a6ff", "#388bfd", "#2ea043", "#e3b341", "#3fb950", "#f85149"];
    const html = funnel
      .map((f, i) => {
        const pct = Math.max((f.count / max) * 100, f.count ? 4 : 0);
        return `
          <div class="funnel-stage">
            <span class="funnel-label">${f.stage}</span>
            <div class="funnel-bar-wrap">
              <div class="funnel-bar" style="width:${pct}%;background:${colors[i]}"></div>
            </div>
            <span class="funnel-count">${f.count}</span>
          </div>`;
      })
      .join("");
    $("#funnel-chart").innerHTML = html;
  } catch (e) {
    showToast("Could not load dashboard: " + e.message, "error");
  }
}

/* ── Contacts ─────────────────────────────────────────────────── */
let _contacts = [];

async function loadContacts() {
  try {
    const company = $("#filter-company").value;
    const stage = $("#filter-stage").value;
    const params = new URLSearchParams();
    if (company) params.set("company", company);
    if (stage) params.set("stage", stage);
    _contacts = await api("/contacts?" + params.toString());
    renderContactsTable(_contacts);
  } catch (e) {
    showToast("Could not load contacts: " + e.message, "error");
  }
}

function renderContactsTable(contacts) {
  const tbody = $("#contacts-tbody");
  if (!contacts.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:32px">No contacts found</td></tr>';
    return;
  }
  tbody.innerHTML = contacts
    .map(
      (c) => `
      <tr>
        <td><strong>${c.name}</strong></td>
        <td style="color:var(--text-muted)">${c.title || "–"}</td>
        <td>${c.company}</td>
        <td><a href="mailto:${c.email}" style="color:var(--accent2)">${c.email || "–"}</a></td>
        <td>${stagePill(c.stage)}</td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn btn-sm btn-secondary" onclick="openContactActions('${c.id}')">Actions</button>
            <button class="btn btn-sm btn-icon" onclick="deleteContact('${c.id}')" title="Delete"><i data-feather="trash-2"></i></button>
          </div>
        </td>
      </tr>`
    )
    .join("");
  feather.replace();
}

function openContactActions(id) {
  const c = _contacts.find((x) => x.id === id);
  if (!c) return;
  const stages = ["Identified","Contacted","Meeting Scheduled","Proposal Sent","Closed Won","Closed Lost"];
  const stageOpts = stages.map((s) => `<option${s === c.stage ? " selected" : ""}>${s}</option>`).join("");
  openModal(`
    <h2>${c.name}</h2>
    <p style="color:var(--text-muted);margin-bottom:16px">${c.title || ""} · ${c.company}</p>
    <div class="form-group">
      <label class="form-label">Funnel Stage</label>
      <select id="action-stage" class="form-select">${stageOpts}</select>
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveContactStage('${c.id}')">Save Stage</button>
      <button class="btn btn-secondary" onclick="closeModal();openGenerateEmail('${c.id}')">
        <i data-feather="mail"></i> Generate Email
      </button>
      <button class="btn btn-secondary" onclick="closeModal();openScheduleMeeting('${c.id}')">
        <i data-feather="calendar"></i> Schedule Meeting
      </button>
    </div>
  `);
}

async function saveContactStage(id) {
  const stage = $("#action-stage").value;
  try {
    await put(`/contacts/${id}/stage`, { stage });
    closeModal();
    showToast("Stage updated");
    loadContacts();
    if (_currentView === "dashboard") loadDashboard();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

async function deleteContact(id) {
  if (!confirm("Delete this contact?")) return;
  try {
    await del(`/contacts/${id}`);
    showToast("Contact deleted");
    loadContacts();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

// Add contact modal
$("#btn-add-contact").addEventListener("click", () => {
  openModal(`
    <h2>Add Contact</h2>
    <div class="form-group"><label class="form-label">Name *</label><input id="nc-name" class="form-input" placeholder="Full name" /></div>
    <div class="form-group"><label class="form-label">Title</label><input id="nc-title" class="form-input" placeholder="Job title" /></div>
    <div class="form-group"><label class="form-label">Company *</label><input id="nc-company" class="form-input" placeholder="Company name" /></div>
    <div class="form-group"><label class="form-label">Email</label><input id="nc-email" class="form-input" type="email" placeholder="email@company.com" /></div>
    <div class="form-group"><label class="form-label">Phone</label><input id="nc-phone" class="form-input" placeholder="+1-000-000-0000" /></div>
    <div class="form-group"><label class="form-label">LinkedIn URL</label><input id="nc-linkedin" class="form-input" placeholder="linkedin.com/in/..." /></div>
    <div class="form-group"><label class="form-label">Notes</label><textarea id="nc-notes" class="form-textarea"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="submitAddContact()">Add Contact</button>
    </div>
  `);
});

async function submitAddContact() {
  const name = $("#nc-name").value.trim();
  const company = $("#nc-company").value.trim();
  if (!name || !company) return showToast("Name and Company are required", "error");
  try {
    await post("/contacts", {
      name,
      title: $("#nc-title").value.trim(),
      company,
      email: $("#nc-email").value.trim(),
      phone: $("#nc-phone").value.trim(),
      linkedin: $("#nc-linkedin").value.trim(),
      notes: $("#nc-notes").value.trim(),
    });
    closeModal();
    showToast("Contact added");
    loadContacts();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

// Filters
$("#filter-company").addEventListener("change", loadContacts);
$("#filter-stage").addEventListener("change", loadContacts);

/* ── Emails ───────────────────────────────────────────────────── */
async function loadEmails() {
  try {
    const emails = await api("/emails");
    const el = $("#emails-list");
    if (!emails.length) {
      el.innerHTML = '<p style="color:var(--text-muted)">No emails yet. Generate one from a contact!</p>';
      return;
    }
    el.innerHTML = emails
      .map(
        (e) => `
        <div class="list-card">
          <div class="list-card-header">
            <div>
              <div class="list-card-title">${e.subject}</div>
              <div class="list-card-meta">To: ${e.contact_name} (${e.company}) · ${fmtDate(e.created_at)}</div>
            </div>
            ${statusPill(e.status)}
          </div>
          <div class="list-card-body">${e.body}</div>
          <div class="list-card-actions">
            ${e.status === "Draft" ? `<button class="btn btn-sm btn-primary" onclick="sendEmail('${e.id}')"><i data-feather="send"></i> Mark Sent</button>` : ""}
          </div>
        </div>`
      )
      .join("");
    feather.replace();
  } catch (e) {
    showToast("Could not load emails: " + e.message, "error");
  }
}

function openGenerateEmail(contactId) {
  navigate("contacts");
  // open generate email modal
  _openGenerateEmailModal(contactId);
}

async function _openGenerateEmailModal(preselected) {
  const contacts = _contacts.length ? _contacts : await api("/contacts");
  if (!contacts.length) return showToast("No contacts found", "error");
  const opts = contacts.map((c) => `<option value="${c.id}"${c.id === preselected ? " selected" : ""}>${c.name} – ${c.company}</option>`).join("");
  openModal(`
    <h2>Generate Outreach Email</h2>
    <div class="form-group"><label class="form-label">Contact *</label><select id="ge-contact" class="form-select">${opts}</select></div>
    <div class="form-group"><label class="form-label">Extra context (optional)</label><textarea id="ge-context" class="form-textarea" placeholder="e.g. focus on recycled PET savings, mention Q3 promotion…"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" id="btn-ge-submit" onclick="submitGenerateEmail()"><i data-feather="zap"></i> Generate</button>
    </div>
  `);
}

async function submitGenerateEmail() {
  const contactId = $("#ge-contact").value;
  const context = $("#ge-context").value.trim();
  const btn = $("#btn-ge-submit");
  btn.disabled = true;
  btn.innerHTML = '<span class="loader"></span> Generating…';
  try {
    await post("/emails/generate", { contact_id: contactId, context });
    closeModal();
    showToast("Email generated");
    navigate("emails");
  } catch (e) {
    showToast("Error: " + e.message, "error");
    btn.disabled = false;
    btn.innerHTML = '<i data-feather="zap"></i> Generate';
    feather.replace();
  }
}

async function sendEmail(id) {
  try {
    await post(`/emails/${id}/send`, {});
    showToast("Email marked as sent");
    loadEmails();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

$("#btn-generate-email").addEventListener("click", () => _openGenerateEmailModal(null));

/* ── Meetings ─────────────────────────────────────────────────── */
async function loadMeetings() {
  try {
    const meetings = await api("/meetings");
    const el = $("#meetings-list");
    if (!meetings.length) {
      el.innerHTML = '<p style="color:var(--text-muted)">No meetings scheduled yet.</p>';
      return;
    }
    el.innerHTML = meetings
      .map(
        (m) => `
        <div class="list-card">
          <div class="list-card-header">
            <div>
              <div class="list-card-title">${m.title}</div>
              <div class="list-card-meta">${m.contact_name} (${m.company}) · ${fmtDate(m.scheduled_at)} · ${m.duration_mins} min · ${m.location}</div>
            </div>
            ${statusPill(m.status)}
          </div>
          <div class="list-card-body" style="white-space:pre-wrap">${m.agenda || ""}</div>
          <div class="list-card-actions">
            <button class="btn btn-sm btn-secondary" onclick="completeMeeting('${m.id}')">Mark Completed</button>
          </div>
        </div>`
      )
      .join("");
    feather.replace();
  } catch (e) {
    showToast("Could not load meetings: " + e.message, "error");
  }
}

async function completeMeeting(id) {
  try {
    await put(`/meetings/${id}`, { notes: "Completed", status: "Completed" });
    showToast("Meeting marked as completed");
    loadMeetings();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

function openScheduleMeeting(contactId) {
  _openScheduleMeetingModal(contactId);
}

async function _openScheduleMeetingModal(preselected) {
  const contacts = _contacts.length ? _contacts : await api("/contacts");
  if (!contacts.length) return showToast("No contacts found", "error");
  const opts = contacts.map((c) => `<option value="${c.id}"${c.id === preselected ? " selected" : ""}>${c.name} – ${c.company}</option>`).join("");
  const defaultDt = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16);
  openModal(`
    <h2>Schedule Meeting</h2>
    <div class="form-group"><label class="form-label">Contact *</label><select id="sm-contact" class="form-select">${opts}</select></div>
    <div class="form-group"><label class="form-label">Meeting Title *</label><input id="sm-title" class="form-input" value="Discovery Call" /></div>
    <div class="form-group"><label class="form-label">Date & Time *</label><input id="sm-dt" class="form-input" type="datetime-local" value="${defaultDt}" /></div>
    <div class="form-group"><label class="form-label">Duration (mins)</label><input id="sm-dur" class="form-input" type="number" value="30" /></div>
    <div class="form-group"><label class="form-label">Location</label><input id="sm-loc" class="form-input" value="Video Call (Zoom)" /></div>
    <div class="form-group"><label class="form-label">Context / Agenda hints</label><textarea id="sm-context" class="form-textarea" placeholder="Focus areas, questions to ask…"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" id="btn-sm-submit" onclick="submitScheduleMeeting()"><i data-feather="calendar"></i> Schedule</button>
    </div>
  `);
}

async function submitScheduleMeeting() {
  const btn = $("#btn-sm-submit");
  btn.disabled = true;
  btn.innerHTML = '<span class="loader"></span> Scheduling…';
  try {
    await post("/meetings", {
      contact_id: $("#sm-contact").value,
      title: $("#sm-title").value.trim(),
      scheduled_at: new Date($("#sm-dt").value).toISOString(),
      duration_mins: parseInt($("#sm-dur").value) || 30,
      location: $("#sm-loc").value.trim(),
      context: $("#sm-context").value.trim(),
    });
    closeModal();
    showToast("Meeting scheduled");
    navigate("meetings");
  } catch (e) {
    showToast("Error: " + e.message, "error");
    btn.disabled = false;
    btn.innerHTML = '<i data-feather="calendar"></i> Schedule';
    feather.replace();
  }
}

$("#btn-schedule-meeting").addEventListener("click", () => _openScheduleMeetingModal(null));

/* ── Orders ───────────────────────────────────────────────────── */
async function loadOrders() {
  try {
    const orders = await api("/orders");
    const el = $("#orders-list");
    if (!orders.length) {
      el.innerHTML = '<p style="color:var(--text-muted)">No orders yet.</p>';
      return;
    }
    el.innerHTML = orders
      .map(
        (o) => `
        <div class="list-card">
          <div class="list-card-header">
            <div>
              <div class="list-card-title">${o.product}</div>
              <div class="list-card-meta">${o.contact_name} (${o.company}) · ${o.quantity_tons} tons · ${fmtUSD(o.unit_price_usd)}/ton · Total: ${fmtUSD(o.quantity_tons * o.unit_price_usd)}</div>
            </div>
            ${statusPill(o.status)}
          </div>
          ${o.notes ? `<div class="list-card-body">${o.notes}</div>` : ""}
          <div class="list-card-actions">
            <select class="form-select" style="width:180px" onchange="updateOrderStatus('${o.id}',this.value)">
              ${["Pending","Confirmed","In Production","Shipped","Delivered","Cancelled"].map((s) => `<option${s === o.status ? " selected" : ""}>${s}</option>`).join("")}
            </select>
          </div>
        </div>`
      )
      .join("");
    feather.replace();
  } catch (e) {
    showToast("Could not load orders: " + e.message, "error");
  }
}

async function updateOrderStatus(id, status) {
  try {
    await put(`/orders/${id}/status`, { status });
    showToast("Order updated");
    loadOrders();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

$("#btn-create-order").addEventListener("click", async () => {
  const contacts = _contacts.length ? _contacts : await api("/contacts");
  if (!contacts.length) return showToast("No contacts found", "error");
  const opts = contacts.map((c) => `<option value="${c.id}">${c.name} – ${c.company}</option>`).join("");
  openModal(`
    <h2>Create Order</h2>
    <div class="form-group"><label class="form-label">Contact *</label><select id="co-contact" class="form-select">${opts}</select></div>
    <div class="form-group"><label class="form-label">Product *</label><input id="co-product" class="form-input" placeholder="e.g. Virgin PET Resin – Grade A" /></div>
    <div class="form-group"><label class="form-label">Quantity (tons) *</label><input id="co-qty" class="form-input" type="number" step="0.1" placeholder="50" /></div>
    <div class="form-group"><label class="form-label">Unit Price (USD/ton) *</label><input id="co-price" class="form-input" type="number" step="0.01" placeholder="1250" /></div>
    <div class="form-group"><label class="form-label">Notes</label><textarea id="co-notes" class="form-textarea"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="submitCreateOrder()"><i data-feather="package"></i> Create Order</button>
    </div>
  `);
});

async function submitCreateOrder() {
  const qty = parseFloat($("#co-qty").value);
  const price = parseFloat($("#co-price").value);
  const product = $("#co-product").value.trim();
  if (!product || isNaN(qty) || isNaN(price)) return showToast("Product, quantity and price are required", "error");
  try {
    const res = await post("/orders", {
      contact_id: $("#co-contact").value,
      product,
      quantity_tons: qty,
      unit_price_usd: price,
      notes: $("#co-notes").value.trim(),
    });
    closeModal();
    showToast(`Order created – Total: ${fmtUSD(res.total_usd)}`);
    navigate("orders");
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

/* ── Feedback ─────────────────────────────────────────────────── */
async function loadFeedback() {
  try {
    const items = await api("/feedback");
    const el = $("#feedback-list");
    if (!items.length) {
      el.innerHTML = '<p style="color:var(--text-muted)">No feedback logged yet.</p>';
      return;
    }
    el.innerHTML = items
      .map(
        (f) => `
        <div class="list-card">
          <div class="list-card-header">
            <div>
              <div class="list-card-title">${f.contact_name} · ${f.company}</div>
              <div class="list-card-meta">${fmtDate(f.created_at)}</div>
            </div>
            ${statusPill(f.sentiment)}
          </div>
          <div class="list-card-body"><strong>Feedback:</strong> ${f.message}</div>
          ${f.response ? `<div class="list-card-body" style="margin-top:8px;border-left:2px solid var(--accent2);padding-left:10px"><strong>AI Response:</strong> ${f.response}</div>` : ""}
        </div>`
      )
      .join("");
    feather.replace();
  } catch (e) {
    showToast("Could not load feedback: " + e.message, "error");
  }
}

$("#btn-add-feedback").addEventListener("click", async () => {
  const contacts = _contacts.length ? _contacts : await api("/contacts");
  if (!contacts.length) return showToast("No contacts found", "error");
  const opts = contacts.map((c) => `<option value="${c.id}">${c.name} – ${c.company}</option>`).join("");
  openModal(`
    <h2>Log Feedback</h2>
    <div class="form-group"><label class="form-label">Contact *</label><select id="fb-contact" class="form-select">${opts}</select></div>
    <div class="form-group"><label class="form-label">Feedback Message *</label><textarea id="fb-msg" class="form-textarea" placeholder="Enter the customer's feedback…"></textarea></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" id="btn-fb-submit" onclick="submitFeedback()"><i data-feather="message-circle"></i> Submit & Get AI Response</button>
    </div>
  `);
});

async function submitFeedback() {
  const msg = $("#fb-msg").value.trim();
  if (!msg) return showToast("Message is required", "error");
  const btn = $("#btn-fb-submit");
  btn.disabled = true;
  btn.innerHTML = '<span class="loader"></span> Processing…';
  try {
    await post("/feedback", { contact_id: $("#fb-contact").value, message: msg });
    closeModal();
    showToast("Feedback logged with AI response");
    navigate("feedback");
  } catch (e) {
    showToast("Error: " + e.message, "error");
    btn.disabled = false;
    btn.innerHTML = '<i data-feather="message-circle"></i> Submit & Get AI Response';
    feather.replace();
  }
}

/* ── Leads ────────────────────────────────────────────────────── */
let _leads = [];

async function loadLeads() {
  try {
    const status = $("#filter-lead-status").value;
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    _leads = await api("/leads?" + params.toString());
    renderLeadsTable(_leads);
  } catch (e) {
    showToast("Could not load leads: " + e.message, "error");
  }
}

function renderLeadsTable(leads) {
  const tbody = $("#leads-tbody");
  if (!leads.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:32px">No leads yet. Click "Generate Leads" to create some!</td></tr>';
    return;
  }
  tbody.innerHTML = leads
    .map(
      (l) => `
      <tr>
        <td><strong>${l.name}</strong></td>
        <td style="color:var(--text-muted)">${l.title || "–"}</td>
        <td>${l.company}</td>
        <td style="color:var(--text-muted);font-size:0.85em;max-width:220px">${l.rationale || "–"}</td>
        <td>${stagePill(l.status)}</td>
        <td>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            ${l.status !== "Converted" ? `<button class="btn btn-sm btn-primary" onclick="convertLead('${l.id}')"><i data-feather="user-plus"></i> Convert</button>` : ""}
            <button class="btn btn-sm btn-secondary" onclick="updateLeadStatus('${l.id}','Dismissed')" title="Dismiss"><i data-feather="x"></i></button>
            <button class="btn btn-sm btn-icon" onclick="deleteLead('${l.id}')" title="Delete"><i data-feather="trash-2"></i></button>
          </div>
        </td>
      </tr>`
    )
    .join("");
  feather.replace();
}

async function convertLead(id) {
  try {
    const res = await post(`/leads/${id}/convert`, {});
    showToast("Lead converted to contact!");
    loadLeads();
    if (_currentView === "dashboard") loadDashboard();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

async function updateLeadStatus(id, status) {
  try {
    await put(`/leads/${id}/status`, { status });
    showToast(`Lead marked as ${status}`);
    loadLeads();
    if (_currentView === "dashboard") loadDashboard();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

async function deleteLead(id) {
  if (!confirm("Delete this lead?")) return;
  try {
    await del(`/leads/${id}`);
    showToast("Lead deleted");
    loadLeads();
  } catch (e) {
    showToast("Error: " + e.message, "error");
  }
}

$("#btn-generate-leads").addEventListener("click", () => {
  openModal(`
    <h2>Generate AI Leads</h2>
    <p style="color:var(--text-muted);margin-bottom:16px">The AI will identify new PET-industry prospects and add them to your pipeline.</p>
    <div class="form-group">
      <label class="form-label">Number of leads to generate</label>
      <input id="gl-count" class="form-input" type="number" min="1" max="20" value="5" />
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" id="btn-gl-submit" onclick="submitGenerateLeads()"><i data-feather="zap"></i> Generate</button>
    </div>
  `);
});

async function submitGenerateLeads() {
  const count = parseInt($("#gl-count").value) || 5;
  const btn = $("#btn-gl-submit");
  btn.disabled = true;
  btn.innerHTML = '<span class="loader"></span> Generating…';
  try {
    const res = await post("/leads/generate", { count });
    closeModal();
    showToast(`Generated ${res.generated} new lead${res.generated !== 1 ? "s" : ""}!`);
    navigate("leads");
    if (_currentView === "dashboard") loadDashboard();
  } catch (e) {
    showToast("Error: " + e.message, "error");
    btn.disabled = false;
    btn.innerHTML = '<i data-feather="zap"></i> Generate';
    feather.replace();
  }
}

$("#filter-lead-status").addEventListener("change", loadLeads);

/* ── AI Agent chat ────────────────────────────────────────────── */
async function loadAgent() {
  // Populate contact dropdown
  try {
    const contacts = await api("/contacts");
    _contacts = contacts;
    const sel = $("#agent-contact-select");
    sel.innerHTML = '<option value="">No contact selected</option>' +
      contacts.map((c) => `<option value="${c.id}">${c.name} – ${c.company}</option>`).join("");
  } catch {}
}

function appendAgentMsg(text, role = "agent") {
  const el = document.createElement("div");
  el.className = `agent-msg ${role}`;
  el.textContent = text;
  const msgs = $("#agent-messages");
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

async function runAgent() {
  const input = $("#agent-input");
  const task = input.value.trim();
  if (!task) return;
  const contactId = $("#agent-contact-select").value;
  appendAgentMsg(task, "user");
  input.value = "";
  const loader = document.createElement("div");
  loader.className = "agent-msg agent";
  loader.innerHTML = '<span class="loader"></span>';
  $("#agent-messages").appendChild(loader);

  try {
    const res = await post("/agent/run", { task, contact_id: contactId || undefined });
    loader.remove();
    if (res.error) {
      appendAgentMsg("⚠️ " + res.error);
    } else if (res.action === "email_generated") {
      appendAgentMsg(`✉️ Email drafted!\n\nSubject: ${res.subject}\n\n${res.body}`);
    } else if (res.action === "meeting_agenda_generated") {
      appendAgentMsg(`📅 Meeting Agenda:\n\n${res.agenda}\n\n${res.suggestion || ""}`);
    } else if (res.action === "feedback_response_generated") {
      appendAgentMsg(`💬 Suggested Response:\n\n${res.response}`);
    } else if (res.response) {
      appendAgentMsg(res.response);
    } else {
      appendAgentMsg(JSON.stringify(res, null, 2));
    }
  } catch (e) {
    loader.remove();
    appendAgentMsg("❌ Error: " + e.message);
  }
}

$("#btn-agent-send").addEventListener("click", runAgent);
$("#agent-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runAgent(); });
$$(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    $("#agent-input").value = chip.dataset.prompt;
    $("#agent-input").focus();
  });
});

/* ── Init ─────────────────────────────────────────────────────── */
window.addEventListener("DOMContentLoaded", () => {
  feather.replace();
  checkHealth();
  setInterval(checkHealth, 30000);
  loadDashboard();
});

// Expose globals needed by inline onclick handlers
Object.assign(window, {
  saveContactStage,
  deleteContact,
  openContactActions,
  sendEmail,
  completeMeeting,
  submitGenerateEmail,
  submitScheduleMeeting,
  submitCreateOrder,
  submitFeedback,
  updateOrderStatus,
  closeModal,
  submitAddContact,
  openGenerateEmail,
  openScheduleMeeting,
  convertLead,
  updateLeadStatus,
  deleteLead,
  submitGenerateLeads,
});
