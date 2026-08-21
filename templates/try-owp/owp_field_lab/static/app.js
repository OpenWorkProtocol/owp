"use strict";

const $ = (id) => document.getElementById(id);
const form = $("submit-form");
const submitButton = $("submit-button");
let currentRef = null;
let currentToken = null;
let accepting = true;

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]));
}

function setMessage(el, text, kind = "") {
  el.textContent = text || "";
  el.className = `message ${kind}`.trim();
}

function money(value) {
  return `$${value || "0.00"}`;
}

function fragmentFor(ref, token) {
  const q = new URLSearchParams({work: ref, token});
  return `${location.origin}${location.pathname}#${q.toString()}`;
}

function readFragment() {
  const q = new URLSearchParams(location.hash.replace(/^#/, ""));
  const work = q.get("work");
  const token = q.get("token");
  return work && token ? {work, token} : null;
}

async function api(path, opts = {}) {
  const headers = {Accept: "application/json", ...(opts.headers || {})};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;
  const res = await fetch(path, {...opts, headers, body: opts.body === undefined ? undefined : JSON.stringify(opts.body)});
  let body = {};
  try { body = await res.json(); } catch (_) {}
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

async function refreshCapacity() {
  const status = await api("/api/status");
  const q = status.queue;
  accepting = Boolean(q.accepting);
  $("capacity-count").textContent = `${q.occupied} / ${q.max}`;
  $("capacity-fill").style.width = `${Math.min(100, (q.occupied / q.max) * 100)}%`;
  $("capacity-status").textContent = accepting ? `${q.available} slots open` : "Queue full";
  submitButton.disabled = !accepting;
}

function connectLive() {
  if (!("EventSource" in window)) return;
  const stream = new EventSource("/api/live");
  stream.addEventListener("capacity", (event) => {
    try {
      const status = JSON.parse(event.data);
      const q = status.queue;
      accepting = Boolean(q.accepting);
      $("capacity-count").textContent = `${q.occupied} / ${q.max}`;
      $("capacity-fill").style.width = `${Math.min(100, (q.occupied / q.max) * 100)}%`;
      $("capacity-status").textContent = accepting ? `${q.available} slots open` : "Queue full";
      submitButton.disabled = !accepting;
    } catch (_) {}
  });
  stream.onerror = () => { $("live-status").innerHTML = "<i></i> reconnecting"; };
  stream.onopen = () => { $("live-status").innerHTML = "<i></i> live"; };
}

function selectedKind() {
  return form.querySelector('input[name="work_kind"]:checked')?.value || "github_pr";
}

function syncKindFields() {
  const kind = selectedKind();
  $("pr-fields").classList.toggle("hidden", kind !== "github_pr");
  $("idea-fields").classList.toggle("hidden", kind !== "idea");
  $("pr-url").required = kind === "github_pr";
  $("idea-title").required = kind === "idea";
}

form.querySelectorAll('input[name="work_kind"]').forEach((input) => input.addEventListener("change", syncKindFields));
syncKindFields();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!accepting) return setMessage($("form-message"), "The field-lab queue is full right now.", "error");
  submitButton.disabled = true;
  setMessage($("form-message"), "Verifying and creating durable work…");
  const kind = selectedKind();
  const body = {
    work_kind: kind,
    value_usd: $("value-usd").value.trim(),
    outcome: $("outcome").value.trim(),
    attested: $("attested").checked,
    pr_url: kind === "github_pr" ? $("pr-url").value.trim() : "",
    idea_title: kind === "idea" ? $("idea-title").value.trim() : "",
    context_url: kind === "idea" ? $("context-url").value.trim() : "",
  };
  try {
    const result = await api("/api/submissions", {method: "POST", body});
    currentRef = result.work_ref;
    currentToken = result.claim_token;
    const link = fragmentFor(currentRef, currentToken);
    history.replaceState(null, "", `#${new URL(link).hash.slice(1)}`);
    $("tracking-link").value = link;
    $("receipt-title").textContent = `${currentRef} is live.`;
    $("receipt-copy").textContent = "__OWP_OPERATOR_NAME__ now has an explicit choice: accept the work or pass. Save the tracking link before you close this page.";
    $("receipt-panel").classList.remove("hidden");
    setMessage($("form-message"), "Work created.", "success");
    renderWork(result.work);
    $("work-panel").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (err) {
    setMessage($("form-message"), err.message, "error");
  } finally {
    try { await refreshCapacity(); } catch (_) {}
    submitButton.disabled = !accepting;
  }
});

$("copy-link").addEventListener("click", async () => {
  const value = $("tracking-link").value;
  try { await navigator.clipboard.writeText(value); $("copy-link").textContent = "Copied"; }
  catch (_) { $("tracking-link").select(); document.execCommand("copy"); $("copy-link").textContent = "Copied"; }
  setTimeout(() => { $("copy-link").textContent = "Copy"; }, 1200);
});

function sourceLabel(source) {
  if (source.kind === "github_pr") return `${source.repo} #${source.number}`;
  return source.title || "Build idea";
}

function sourceDetail(source) {
  if (source.kind === "github_pr") return `${source.size_band} · ${source.changed_files} files · +${source.additions}/-${source.deletions}`;
  return source.context_url || "No external context URL";
}

function stageFor(work) {
  if (work.state === "completed" || work.state === "cancelled") return "decision";
  if (work.validation_status || work.state === "review") return "validation";
  if (work.attempt_number > 0 || work.state === "in_progress" || work.state === "parked") return "attempt";
  if (work.provider_decision === "ACCEPT" || work.state === "todo") return "accepted";
  return "submitted";
}

function renderStages(work) {
  const order = ["submitted", "accepted", "attempt", "validation", "decision"];
  const current = order.indexOf(stageFor(work));
  document.querySelectorAll(".stage-rail span").forEach((node) => {
    node.classList.toggle("active", order.indexOf(node.dataset.stage) <= current);
  });
}

function eventSummary(ev) {
  const p = ev.payload || {};
  const labels = {
    "work.requested":"Work requested",
    "provider.accepted":"__OWP_OPERATOR_NAME__ accepted",
    "provider.passed":"__OWP_OPERATOR_NAME__ passed",
    "pr.snapshot_refreshed":"PR snapshot refreshed",
    "attempt.started":"Attempt started",
    "question.asked":"Question asked",
    "question.answered":"Customer answered",
    "delivery.submitted":"Delivery submitted",
    "validation.recorded":"Validation recorded",
    "customer.approved":"Customer approved",
    "customer.steered":"Customer steered",
    "customer.rejected":"Customer rejected",
  };
  let detail = "";
  if (p.reason) detail = p.reason;
  else if (p.note) detail = p.note;
  else if (p.summary) detail = p.summary;
  else if (p.text) detail = p.text;
  else if (p.result) detail = `${p.result}${p.validator ? ` · ${p.validator}` : ""}`;
  else if (p.option) detail = p.option;
  else if (p.attempt_number) detail = `Attempt ${p.attempt_number}`;
  return {name: labels[ev.type] || ev.type, detail};
}

function renderTimeline(events) {
  $("timeline").innerHTML = events.map((ev) => {
    const info = eventSummary(ev);
    return `<li><div class="seq">${String(ev.seq).padStart(2, "0")}</div><div><div class="event-name">${esc(info.name)}</div><div class="payload">${esc(info.detail)}</div></div><div class="meta">${esc(ev.actor)}<br>${esc(ev.created_at)}<br><code title="${esc(ev.event_hash)}">${esc(ev.event_hash.slice(0, 12))}…</code></div></li>`;
  }).join("");
}

function renderQuestion(work) {
  const box = $("question-box");
  const q = work.questions.find((item) => item.status === "open");
  if (!q) return box.classList.add("hidden");
  box.innerHTML = `<h3>__OWP_OPERATOR_NAME__ needs a decision</h3><p>${esc(q.text)}</p>${q.evidence.length ? `<p>${q.evidence.map((u) => `<a href="${esc(u)}" rel="noopener" target="_blank">Evidence</a>`).join(" · ")}</p>` : ""}<form id="answer-form">${q.options.map((option, i) => `<label class="option"><input type="radio" name="answer" value="${esc(option)}" ${i === 0 ? "checked" : ""}><span>${esc(option)}</span></label>`).join("")}<textarea id="answer-note" maxlength="2000" placeholder="Optional note"></textarea><button type="submit">Record decision →</button></form>`;
  box.classList.remove("hidden");
  $("answer-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const option = new FormData(event.currentTarget).get("answer");
    try {
      const updated = await api(`/api/work/${currentRef}/answer`, {method:"POST", token:currentToken, body:{question_id:q.id, option, note:$("answer-note").value}});
      renderWork(updated);
    } catch (err) { setMessage($("work-message"), err.message, "error"); }
  });
}

