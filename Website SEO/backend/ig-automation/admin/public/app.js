/*
 * The panel, as one file of plain JavaScript.
 *
 * No framework, because the service it configures has three dependencies and a
 * build step on the VPS would be a fourth thing to keep alive. The state is one
 * object, the server is the source of truth, and every save round-trips through
 * the same validator the webhook uses — so the panel cannot express a rule the
 * automation would refuse.
 *
 * The editing model is deliberate: edits are local until "Save & go live". A
 * form that wrote on every keystroke would mean a half-typed keyword is briefly
 * what the account replies to.
 */

const state = {
  account: {},
  limits: {},
  files: [],
  media: [],
  mediaError: null,
  config: { rules: [] },
  savedJson: "[]",
  etag: "",
  problems: [],
  open: new Set(),
  tab: "rules",
};

/* ---------- plumbing ---------- */

const $ = (sel) => document.querySelector(sel);
const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

let toastTimer;
function toast(message, bad) {
  const el = $("#toast");
  el.textContent = message;
  el.className = "show" + (bad ? " bad" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = ""), bad ? 5200 : 2600);
}

/**
 * Every call goes through here so a 401 has exactly one meaning everywhere:
 * the session ended, show the login card, keep the page as it is. A redirect
 * would throw away unsaved edits, which is the worst possible response to a
 * cookie quietly expiring.
 */
async function api(path, options = {}) {
  const res = await fetch(`/admin/api${path}`, { credentials: "same-origin", ...options });
  if (res.status === 401) {
    showLogin();
    throw new Error("signed out");
  }
  let body = null;
  try {
    body = await res.json();
  } catch {
    /* 204s and file bodies */
  }
  if (!res.ok) {
    const err = new Error((body && body.message) || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

const json = (body) => ({ headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

/* ---------- boot ---------- */

async function boot() {
  const session = await fetch("/admin/api/session", { credentials: "same-origin" }).then((r) => r.json());
  // The markup carries the handle too, so an unresolved account still reads right.
  if (session.username) $("#login-handle").textContent = `@${session.username}`;
  if (!session.authed) return showLogin();
  await loadEverything();
  showApp();
}

async function loadEverything() {
  const data = await api("/state");
  state.account = data.account;
  state.limits = data.limits;
  state.files = data.files;
  state.config = data.rules && Array.isArray(data.rules.rules) ? data.rules : { rules: [] };
  state.etag = data.etag;
  state.problems = data.problems || [];
  state.savedJson = JSON.stringify(state.config.rules);
  renderAll();
  loadMedia();
}

async function loadMedia() {
  try {
    const data = await api("/media");
    state.media = data.items || [];
    state.mediaError = data.error || null;
  } catch (err) {
    state.mediaError = err.message;
  }
  renderRules();
  renderTestMedia();
}

function showLogin() {
  $("#app").classList.add("hidden");
  $("#login").classList.remove("hidden");
  setTimeout(() => $("#login-password").focus(), 30);
}
function showApp() {
  $("#login").classList.add("hidden");
  $("#app").classList.remove("hidden");
}

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("#login-error");
  err.classList.add("hidden");
  try {
    await api("/login", { method: "POST", ...json({ password: $("#login-password").value }) });
    $("#login-password").value = "";
    await loadEverything();
    showApp();
  } catch (ex) {
    err.textContent = ex.message;
    err.classList.remove("hidden");
  }
});

$("#btn-signout").addEventListener("click", async () => {
  if (isDirty() && !confirm("You have unsaved changes. Sign out anyway?")) return;
  await api("/logout", { method: "POST" }).catch(() => {});
  location.reload();
});

/* ---------- tabs ---------- */

document.querySelectorAll("nav.tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.tab = btn.dataset.tab;
    document.querySelectorAll("nav.tabs button").forEach((b) => b.setAttribute("aria-selected", String(b === btn)));
    for (const name of ["rules", "files", "activity"]) $(`#tab-${name}`).classList.toggle("hidden", name !== state.tab);
    if (state.tab === "activity") renderActivity();
  });
});

