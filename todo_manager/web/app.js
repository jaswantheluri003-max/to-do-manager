(() => {
  "use strict";

  const API_BASE = "";
  const PAGE_SIZE = 10;

  const $ = (sel, scope = document) => scope.querySelector(sel);
  const $$ = (sel, scope = document) => Array.from(scope.querySelectorAll(sel));

  const els = {
    header: $("#site-header"),
    navNewTask: $("#nav-new-task"),
    syncIndicator: $("#sync-indicator"),
    heroTaskCount: $("#hero-task-count"),
    kpiTotal: $("#kpi-total"),
    kpiTotalSub: $("#kpi-total-sub"),
    kpiRate: $("#kpi-rate"),
    kpiProgressFill: $("#kpi-progress-fill"),
    kpiOverdue: $("#kpi-overdue"),
    kpiOverdueSub: $("#kpi-overdue-sub"),
    kpiTurnaround: $("#kpi-turnaround"),
    wsSearch: $("#ws-search"),
    filterRows: $$(".filter-row"),
    fcountAll: $("#fcount-all"),
    fcountOverdue: $("#fcount-overdue"),
    fcountCategory: $("#fcount-category"),
    fcountCompleted: $("#fcount-completed"),
    pills: $$(".pill"),
    ledgerTbody: $("#ledger-tbody"),
    ledgerEmpty: $("#ledger-empty"),
    pagPrev: $("#pag-prev"),
    pagNext: $("#pag-next"),
    pagPageNum: $("#pag-page-num"),
    pagTotal: $("#pag-total"),
    createForm: $("#create-form"),
    cfTitle: $("#cf-title"),
    cfCategory: $("#cf-category"),
    cfPrioritySegs: $$("#cf-priority .seg"),
    cfPriorityInput: $("input[name='priority']"),
    cfDue: $("#cf-due"),
    cfDesc: $("#cf-desc"),
    cfSubmit: $("#cf-submit"),
    formNote: $("#form-note"),
    chartCategory: $("#chart-category"),
    chartPriority: $("#chart-priority"),
    watchlist: $("#watchlist"),
    dropzone: $("#dropzone"),
    csvInput: $("#csv-input"),
    btnPickCsv: $("#btn-pick-csv"),
    importLog: $("#import-log"),
    btnRefresh: $("#btn-refresh-metrics"),
    exportBtns: $$("[data-format]"),
    toast: $("#toast"),
    toastMsg: $("#toast-msg"),
    toastClose: $("#toast-close"),
    footerHealth: $("#footer-health"),
  };

  const state = {
    tasks: [],
    filter: "all",
    priorityFilter: "all",
    query: "",
    page: 1,
    analytics: null,
  };

  const PRIORITY_LABELS = { 1: "Low", 2: "Medium", 3: "High", 4: "Critical", 5: "Urgent" };
  const PRIORITY_CLASSES = { 1: "low", 2: "medium", 3: "medium", 4: "critical", 5: "critical" };

  async function fetchJSON(path, opts = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Request failed (${res.status})`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  function escapeHtml(value) {
    const ent = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return String(value ?? "").replace(/[&<>"']/g, (c) => ent[c]);
  }

  function parseDateISO(v) {
    if (!v) return null;
    const d = new Date(v);
    return isNaN(d.getTime()) ? null : d;
  }

  function isOverdue(task) {
    if (task.completed || !task.due_date) return false;
    return new Date() > parseDateISO(task.due_date);
  }

  function daysOverdue(task) {
    if (!isOverdue(task)) return 0;
    const due = parseDateISO(task.due_date);
    return Math.ceil((new Date() - due) / (1000 * 60 * 60 * 24));
  }

  function formatDate(v) {
    if (!v) return "&mdash;";
    const d = parseDateISO(v);
    if (!d) return "&mdash;";
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  async function loadTasks() {
    const params = new URLSearchParams();
    if (state.query) params.set("q", state.query);
    if (state.filter === "completed") params.set("status", "completed");
    else if (state.filter === "pending") params.set("status", "pending");
    else if (state.filter === "overdue") params.set("overdue_only", "true");
    if (state.priorityFilter !== "all") params.set("priority", state.priorityFilter);

    const data = await fetchJSON(`/api/tasks?${params}`);
    state.tasks = data.tasks || [];
    renderLedger();
    updateCounters();
  }

  function filteredTasks() {
    let list = state.tasks;
    if (state.query) {
      const q = state.query.toLowerCase();
      list = list.filter((t) => (t.title || "").toLowerCase().includes(q) || (t.description || "").toLowerCase().includes(q));
    }
    if (state.priorityFilter !== "all") {
      list = list.filter((t) => String(t.priority) === state.priorityFilter);
    }
    return list;
  }

  function renderLedger() {
    const list = filteredTasks();
    const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (state.page > totalPages) state.page = totalPages;
    const start = (state.page - 1) * PAGE_SIZE;
    const pageItems = list.slice(start, start + PAGE_SIZE);

    els.ledgerTbody.innerHTML = "";
    if (list.length === 0) {
      els.ledgerEmpty.hidden = false;
      els.ledgerTbody.hidden = true;
    } else {
      els.ledgerEmpty.hidden = true;
      els.ledgerTbody.hidden = false;
      pageItems.forEach((task) => {
        const overdue = isOverdue(task);
        const dueClass = overdue ? "overdue" : daysUntil(task) <= 2 ? "soon" : "";
        const prioCls = PRIORITY_CLASSES[task.priority] || "low";
        const statusCls = task.completed ? "done" : "pending";
        const statusText = task.completed ? "Done" : "Pending";
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="task-id">${escapeHtml(task.id)}</span></td>
          <td><div class="task-title">${escapeHtml(task.title)}</div></td>
          <td><span class="task-category">${escapeHtml(task.category)}</span></td>
          <td><span class="priority-badge ${prioCls}">${escapeHtml(PRIORITY_LABELS[task.priority] || task.priority)}</span></td>
          <td><span class="task-due ${dueClass}">${formatDate(task.due_date)}${overdue ? " &middot; OVERDUE" : ""}</span></td>
          <td><span class="status-cell ${statusCls}">${statusText}</span></td>
          <td>
            <button class="action-btn toggle" data-id="${escapeHtml(task.id)}" aria-label="${task.completed ? "Reopen" : "Complete"}: ${escapeHtml(task.title)}" title="${task.completed ? "Reopen" : "Complete"}">${task.completed ? "\u21ba" : "\u2713"}</button>
            <button class="action-btn delete" data-id="${escapeHtml(task.id)}" aria-label="Delete: ${escapeHtml(task.title)}" title="Delete">&#215;</button>
          </td>
        `;
        els.ledgerTbody.appendChild(tr);
      });

      els.ledgerTbody.addEventListener("click", (ev) => {
        const toggle = ev.target.closest(".toggle");
        const del = ev.target.closest(".delete");
        if (toggle) {
          const id = toggle.dataset.id;
          toggleTask(id, !getTask(id).completed);
        } else if (del) {
          const id = del.dataset.id;
          deleteTask(id);
        }
      });
    }

    els.pagPageNum.textContent = String(state.page);
    els.pagTotal.textContent = String(totalPages);
    els.pagPrev.disabled = state.page <= 1;
    els.pagNext.disabled = state.page >= totalPages;
  }

  function getTask(id) {
    return state.tasks.find((t) => t.id === id);
  }

  function daysUntil(task) {
    if (!task.due_date) return null;
    const due = parseDateISO(task.due_date);
    if (!due) return null;
    return Math.round((due - new Date()) / (1000 * 60 * 60 * 24));
  }

  function updateCounters() {
    const total = state.tasks.length;
    const completed = state.tasks.filter((t) => t.completed).length;
    const pending = total - completed;
    const overdue = state.tasks.filter(isOverdue).length;
    const rate = total ? Math.round((completed / total) * 100) : 0;

    els.heroTaskCount.textContent = String(total);
    els.kpiTotal.textContent = String(total);
    els.kpiTotalSub.textContent = `${pending} pending · ${completed} completed`;
    els.kpiRate.textContent = `${rate}%`;
    els.kpiProgressFill.style.width = `${rate}%`;
    els.kpiOverdue.textContent = String(overdue);
    els.kpiOverdue.textContent = String(overdue);
    els.kpiOverdueSub.textContent = overdue > 0 ? "threshold flag" : "all clear";
    els.kpiTurnaround.textContent = state.analytics ? `${state.analytics.avg_turnaround_hours || 0}h` : "0h";

    els.fcountAll.textContent = String(total);
    els.fcountOverdue.textContent = String(overdue);
    els.fcountCompleted.textContent = String(completed);

    const categoryCounts = {};
    state.tasks.forEach((t) => { if (!t.completed) categoryCounts[t.category] = (categoryCounts[t.category] || 0) + 1; });
    els.fcountCategory.textContent = String(Object.values(categoryCounts).reduce((a, b) => a + b, 0));
  }

  async function loadAnalytics() {
    try {
      state.analytics = await fetchJSON("/api/analytics");
      renderAnalytics();
      updateCounters();
    } catch (err) {
      console.error("Analytics load failed:", err);
    }
  }

  function renderAnalytics() {
    if (!state.analytics) return;
    const { category_breakdown: cat, priority_breakdown: prio } = state.analytics;

    // Category bar chart
    const catEntries = Object.entries(cat).sort((a, b) => b[1] - a[1]);
    const maxCat = catEntries.length ? catEntries[0][1] : 1;
    els.chartCategory.innerHTML = catEntries.map(([name, count]) => `
      <div class="bar-row">
        <span class="bar-name">${escapeHtml(name)}</span>
        <div class="bar-track"><span class="bar-fill" style="width: ${Math.max(8, Math.round((count / maxCat) * 100))}%"></span></div>
        <span class="bar-num">${count}</span>
      </div>
    `).join("");

    // Priority ring
    const pendingPrio = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    state.tasks.filter((t) => !t.completed).forEach((t) => { pendingPrio[t.priority] = (pendingPrio[t.priority] || 0) + 1; });
    const totalPrio = Object.values(pendingPrio).reduce((a, b) => a + b, 0);
    const criticalPct = totalPrio ? Math.round(((pendingPrio[4] || 0) + (pendingPrio[5] || 0)) / totalPrio * 100) : 0;
    const ring = $(".ring-fill");
    const valBig = $(".ring-value .big");
    const valSmall = $(".ring-value .small");
    if (ring) ring.style.strokeDashoffset = `452`;
    if (valBig) valBig.textContent = `${criticalPct}%`;
    if (valSmall) valSmall.textContent = "critical / urgent";

    // Watchlist
    const overdue = state.tasks.filter(isOverdue).sort((a, b) => daysOverdue(b) - daysOverdue(a)).slice(0, 6);
    els.watchlist.innerHTML = overdue.map((t) => `
      <li class="watch-item">
        <span class="watch-title">${escapeHtml(t.title)}</span>
        <span class="watch-days">${daysOverdue(t)}d overdue</span>
      </li>
    `).join("");
  }

  async function toggleTask(id, completed) {
    try {
      if (completed) {
        await fetchJSON(`/api/tasks/${id}/complete`, { method: "PATCH" });
      } else {
        // No uncomplete endpoint in spec; simulate by toggling locally is not ideal.
        // We'll mark complete only via API; reopen not exposed, so skip.
        showToast("Reopen not supported via API.", null);
        return;
      }
      await loadTasks();
      await loadAnalytics();
      showToast(completed ? "Task completed." : "Task reopened.");
    } catch (err) {
      showToast(err.message);
    }
  }

  async function deleteTask(id) {
    if (!confirm(`Delete task ${id}?`)) return;
    try {
      await fetchJSON(`/api/tasks/${id}`, { method: "DELETE" });
      await loadTasks();
      await loadAnalytics();
      showToast("Task deleted.");
    } catch (err) {
      showToast(err.message);
    }
  }

  async function createTask(e) {
    e.preventDefault();
    clearErrors();

    const title = els.cfTitle.value.trim();
    const category = els.cfCategory.value || "General";
    let priority = parseInt(els.cfPriorityInput.value, 10) || 1;
    const due = els.cfDue.value || null;
    const desc = els.cfDesc.value.trim();

    let ok = true;
    if (!title || title.length < 1 || title.length > 100) {
      showError("cf-title-error", "Title must be 1&ndash;100 characters.");
      ok = false;
    }
    if (desc.length > 300) {
      showError("cf-desc-error", "Description must be 300 characters or less.");
      ok = false;
    }
    if (due) {
      const d = parseDateISO(due);
      if (!d) {
        showError("cf-due-error", "Invalid due date. Use YYYY-MM-DD.");
        ok = false;
      }
    }
    if (priority < 1 || priority > 5) {
      showError("cf-priority-error", "Priority must be between 1 and 5.");
      ok = false;
    }
    if (!ok) return;

    try {
      await fetchJSON("/api/tasks", {
        method: "POST",
        body: JSON.stringify({ title, description: desc, category, priority, due_date: due }),
      });
      els.createForm.reset();
      els.cfPrioritySegs.forEach((s) => s.classList.toggle("seg--active", s.dataset.value === "1"));
      els.cfPriorityInput.value = "1";
      await loadTasks();
      await loadAnalytics();
      showToast("Task saved to JSON.");
    } catch (err) {
      showToast(err.message);
    }
  }

  function showError(id, msg) {
    const el = $(`#${id}`);
    if (el) { el.textContent = msg; el.hidden = false; }
  }
  function clearErrors() {
    $$(".field__error").forEach((el) => { el.hidden = true; });
  }

  async function exportFile(format) {
    try {
      const data = await fetchJSON(`/api/export/${format}`);
      const ext = { md: "md", csv: "csv", txt: "txt" }[format] || format;
      const blob = await (await fetch(`${API_BASE}${data.path}`)).blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tasks.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast(`${format.toUpperCase()} exported.`);
    } catch (err) {
      showToast(err.message);
    }
  }

  async function importCsv() {
    const file = els.csvInput.files[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/api/import-csv`, { method: "POST", body: form });
      if (!res.ok) throw new Error("Import failed");
      const result = await res.json();
      els.importLog.innerHTML = `
        <div class="log-entry log-ok">Imported ${result.imported} rows.</div>
        ${(result.errors || []).map((e) => `<div class="log-entry log-err">Row ${e.row}: ${e.errors ? e.errors.join("; ") : e.error}</div>`).join("")}
      `;
      await loadTasks();
      await loadAnalytics();
      showToast(`Imported ${result.imported} tasks.`);
    } catch (err) {
      showToast(err.message);
    }
  }

  function showToast(msg, duration = 4000) {
    els.toastMsg.textContent = msg;
    els.toast.classList.add("is-visible");
    els.toast.hidden = false;
    clearTimeout(els.toast.timer);
    els.toast.timer = setTimeout(() => {
      els.toast.classList.remove("is-visible");
    }, duration);
  }

  function setupReveal() {
    const items = $$(".reveal");
    if (!("IntersectionObserver" in window)) {
      items.forEach((i) => i.classList.add("is-visible"));
      return;
    }
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -8% 0px" });
    items.forEach((i) => obs.observe(i));
  }

  function init() {
    // Header scroll
    window.addEventListener("scroll", () => {
      els.header.style.borderBottomOpacity = window.scrollY > 20 ? "1" : "1";
    }, { passive: true });

    // Nav new task
    els.navNewTask.addEventListener("click", (e) => {
      e.preventDefault();
      location.hash = "#create";
      setTimeout(() => els.cfTitle.focus(), 300);
    });

    // Filter rows
    els.filterRows.forEach((row) => {
      row.addEventListener("click", () => {
        const f = row.dataset.filter;
        els.filterRows.forEach((r) => r.classList.remove("filter-row--active"));
        row.classList.add("filter-row--active");
        state.filter = f;
        state.page = 1;
        loadTasks();
      });
    });

    // Priority pills
    els.pills.forEach((pill) => {
      pill.addEventListener("click", () => {
        const p = pill.dataset.priority;
        els.pills.forEach((p2) => p2.classList.remove("pill--active"));
        pill.classList.add("pill--active");
        state.priorityFilter = p;
        state.page = 1;
        loadTasks();
      });
    });

    // Pagination
    els.pagPrev.addEventListener("click", () => { if (state.page > 1) { state.page--; loadTasks(); } });
    els.pagNext.addEventListener("click", () => { state.page++; loadTasks(); });

    // Search
    let searchTimer;
    els.wsSearch.addEventListener("input", (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.query = e.target.value.trim();
        state.page = 1;
        loadTasks();
      }, 200);
    });

    // Create form
    els.cfPrioritySegs.forEach((seg) => {
      seg.addEventListener("click", () => {
        els.cfPrioritySegs.forEach((s) => s.classList.remove("seg--active"));
        seg.classList.add("seg--active");
        els.cfPriorityInput.value = seg.dataset.value;
      });
    });
    els.createForm.addEventListener("submit", createTask);

    // Export
    els.exportBtns.forEach((btn) => {
      btn.addEventListener("click", () => exportFile(btn.dataset.format));
    });

    // CSV import
    els.btnPickCsv.addEventListener("click", () => els.csvInput.click());
    els.csvInput.addEventListener("change", importCsv);
    els.dropzone.addEventListener("dragover", (e) => { e.preventDefault(); els.dropzone.style.borderColor = "var(--accent-gold)"; });
    els.dropzone.addEventListener("dragleave", () => { els.dropzone.style.borderColor = ""; });
    els.dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      els.dropzone.style.borderColor = "";
      if (e.dataTransfer.files.length) {
        els.csvInput.files = e.dataTransfer.files;
        importCsv();
      }
    });

    // Refresh metrics
    els.btnRefresh.addEventListener("click", () => {
      els.btnRefresh.textContent = "Refreshing &hellip;";
      loadAnalytics().then(() => { els.btnRefresh.textContent = "Refresh Metrics &rarr;"; showToast("Metrics refreshed."); });
    });

    // Toast close
    els.toastClose.addEventListener("click", () => {
      els.toast.classList.remove("is-visible");
      clearTimeout(els.toast.timer);
    });

    setupReveal();
    loadTasks();
    loadAnalytics();
    setInterval(loadTasks, 30000);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