function renderDisposition(work) {
  const box = $("disposition-box");
  if (!(work.state === "review" && work.validation_status === "valid")) return box.classList.add("hidden");
  box.innerHTML = `<h3>The delivery passed recorded validation. Your call.</h3><p>Approve closes this work. Steer creates another attempt. Reject closes it as rejected.</p><textarea id="disposition-note" maxlength="2000" placeholder="Required for steer or reject; optional for approve."></textarea><div class="decision-buttons"><button data-action="approve">Approve</button><button data-action="steer">Steer another attempt</button><button data-action="reject" class="danger">Reject</button></div>`;
  box.classList.remove("hidden");
  box.querySelectorAll("button[data-action]").forEach((button) => button.addEventListener("click", async () => {
    try {
      const updated = await api(`/api/work/${currentRef}/disposition`, {method:"POST", token:currentToken, body:{action:button.dataset.action, note:$("disposition-note").value}});
      renderWork(updated);
    } catch (err) { setMessage($("work-message"), err.message, "error"); }
  }));
}

function renderWork(work) {
  $("work-panel").classList.remove("hidden");
  $("work-ref").textContent = work.work_ref;
  $("work-state").textContent = work.state.replaceAll("_", " ");
  $("integrity-state").textContent = work.integrity.chain_verified ? "chain verified" : "integrity warning";
  $("integrity-state").style.color = work.integrity.chain_verified ? "var(--good)" : "var(--bad)";
  const source = work.source;
  $("work-summary").innerHTML = `
    <div><small>Source</small><strong>${esc(sourceLabel(source))}</strong></div>
    <div><small>Source detail</small><strong>${esc(sourceDetail(source))}</strong></div>
    <div><small>Value signal</small><strong>${esc(money(work.value_signal_usd))}</strong></div>
    <div><small>Attempt</small><strong>${work.attempt_number || "Not started"}</strong></div>
    <div><small>Provider decision</small><strong>${esc(work.provider_decision || "Pending")}</strong></div>
    <div><small>Validation</small><strong>${esc(work.validation_status || "Pending")}</strong></div>
    <div style="grid-column:span 2"><small>Requested outcome</small><strong>${esc(work.outcome)}</strong></div>`;
  renderStages(work);
  renderQuestion(work);
  renderDisposition(work);
  renderTimeline(work.events);
  setMessage($("work-message"), work.state === "cancelled" ? "This work item is closed." : work.state === "completed" ? "This work item is complete." : "");
}

async function loadCurrent() {
  const found = readFragment();
  if (!found) return;
  currentRef = found.work;
  currentToken = found.token;
  $("tracking-link").value = fragmentFor(currentRef, currentToken);
  try {
    const work = await api(`/api/work/${encodeURIComponent(currentRef)}`, {token: currentToken});
    $("receipt-panel").classList.remove("hidden");
    $("receipt-title").textContent = `${currentRef} private work thread`;
    $("receipt-copy").textContent = "This tracking link is the customer key for the durable work record.";
    renderWork(work);
  } catch (err) {
    setMessage($("form-message"), "That private tracking link is invalid or unavailable.", "error");
  }
}

$("download-handoff").addEventListener("click", async () => {
  if (!currentRef || !currentToken) return;
  try {
    const data = await api(`/api/work/${encodeURIComponent(currentRef)}/handoff`, {token: currentToken});
    const blob = new Blob([JSON.stringify(data, null, 2) + "\n"], {type:"application/json"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${currentRef}-handoff.json`; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (err) { setMessage($("work-message"), err.message, "error"); }
});

refreshCapacity().catch(() => {});
connectLive();
loadCurrent();