/* ---------- header ---------- */

function renderFacts() {
  const a = state.account || {};
  const bits = [
    a.username ? `@${esc(a.username)}` : "account not resolved",
    a.tokenDaysLeft == null ? "token: unknown" : `token: ${a.tokenDaysLeft}d left`,
    a.appSecret ? "signed" : "⚠ no app secret",
    `leads → ${esc(a.ledger || "logs")}`,
  ];
  $("#facts").innerHTML = bits.map((b) => `<span>${b}</span>`).join("");
}

/* ---------- problems ---------- */

/**
 * Findings from the server's validator, not a second copy of the rules here.
 * One validator, used by the boot check, the save gate and this banner, so the
 * panel can never disagree with what the service will actually accept.
 */
function renderProblems() {
  const box = $("#problems");
  const errors = state.problems.filter((p) => p.severity === "error");
  const warns = state.problems.filter((p) => p.severity === "warn");
  if (!errors.length && !warns.length) return (box.innerHTML = "");

  const group = (list, kind, title) =>
    !list.length
      ? ""
      : `<div class="note ${kind}"><strong>${title}</strong><ul>${list
          .map((p) => `<li>${esc(p.message)}</li>`)
          .join("")}</ul></div>`;

  box.innerHTML =
    group(errors, "error", errors.length === 1 ? "1 problem blocks saving" : `${errors.length} problems block saving`) +
    group(warns, "warn", warns.length === 1 ? "1 thing to look at" : `${warns.length} things to look at`);
}

/* ---------- rules ---------- */

const rules = () => state.config.rules;
const isDirty = () => JSON.stringify(rules()) !== state.savedJson;

function markDirty() {
  const dirty = isDirty();
  $("#btn-save").disabled = !dirty;
  $("#btn-revert").disabled = !dirty;
  $("#dirty").innerHTML = dirty
    ? `<span class="dirty-dot"></span>Unsaved — the account is still using the last saved version`
    : `Live. Every change here is what @${esc(state.account.username || "you")} replies with.`;
  $("#rule-count").textContent = `${rules().length} rule${rules().length === 1 ? "" : "s"}, ${rules().filter((r) => r.enabled !== false).length} on`;
}

function renderAll() {
  renderFacts();
  renderProblems();
  renderRules();
  renderFiles();
  renderTestMedia();
  $("#upload-limits").textContent = `Up to ${state.limits.maxUploadMB} MB · ${(state.limits.allowedTypes || []).join(", ")}`;
  markDirty();
}

const mediaById = (id) => state.media.find((m) => m.id === String(id));

function scopeSummary(rule) {
  const media = rule.media || {};
  if (media.mode !== "only" || !(media.ids || []).length) return "every post";
  const n = media.ids.length;
  return `${n} post${n === 1 ? "" : "s"}`;
}

function renderRules() {
  const host = $("#rules");
  if (!rules().length) {
    host.innerHTML = `<div class="note warn" style="margin:0">No rules yet. <strong>+ New rule</strong> and the account will start answering comments.</div>`;
    return markDirty();
  }
  host.innerHTML = rules().map(ruleCard).join("");
  wireRules();
  markDirty();
}

function ruleCard(rule, i) {
  const open = state.open.has(i);
  const bad = state.problems.some((p) => p.severity === "error" && p.ruleIndex === i);
  const keywords = (rule.keywords || []).map((k) => esc(k)).join(", ") || "no keywords yet";

  return `
<div class="rule ${rule.enabled === false ? "off" : ""} ${bad ? "bad" : ""}" data-i="${i}">
  <div class="rule-head" data-act="toggle">
    <div class="order">
      <button data-act="up" title="Earlier rules match first" ${i === 0 ? "disabled" : ""}>▲</button>
      <button data-act="down" ${i === rules().length - 1 ? "disabled" : ""}>▼</button>
    </div>
    <label class="switch" data-stop>
      <input type="checkbox" data-act="enabled" ${rule.enabled === false ? "" : "checked"}>
      <span class="track"></span>
    </label>
    <div>
      <div class="name">${esc(rule.name || rule.id || "Untitled rule")}</div>
      <div class="summary">${keywords} · ${scopeSummary(rule)}</div>
    </div>
    <div style="flex:1"></div>
    <span class="chev">${open ? "▲" : "▼"}</span>
  </div>

  ${open ? ruleBody(rule, i) : ""}
</div>`;
}

function ruleBody(rule, i) {
  const dm = rule.dm || {};
  const media = rule.media || { mode: "all", ids: [] };
  const only = media.mode === "only";
  const file = state.files.find((f) => f.id === dm.fileId);

  const previewParts = [dm.text, dm.link, file && file.url].filter(Boolean);

  return `
<div class="rule-body">
  <div class="two-col">
    <div>
      <label class="field">
        <span class="lbl">Name it (for you, not for followers)</span>
        <input type="text" data-act="name" value="${esc(rule.name || "")}" placeholder="Smart Storefront enquiries">
      </label>

      <div class="field">
        <span class="lbl">Fires when a comment contains</span>
        <div class="chips" data-act="chips">
          ${(rule.keywords || [])
            .map(
              (k, ki) =>
                `<span class="chip">${esc(k)}<button data-act="rmkw" data-ki="${ki}" title="Remove" type="button">×</button></span>`
            )
            .join("")}
          <input type="text" data-act="addkw" placeholder="type a keyword, press Enter">
        </div>
        <span class="hint">Case, punctuation, emoji and Arabic spelling variants are handled — "متجر" also matches "المتجر".</span>
      </div>

      <div class="field">
        <span class="lbl">How to match it</span>
        <div class="seg" data-act="match">
          <button type="button" data-mode="word" aria-pressed="${(rule.match || "word") === "word"}">Whole word</button>
          <button type="button" data-mode="contains" aria-pressed="${rule.match === "contains"}">Anywhere inside</button>
          <button type="button" data-mode="exact" aria-pressed="${rule.match === "exact"}">Whole comment</button>
        </div>
      </div>

      <div class="field">
        <span class="lbl">On which posts</span>
        <div class="seg" data-act="scope">
          <button type="button" data-mode="all" aria-pressed="${!only}">Every post</button>
          <button type="button" data-mode="only" aria-pressed="${only}">Only the ones I pick</button>
        </div>
        ${only ? postPicker(rule) : `<span class="hint">Any comment on any post or reel can trigger this rule.</span>`}
      </div>
    </div>

    <div>
      <label class="field">
        <span class="lbl">The DM they get</span>
        <textarea data-act="dmtext" placeholder="Here's the Smart Storefront breakdown — what it includes and how fast it goes live 👇">${esc(dm.text || "")}</textarea>
        <span class="hint">One message only. Instagram allows exactly one private reply per comment, ever — so the link and the file below are appended to this text, not sent after it.</span>
      </label>

      <label class="field">
        <span class="lbl">Link to include (optional)</span>
        <input type="text" data-act="dmlink" value="${esc(dm.link || "")}" placeholder="https://aiprofitlab.io/en/smart-storefront/">
      </label>

      <label class="field">
        <span class="lbl">File to send (optional)</span>
        <select data-act="dmfile">
          <option value="">— no file —</option>
          ${state.files
            .map((f) => `<option value="${esc(f.id)}" ${f.id === dm.fileId ? "selected" : ""}>${esc(f.name)} (${kb(f.size)})</option>`)
            .join("")}
        </select>
        <span class="hint">${
          dm.fileId && !file
            ? `<strong style="color:#a6431f">The attached file was deleted.</strong> Pick another, or the DM goes out without it.`
            : `Upload one on the <strong>Files</strong> tab. It is sent as a private link inside the message.`
        }</span>
      </label>

      <label class="field">
        <span class="lbl">Public reply under their comment</span>
        <input type="text" data-act="publicreply" value="${esc(rule.publicReply || "")}" placeholder="Sent! Check your DMs 📩">
        <span class="hint">Never repeat a keyword here. Instagram hands your own reply back as a new comment, and the account would answer itself — saving is blocked if it would.</span>
      </label>

      <div class="field">
        <label class="switch">
          <input type="checkbox" data-act="askemail" ${rule.askEmail ? "checked" : ""}>
          <span class="track"></span>
          <span>Ask them to reply with their email</span>
        </label>
        <span class="hint">Their reply is watched for 24 hours and the address is written back to the lead row.</span>
      </div>
    </div>
  </div>

  <div class="preview" style="margin-top:6px">
    <p class="lbl">What actually arrives</p>
    <div class="bubble">${previewParts.length ? esc(previewParts.join("\n\n")) : '<span class="muted">Nothing yet — add a message, a link or a file.</span>'}</div>
  </div>

  <div style="display:flex;gap:10px;margin-top:14px;align-items:center">
    <span class="muted mono">id: ${esc(rule.id || "—")}</span>
    <div style="flex:1"></div>
    <button class="danger tiny" data-act="delete" type="button">Delete this rule</button>
  </div>
</div>`;
}

function postPicker(rule) {
  const chosen = new Set((rule.media && rule.media.ids) || []);
  // Ids the account no longer returns — an old post, or one past the page we
  // fetched. Shown as a tile rather than dropped, because silently forgetting
  // targeting is how a rule starts firing everywhere.
  const orphans = [...chosen].filter((id) => !mediaById(id));

  if (!state.media.length && !orphans.length) {
    return `<div class="note warn" style="margin:8px 0 0">${
      state.mediaError ? esc(state.mediaError) : "Loading your posts…"
    }</div>`;
  }

  const tile = (m) => `
    <button type="button" class="post" data-act="pick" data-id="${esc(m.id)}" aria-pressed="${chosen.has(m.id)}" title="${esc(m.caption || m.id)}">
      ${m.thumb ? `<img src="${esc(m.thumb)}" alt="" loading="lazy">` : ""}
      ${m.type ? `<span class="kind">${esc(String(m.type).replace("CAROUSEL_ALBUM", "ALBUM"))}</span>` : ""}
      ${m.caption ? `<span class="cap">${esc(m.caption.slice(0, 60))}</span>` : ""}
    </button>`;

  return `
  <div class="posts">
    ${orphans
      .map(
        (id) =>
          `<button type="button" class="post missing" data-act="pick" data-id="${esc(id)}" aria-pressed="true" title="This post is not in the recent list">not in recent list<br>${esc(
            id
          )}</button>`
      )
      .join("")}
    ${state.media.map(tile).join("")}
  </div>
  <span class="hint">${chosen.size} selected${state.mediaError ? ` · ${esc(state.mediaError)}` : ""}</span>`;
}

const kb = (n) => (n > 1024 * 1024 ? `${(n / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

/* ---------- rule interactions ---------- */

/**
 * Rebinding after every render is fine at this size and removes a whole class
 * of stale-closure bug. Text inputs update state WITHOUT re-rendering, so the
 * caret never jumps mid-word; only structural changes redraw.
 */
function wireRules() {
  const host = $("#rules");

  host.querySelectorAll(".rule").forEach((card) => {
    const i = Number(card.dataset.i);
    const rule = rules()[i];

    card.querySelector(".rule-head").addEventListener("click", (e) => {
      if (e.target.closest("[data-stop]") || e.target.closest(".order")) return;
      state.open.has(i) ? state.open.delete(i) : state.open.add(i);
      renderRules();
    });

    const on = (sel, event, fn) => card.querySelectorAll(sel).forEach((el) => el.addEventListener(event, fn));

    on('[data-act="up"]', "click", () => move(i, -1));
    on('[data-act="down"]', "click", () => move(i, 1));
    on('[data-act="enabled"]', "change", (e) => {
      rule.enabled = e.target.checked;
      renderRules();
    });

    // Live-typed fields: state only, no redraw.
    const bind = (sel, apply) =>
      on(sel, "input", (e) => {
        apply(e.target.value);
        markDirty();
      });
    bind('[data-act="name"]', (v) => (rule.name = v));
    bind('[data-act="dmtext"]', (v) => ((rule.dm = rule.dm || {}), (rule.dm.text = v), refreshPreview(card, rule)));
    bind('[data-act="dmlink"]', (v) => ((rule.dm = rule.dm || {}), (rule.dm.link = v), refreshPreview(card, rule)));
    bind('[data-act="publicreply"]', (v) => (rule.publicReply = v));

    on('[data-act="dmfile"]', "change", (e) => {
      rule.dm = rule.dm || {};
      rule.dm.fileId = e.target.value;
      renderRules();
    });
    on('[data-act="askemail"]', "change", (e) => {
      rule.askEmail = e.target.checked;
      markDirty();
    });

    on('[data-act="match"] button', "click", (e) => {
      rule.match = e.currentTarget.dataset.mode;
      renderRules();
    });
    on('[data-act="scope"] button', "click", (e) => {
      const mode = e.currentTarget.dataset.mode;
      rule.media = { mode, ids: (rule.media && rule.media.ids) || [] };
      renderRules();
    });
    on('[data-act="pick"]', "click", (e) => {
      const id = e.currentTarget.dataset.id;
      rule.media = rule.media || { mode: "only", ids: [] };
      const set = new Set(rule.media.ids || []);
      set.has(id) ? set.delete(id) : set.add(id);
      rule.media.ids = [...set];
      renderRules();
    });

    on('[data-act="rmkw"]', "click", (e) => {
      rule.keywords.splice(Number(e.currentTarget.dataset.ki), 1);
      renderRules();
    });
    const kw = card.querySelector('[data-act="addkw"]');
    if (kw) {
      const commit = () => {
        const value = kw.value.trim().replace(/,$/, "");
        if (!value) return;
        rule.keywords = [...new Set([...(rule.keywords || []), value])];
        kw.value = "";
        renderRules();
        // Straight back into the field: keywords are added several at a time.
        const next = $(`.rule[data-i="${i}"] [data-act="addkw"]`);
        if (next) next.focus();
      };
      kw.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === ",") {
          e.preventDefault();
          commit();
        } else if (e.key === "Backspace" && !kw.value && (rule.keywords || []).length) {
          rule.keywords.pop();
          renderRules();
          const next = $(`.rule[data-i="${i}"] [data-act="addkw"]`);
          if (next) next.focus();
        }
      });
      kw.addEventListener("blur", commit);
    }

    on('[data-act="delete"]', "click", () => {
      if (!confirm(`Delete "${rule.name || rule.id}"? Followers commenting those keywords stop getting anything.`)) return;
      rules().splice(i, 1);
      state.open = new Set();
      renderRules();
    });
  });
}

function refreshPreview(card, rule) {
  const file = state.files.find((f) => f.id === (rule.dm && rule.dm.fileId));
  const parts = [rule.dm && rule.dm.text, rule.dm && rule.dm.link, file && file.url].filter(Boolean);
  const bubble = card.querySelector(".preview .bubble");
  if (bubble) bubble.textContent = parts.join("\n\n") || "Nothing yet — add a message, a link or a file.";
}

function move(i, by) {
  const to = i + by;
  if (to < 0 || to >= rules().length) return;
  const [row] = rules().splice(i, 1);
  rules().splice(to, 0, row);
  // Order is the matching order, so an expanded card must follow its rule.
  const open = new Set();
  for (const idx of state.open) open.add(idx === i ? to : idx === to ? i : idx);
  state.open = open;
  renderRules();
}

$("#btn-add").addEventListener("click", () => {
  const n = rules().length + 1;
  rules().push({
    id: `rule-${n}-${Math.random().toString(36).slice(2, 6)}`,
    name: `New rule ${n}`,
    enabled: false, // off until it has been given something to say
    keywords: [],
    match: "word",
    media: { mode: "all", ids: [] },
    dm: { text: "", link: "" },
    publicReply: "",
    askEmail: false,
  });
  state.open = new Set([rules().length - 1]);
  renderRules();
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
});

$("#btn-revert").addEventListener("click", () => {
  if (!confirm("Throw away every change since the last save?")) return;
  state.config.rules = JSON.parse(state.savedJson);
  renderRules();
});

$("#btn-save").addEventListener("click", async () => {
  const btn = $("#btn-save");
  btn.disabled = true;
  btn.textContent = "Saving…";
  try {
    const result = await api("/rules", { method: "PUT", ...json({ rules: rules(), etag: state.etag }) });
    state.config = result.rules;
    state.etag = result.etag;
    state.problems = result.problems || [];
    state.savedJson = JSON.stringify(state.config.rules);
    renderProblems();
    renderRules();
    toast("Live. The next matching comment uses these rules.");
  } catch (err) {
    state.problems = (err.body && err.body.problems) || state.problems;
    renderProblems();
    toast(err.message, true);
    if (err.status === 409) {
      // Someone (or another tab) saved in between. Refusing is the whole point;
      // offering the reload is the only useful next step.
      if (confirm(`${err.message}\n\nReload now? Unsaved edits on this page are lost.`)) location.reload();
    }
  } finally {
    btn.textContent = "Save & go live";
    markDirty();
  }
});

window.addEventListener("beforeunload", (e) => {
  if (!isDirty()) return;
  e.preventDefault();
  e.returnValue = "";
});

/* ---------- the dry run ---------- */

$("#btn-test").addEventListener("click", () => {
  $("#tester").classList.toggle("hidden");
  if (!$("#tester").classList.contains("hidden")) $("#test-text").focus();
});

function renderTestMedia() {
  const sel = $("#test-media");
  if (!sel) return;
  const keep = sel.value;
  sel.innerHTML =
    `<option value="">— any post (untargeted rules only) —</option>` +
    state.media
      .map((m) => `<option value="${esc(m.id)}">${esc((m.caption || m.id).slice(0, 60))}</option>`)
      .join("");
  sel.value = keep;
}

$("#btn-run-test").addEventListener("click", async () => {
  const box = $("#test-result");
  box.innerHTML = `<span class="muted">Checking…</span>`;
  try {
    const body = { text: $("#test-text").value, rules: rules() };
    const mediaId = $("#test-media").value;
    if (mediaId) body.mediaId = mediaId;
    const r = await api("/rules/preview", { method: "POST", ...json(body) });
    box.innerHTML =
      r.outcome === "dropped"
        ? `<div class="note warn" style="margin:0"><strong>Nothing happens.</strong> ${esc(r.why)}</div>`
        : `<div class="preview">
             <p class="lbl">Rule: ${esc(r.ruleName)} — matched on "${esc(r.keyword)}"</p>
             <div class="bubble">${esc(r.dm)}</div>
             <p class="lbl" style="margin-top:10px">Public reply</p>
             <div class="bubble" style="border-radius:14px 14px 4px 14px">${esc(r.publicReply || "— none —")}</div>
             ${r.askEmail ? `<p class="muted" style="margin:8px 0 0;font-size:12.5px">Then waits 24h for an email in their reply.</p>` : ""}
           </div>`;
  } catch (err) {
    box.innerHTML = `<div class="note error" style="margin:0">${esc(err.message)}</div>`;
  }
});

/* ---------- files ---------- */

function renderFiles() {
  const host = $("#file-list");
  if (!state.files.length) {
    host.innerHTML = `<p class="muted" style="font-size:13.5px">Nothing uploaded yet.</p>`;
    return;
  }
  host.innerHTML = `
  <table class="rows">
    <thead><tr><th>File</th><th>Size</th><th>Used by</th><th></th></tr></thead>
    <tbody>
      ${state.files
        .map((f) => {
          const used = rules().filter((r) => r.dm && r.dm.fileId === f.id).map((r) => r.name || r.id);
          return `<tr>
            <td><strong>${esc(f.name)}</strong><br><span class="mono muted">${esc(f.url)}</span></td>
            <td>${kb(f.size)}</td>
            <td>${used.length ? used.map((u) => `<span class="pill">${esc(u)}</span>`).join(" ") : `<span class="muted">—</span>`}</td>
            <td style="text-align:right;white-space:nowrap">
              <button class="tiny" data-copy="${esc(f.url)}">Copy link</button>
              <button class="tiny danger" data-del="${esc(f.id)}">Delete</button>
            </td>
          </tr>`;
        })
        .join("")}
    </tbody>
  </table>`;

  host.querySelectorAll("[data-copy]").forEach((b) =>
    b.addEventListener("click", async () => {
      await navigator.clipboard.writeText(b.dataset.copy).catch(() => {});
      toast("Link copied");
    })
  );
  host.querySelectorAll("[data-del]").forEach((b) =>
    b.addEventListener("click", async () => {
      if (!confirm("Delete this file? Any DM link to it stops working immediately, including ones already sent.")) return;
      try {
        await api(`/files/${b.dataset.del}`, { method: "DELETE" });
        await refreshFiles();
        toast("Deleted");
      } catch (err) {
        toast(err.message, true);
      }
    })
  );
}

async function refreshFiles() {
  const data = await api("/state");
  state.files = data.files;
  renderFiles();
  renderRules();
}

async function upload(file) {
  if (!file) return;
  const err = $("#upload-error");
  err.innerHTML = "";
  $("#drop").classList.add("over");
  try {
    const res = await api("/files", {
      method: "POST",
      headers: { "content-type": file.type || "application/octet-stream", "x-filename": file.name },
      body: file,
    });
    await refreshFiles();
    toast(`${res.file.name} uploaded`);
  } catch (ex) {
    err.innerHTML = `<div class="note error">${esc(ex.message)}</div>`;
  } finally {
    $("#drop").classList.remove("over");
  }
}

$("#btn-browse").addEventListener("click", () => $("#file-input").click());
$("#file-input").addEventListener("change", (e) => {
  upload(e.target.files[0]);
  e.target.value = "";
});
["dragenter", "dragover"].forEach((ev) =>
  $("#drop").addEventListener(ev, (e) => {
    e.preventDefault();
    $("#drop").classList.add("over");
  })
);
["dragleave", "drop"].forEach((ev) =>
  $("#drop").addEventListener(ev, (e) => {
    e.preventDefault();
    if (ev === "dragleave") $("#drop").classList.remove("over");
  })
);
$("#drop").addEventListener("drop", (e) => upload(e.dataTransfer.files[0]));

/* ---------- activity ---------- */

async function renderActivity() {
  const host = $("#activity");
  host.innerHTML = `<p class="muted">Loading…</p>`;
  try {
    const data = await api("/activity");
    if (!data.items.length) {
      host.innerHTML = `<div class="note ok" style="margin:0">Nothing yet. Every keyword comment the service acts on shows up here.</div>`;
      return;
    }
    host.innerHTML = `
    <table class="rows">
      <thead><tr><th>When</th><th>Who</th><th>Rule</th><th>Result</th><th>Notes</th></tr></thead>
      <tbody>${data.items
        .map(
          (r) => `<tr>
            <td class="mono">${esc(r.at.replace("T", " ").slice(0, 16))}</td>
            <td>${r.username ? `<a href="https://instagram.com/${esc(r.username)}" target="_blank" rel="noopener">@${esc(r.username)}</a>` : "—"}</td>
            <td>${esc(r.ruleId || "—")}</td>
            <td><span class="pill ${esc(r.status)}">${esc(r.status)}</span></td>
            <td class="muted">${esc(r.notes || "")}</td>
          </tr>`
        )
        .join("")}</tbody>
    </table>
    <p class="muted" style="font-size:12.5px;margin-top:10px">${data.stats.handled} comments handled all-time · ${data.stats.openConversations} waiting on an email reply</p>`;
  } catch (err) {
    host.innerHTML = `<div class="note error" style="margin:0">${esc(err.message)}</div>`;
  }
}

$("#btn-refresh-activity").addEventListener("click", renderActivity);

boot().catch((err) => {
  console.error(err);
  showLogin();
});
