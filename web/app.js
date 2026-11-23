(() => {
  "use strict";

  const STORAGE_KEY = "ordo.tasks.v1";
  const DEFAULT_CATEGORIES = ["General", "Work", "Personal", "Health", "Learning"];
  const ROMAN = ["", "I", "II", "III", "IV", "V"];
  const PRIORITY_LABELS = ["", "Low", "Minor", "Medium", "High", "Urgent"];
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const DAY_MS = 86400000;
  const RING_LENGTH = 2 * Math.PI * 54;

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

  const els = {
    header: $("#site-header"),
    menuToggle: $("#menu-toggle"),
    mobileMenu: $("#mobile-menu"),
    todayLabel: $("#today-label"),
    ledgerDate: $("#ledger-date"),
    film: $("#hero-film"),
    filmToggle: $("#film-toggle"),
    statOpen: $("#stat-open"),
    statDone: $("#stat-done"),
    statOverdue: $("#stat-overdue"),
    composer: $("#composer"),
    title: $("#task-title"),
    desc: $("#task-desc"),
    category: $("#task-category"),
    due: $("#task-due"),
    composerSubmit: $("#composer-submit"),
    composerCancel: $("#composer-cancel"),
    composerError: $("#composer-error"),
    categoryOptions: $("#category-options"),
    search: $("#search"),
    categoryFilter: $("#category-filter"),
    openGroup: $('[data-group="open"]'),
    doneGroup: $('[data-group="done"]'),
    openList: $("#open-list"),
    doneList: $("#done-list"),
    openCount: $("#open-count"),
    doneCount: $("#done-count"),
    openEmpty: $("#open-empty"),
    doneEmpty: $("#done-empty"),
    doneBody: $("#done-body"),
    toggleDone: $("#toggle-done"),
    ledgerEmpty: $("#ledger-empty"),
    clearFilters: $("#clear-filters"),
    ring: $(".ring"),
    ringFill: $("#ring-fill"),
    completionRate: $("#completion-rate"),
    completionNote: $("#completion-note"),
    railOpen: $("#rail-open"),
    railTotal: $("#rail-total"),
    categoryBars: $("#category-bars"),
    barsEmpty: $("#bars-empty"),
    overdueList: $("#overdue-list"),
    overdueEmpty: $("#overdue-empty"),
    exportMd: $("#export-md"),
    exportCsv: $("#export-csv"),
    loadSamples: $("#load-samples"),
    taskGroups: $("#task-groups"),
    toast: $("#toast"),
    toastMsg: $("#toast-msg"),
    toastAction: $("#toast-action"),
    toastClose: $("#toast-close"),
    toastUse: $(".toast__icon use"),
    live: $("#live"),
  };

  const state = {
    tasks: [],
    filter: "all",
    query: "",
    category: "all",
    editingId: null,
    doneOpen: true,
  };

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let lastCategorySignature = "";
  let lastDeleted = null;
  let storageWarned = false;
  let toastTimer = 0;
  let toastHideTimer = 0;
  let currentDay = "";

  const pad = (value) => String(value).padStart(2, "0");

  function startOfDay(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function isoDate(date) {
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  }

  function todayISO() {
    return isoDate(startOfDay(new Date()));
  }

  function shiftDays(days) {
    const date = startOfDay(new Date());
    date.setDate(date.getDate() + days);
    return isoDate(date);
  }

  function isoFromDaysAgo(days) {
    return new Date(Date.now() - days * DAY_MS).toISOString();
  }

  function isoFromHoursAgo(hours) {
    return new Date(Date.now() - hours * 3600000).toISOString();
  }

  function parseDate(value) {
    if (!value || typeof value !== "string") return null;
    const parts = value.slice(0, 10).split("-").map(Number);
    const [year, month, day] = parts;
    if (!year || !month || !day) return null;
    const date = new Date(year, month - 1, day);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function daysUntil(value) {
    const due = parseDate(value);
    if (!due) return null;
    return Math.round((startOfDay(due) - startOfDay(new Date())) / DAY_MS);
  }

  function isOverdue(task) {
    if (task.completed) return false;
    const days = daysUntil(task.due_date);
    return days !== null && days < 0;
  }

  function shortDate(date) {
    return `${MONTHS[date.getMonth()]} ${date.getDate()}`;
  }

  function dueMeta(task) {
    if (task.completed || !task.due_date) return null;
    const due = parseDate(task.due_date);
    if (!due) return null;
    const days = daysUntil(task.due_date);
    if (days < 0) return { label: `Overdue · ${shortDate(due)}`, tone: "is-overdue" };
    if (days === 0) return { label: "Due today", tone: "is-soon" };
    if (days === 1) return { label: "Due tomorrow", tone: "is-soon" };
    if (days <= 3) return { label: `Due ${shortDate(due)}`, tone: "is-soon" };
    return { label: `Due ${shortDate(due)}`, tone: "" };
  }

  function settledMeta(task) {
    if (!task.completed || !task.completed_at) return "";
    const date = new Date(task.completed_at);
    return Number.isNaN(date.getTime()) ? "" : `Settled ${shortDate(date)}`;
  }

  const ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ENTITIES[char]);
  }

  function slug(value) {
    return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "general";
  }

  function uid() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID().slice(0, 8);
    }
    return Math.random().toString(36).slice(2, 10);
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function normalizeTask(raw) {
    if (!raw || typeof raw !== "object") return null;
    const title = typeof raw.title === "string" ? raw.title.trim() : "";
    if (!title) return null;
    const completed = Boolean(raw.completed);
    return {
      id: typeof raw.id === "string" && raw.id ? raw.id : uid(),
      title,
      description: typeof raw.description === "string" ? raw.description : "",
      category: typeof raw.category === "string" && raw.category.trim() ? raw.category.trim() : "General",
      priority: clamp(Math.round(Number(raw.priority) || 1), 1, 5),
      completed,
      created_at: typeof raw.created_at === "string" ? raw.created_at : new Date().toISOString(),
      completed_at: completed
        ? typeof raw.completed_at === "string" ? raw.completed_at : new Date().toISOString()
        : null,
      due_date: typeof raw.due_date === "string" && parseDate(raw.due_date) ? raw.due_date.slice(0, 10) : null,
    };
  }

  function buildSamples() {
    const drafts = [
      { title: "Complete the project proposal", description: "Draft the Q4 narrative and send it for review.", category: "Work", priority: 5, due: shiftDays(2), createdDaysAgo: 4 },
      { title: "Review the authentication PR", description: "Leave notes on token refresh and session handling.", category: "Work", priority: 4, due: shiftDays(0), createdDaysAgo: 2 },
      { title: "Send the studio invoice", description: "The retainer invoice is a few days overdue.", category: "Work", priority: 4, due: shiftDays(-2), createdDaysAgo: 6 },
      { title: "Buy groceries for the week", description: "Milk, eggs, bread, dark greens, coffee beans.", category: "Personal", priority: 2, due: shiftDays(0), createdDaysAgo: 1 },
      { title: "Book the dentist", description: "Annual checkup — try for a morning slot.", category: "Health", priority: 2, due: shiftDays(3), createdDaysAgo: 3 },
      { title: "Finish chapter five", description: "Clean Code — the chapter on error handling.", category: "Learning", priority: 1, due: shiftDays(6), createdDaysAgo: 5 },
      { title: "Pay the electricity bill", description: "", category: "Personal", priority: 5, due: shiftDays(-4), createdDaysAgo: 8 },
      { title: "Outline the onboarding flow", description: "Three screens, one quiet hand-off.", category: "Work", priority: 3, completed: true, completedDaysAgo: 1, due: shiftDays(1), createdDaysAgo: 6 },
      { title: "Water the monstera", description: "", category: "Personal", priority: 1, completed: true, completedHoursAgo: 4, due: null, createdDaysAgo: 2 },
      { title: "Morning stretch, ten minutes", description: "Before the first coffee.", category: "Health", priority: 1, completed: true, completedDaysAgo: 2, due: shiftDays(-2), createdDaysAgo: 4 },
    ];

    return drafts.map((draft) => {
      const completed = Boolean(draft.completed);
      return {
        id: uid(),
        title: draft.title,
        description: draft.description,
        category: draft.category,
        priority: draft.priority,
        completed,
        created_at: isoFromDaysAgo(draft.createdDaysAgo || 0),
        completed_at: completed
          ? draft.completedHoursAgo
            ? isoFromHoursAgo(draft.completedHoursAgo)
            : isoFromDaysAgo(draft.completedDaysAgo || 0)
          : null,
        due_date: draft.due || null,
      };
    });
  }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tasks));
      return true;
    } catch (error) {
      if (!storageWarned) {
        storageWarned = true;
        showToast("Changes will last this session only — storage is unavailable.", "Dismiss", hideToast, "i-close");
      }
      return false;
    }
  }

  function restoreTasks() {
    let raw = null;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      raw = null;
    }

    if (raw === null) {
      state.tasks = buildSamples();
      persist();
      return;
    }

    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) throw new Error("Invalid ledger");
      const seen = new Set();
      state.tasks = parsed.map(normalizeTask).filter((task) => {
        if (!task || seen.has(task.id)) return false;
        seen.add(task.id);
        return true;
      });
    } catch (error) {
      state.tasks = buildSamples();
      persist();
    }
  }

  function allCategories() {
    const set = new Set(DEFAULT_CATEGORIES);
    state.tasks.forEach((task) => {
      if (task.category) set.add(task.category);
    });
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }

  function syncCategoryOptions() {
    const categories = allCategories();
    const signature = categories.join("\u0000");
    if (signature !== lastCategorySignature) {
      lastCategorySignature = signature;
      els.categoryFilter.innerHTML = [
        '<option value="all">All categories</option>',
        ...categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`),
      ].join("");
      els.categoryOptions.innerHTML = categories
        .map((category) => `<option value="${escapeHtml(category)}"></option>`)
        .join("");
    }
    const match = categories.find((category) => category.toLowerCase() === state.category.toLowerCase());
    if (!match) state.category = "all";
    els.categoryFilter.value = match || "all";
  }

  function taskRow(task) {
    const due = dueMeta(task);
    const settled = settledMeta(task);
    return `
      <li class="task${task.completed ? " is-done" : ""}" data-id="${escapeHtml(task.id)}">
        <button class="task__check" type="button" role="checkbox" aria-checked="${task.completed}" aria-label="${task.completed ? "Reopen" : "Complete"}: ${escapeHtml(task.title)}" data-action="toggle">
          <svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>
        </button>
        <div class="task__body">
          <button class="task__title" type="button" data-action="edit" title="Edit task">${escapeHtml(task.title)}</button>
          ${task.description ? `<p class="task__desc">${escapeHtml(task.description)}</p>` : ""}
          <div class="task__meta">
            <span class="meta-item"><span class="dot cat-${slug(task.category)}"></span>${escapeHtml(task.category)}</span>
            ${due ? `<span class="meta-item meta-item--due ${due.tone}">${escapeHtml(due.label)}</span>` : ""}
            <span class="meta-item meta-item--prio p${task.priority}" title="${PRIORITY_LABELS[task.priority]} priority">Priority ${ROMAN[task.priority]}</span>
            ${settled ? `<span class="meta-item meta-item--settled">${escapeHtml(settled)}</span>` : ""}
          </div>
        </div>
        <div class="task__actions">
          <button class="icon-btn" type="button" data-action="edit" aria-label="Edit: ${escapeHtml(task.title)}">
            <svg class="icon" aria-hidden="true"><use href="#i-pencil"/></svg>
          </button>
          <button class="icon-btn" type="button" data-action="delete" aria-label="Delete: ${escapeHtml(task.title)}">
            <svg class="icon" aria-hidden="true"><use href="#i-trash"/></svg>
          </button>
        </div>
      </li>`;
  }

  function sortOpen(list) {
    return list.slice().sort((a, b) => {
      const overdueDelta = Number(isOverdue(b)) - Number(isOverdue(a));
      if (overdueDelta) return overdueDelta;
      if (b.priority !== a.priority) return b.priority - a.priority;
      const aDue = a.due_date || "9999-12-31";
      const bDue = b.due_date || "9999-12-31";
      if (aDue !== bDue) return aDue < bDue ? -1 : 1;
      return String(b.created_at).localeCompare(String(a.created_at));
    });
  }

  function sortDone(list) {
    return list.slice().sort((a, b) => String(b.completed_at || "").localeCompare(String(a.completed_at || "")));
  }

  function filteredBase() {
    const query = state.query.trim().toLowerCase();
    const category = state.category.toLowerCase();
    return state.tasks.filter((task) => {
      if (state.category !== "all" && task.category.toLowerCase() !== category) return false;
      if (!query) return true;
      return task.title.toLowerCase().includes(query) || task.description.toLowerCase().includes(query);
    });
  }

  function completionNote(rate, total, overdueCount) {
    if (overdueCount > 0) return `${overdueCount} overdue, worth a gentle look.`;
    if (total > 0 && rate === 100) return "Everything, in its place.";
    if (rate >= 70) return "Nearly set.";
    if (rate > 0) return "A few stones remain.";
    return "A ledger at rest.";
  }

  function render() {
    syncCategoryOptions();

    const base = filteredBase();
    const openAll = sortOpen(base.filter((task) => !task.completed));
    const doneAll = sortDone(base.filter((task) => task.completed));
    const overdue = sortOpen(base.filter(isOverdue));
    const counts = {
      all: base.length,
      open: openAll.length,
      done: doneAll.length,
      overdue: overdue.length,
    };

    $$(".seg[data-filter]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.filter === state.filter));
    });
    $$(".count[data-count]").forEach((counter) => {
      counter.textContent = String(counts[counter.dataset.count] ?? 0);
    });

    const hasFilters = state.query.trim() !== "" || state.category !== "all";
    const noMatches = base.length === 0 && hasFilters && state.tasks.length > 0;
    els.ledgerEmpty.hidden = !noMatches;

    const showOpen = state.filter === "all" || state.filter === "open" || state.filter === "overdue";
    const showDone = state.filter === "all" || state.filter === "done";
    const openTasks = state.filter === "overdue" ? overdue : state.filter === "done" ? [] : openAll;
    const doneTasks = state.filter === "done" || state.filter === "all" ? doneAll : [];

    els.openGroup.hidden = noMatches || !showOpen;
    els.doneGroup.hidden = noMatches || !showDone || (state.tasks.length === 0 && state.filter === "all");

    els.openList.innerHTML = openTasks.map(taskRow).join("");
    els.doneList.innerHTML = doneTasks.map(taskRow).join("");
    els.openCount.textContent = String(openTasks.length);
    els.doneCount.textContent = String(doneTasks.length);

    if (openTasks.length) {
      els.openEmpty.hidden = true;
    } else {
      els.openEmpty.hidden = false;
      els.openEmpty.innerHTML = state.filter === "overdue"
        ? "Nothing overdue. <em>Rare and fine.</em>"
        : state.tasks.length === 0
          ? "The ledger is empty. <em>Start with one stone.</em>"
          : "Nothing pressing. <em>Breathe.</em>";
    }

    els.doneEmpty.hidden = doneTasks.length > 0;

    const doneExpanded = state.filter === "done" ? true : state.doneOpen;
    els.doneBody.hidden = !doneExpanded;
    els.toggleDone.hidden = state.filter !== "all";
    els.toggleDone.textContent = state.doneOpen ? "Hide" : "Show";
    els.toggleDone.setAttribute("aria-expanded", String(state.doneOpen));

    const total = state.tasks.length;
    const completed = state.tasks.filter((task) => task.completed).length;
    const openCount = total - completed;
    const overdueCount = state.tasks.filter(isOverdue).length;
    const rate = total ? Math.round((completed / total) * 100) : 0;

    els.statOpen.textContent = String(openCount);
    els.statDone.textContent = String(completed);
    els.statOverdue.textContent = String(overdueCount);
    els.statOverdue.classList.toggle("is-alert", overdueCount > 0);
    els.railOpen.textContent = `${openCount} open`;
    els.railTotal.textContent = `${total} in total`;
    els.completionRate.textContent = String(rate);
    els.ringFill.style.strokeDashoffset = String(RING_LENGTH * (1 - rate / 100));
    els.ring.setAttribute("aria-label", `${rate}% complete`);
    els.completionNote.textContent = completionNote(rate, total, overdueCount);

    const byCategory = new Map();
    state.tasks
      .filter((task) => !task.completed)
      .forEach((task) => {
        byCategory.set(task.category, (byCategory.get(task.category) || 0) + 1);
      });
    const categoryRows = Array.from(byCategory.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    if (categoryRows.length) {
      const max = categoryRows[0][1];
      els.categoryBars.innerHTML = categoryRows
        .map(([name, count]) => `
          <li class="bar">
            <span class="bar__name">${escapeHtml(name)}</span>
            <span class="bar__num">${count}</span>
            <span class="bar__track"><span class="bar__fill" style="width:${Math.max(8, Math.round((count / max) * 100))}%"></span></span>
          </li>`)
        .join("");
      els.categoryBars.hidden = false;
      els.barsEmpty.hidden = true;
    } else {
      els.categoryBars.innerHTML = "";
      els.categoryBars.hidden = true;
      els.barsEmpty.hidden = false;
    }

    const overdueTasks = sortOpen(state.tasks.filter(isOverdue)).slice(0, 3);
    if (overdueTasks.length) {
      els.overdueList.innerHTML = overdueTasks
        .map((task) => {
          const due = parseDate(task.due_date);
          return `<li><button class="mini" type="button" data-goto="${escapeHtml(task.id)}"><span class="mini__title">${escapeHtml(task.title)}</span><span class="mini__due">${due ? shortDate(due) : ""}</span></button></li>`;
        })
        .join("");
      els.overdueList.hidden = false;
      els.overdueEmpty.hidden = true;
    } else {
      els.overdueList.innerHTML = "";
      els.overdueList.hidden = true;
      els.overdueEmpty.hidden = false;
    }
  }

  function renderDates() {
    const now = new Date();
    els.todayLabel.textContent = new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric" }).format(now);
    els.ledgerDate.textContent = new Intl.DateTimeFormat("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" }).format(now);
  }

  function announce(message) {
    els.live.textContent = message;
  }

  function findRow(id) {
    return $$(".task").find((row) => row.dataset.id === id) || null;
  }

  function scrollToComposer() {
    els.composer.scrollIntoView({ behavior: prefersReducedMotion.matches ? "auto" : "smooth", block: "center" });
  }

  function focusComposer() {
    scrollToComposer();
    els.title.focus({ preventScroll: true });
  }

  function showComposerError(message) {
    els.composerError.textContent = message;
    els.composerError.hidden = false;
  }

  function resetComposer() {
    state.editingId = null;
    els.composer.reset();
    els.composer.classList.remove("is-editing");
    els.composerSubmit.textContent = "Add to ledger";
    els.composerCancel.hidden = true;
    els.composerError.hidden = true;
  }

  function submitComposer() {
    const title = els.title.value.trim();
    const description = els.desc.value.trim();
    const categoryValue = els.category.value.trim().replace(/\s+/g, " ");
    const priorityInput = els.composer.querySelector('input[name="priority"]:checked');
    const priority = clamp(Math.round(Number(priorityInput?.value) || 1), 1, 5);
    const due = els.due.value || null;

    if (!title) {
      showComposerError("A task needs a name — even a small one.");
      els.title.focus();
      return;
    }
    if (title.length > 100) {
      showComposerError("Titles can be 100 characters at most.");
      els.title.focus();
      return;
    }
    if (description.length > 500) {
      showComposerError("Notes can be 500 characters at most.");
      els.desc.focus();
      return;
    }
    if (categoryValue.length > 30) {
      showComposerError("Categories can be 30 characters at most.");
      els.category.focus();
      return;
    }
    if (due && !parseDate(due)) {
      showComposerError("That due date doesn’t look right.");
      els.due.focus();
      return;
    }

    const category = categoryValue || "General";

    if (state.editingId) {
      const task = state.tasks.find((item) => item.id === state.editingId);
      if (!task) {
        resetComposer();
        return;
      }
      Object.assign(task, { title, description, category, priority, due_date: due });
      persist();
      render();
      resetComposer();
      announce("Task updated.");
      showToast("Changes saved.", null, null, "i-check");
      const row = findRow(task.id);
      row?.querySelector(".task__title")?.focus({ preventScroll: true });
      return;
    }

    state.tasks.push({
      id: uid(),
      title,
      description,
      category,
      priority,
      completed: false,
      created_at: new Date().toISOString(),
      completed_at: null,
      due_date: due,
    });
    persist();
    render();
    resetComposer();
    announce("Task added to the ledger.");
    els.title.focus({ preventScroll: true });
    showToast("A new stone, placed.", null, null, "i-check");
  }

  function beginEdit(task) {
    state.editingId = task.id;
    els.title.value = task.title;
    els.desc.value = task.description;
    els.category.value = task.category;
    els.due.value = task.due_date || "";
    const radio = els.composer.querySelector(`input[name="priority"][value="${task.priority}"]`);
    if (radio) radio.checked = true;
    els.composer.classList.add("is-editing");
    els.composerSubmit.textContent = "Save changes";
    els.composerCancel.hidden = false;
    els.composerError.hidden = true;
    scrollToComposer();
    els.title.focus({ preventScroll: true });
    els.title.select();
  }

  function toggleTask(task) {
    task.completed = !task.completed;
    task.completed_at = task.completed ? new Date().toISOString() : null;
    persist();
    render();
    const row = findRow(task.id);
    row?.querySelector(".task__check")?.focus({ preventScroll: true });
    announce(`${task.title} ${task.completed ? "settled" : "reopened"}.`);
  }

  function deleteTask(task) {
    const index = state.tasks.indexOf(task);
    if (index === -1) return;
    state.tasks.splice(index, 1);
    lastDeleted = { task, index };
    if (state.editingId === task.id) resetComposer();
    persist();
    render();
    announce("Task deleted.");
    showToast("Task removed from the ledger.", "Undo", () => {
      if (!lastDeleted) return;
      const restored = lastDeleted.task;
      state.tasks.splice(Math.min(lastDeleted.index, state.tasks.length), 0, restored);
      lastDeleted = null;
      persist();
      render();
      announce("Task restored.");
      showToast("Back in the ledger.", null, null, "i-check");
    }, "i-trash");
  }

  function showToast(message, actionLabel = null, action = null, icon = "i-check") {
    window.clearTimeout(toastTimer);
    window.clearTimeout(toastHideTimer);
    els.toastMsg.textContent = message;
    if (els.toastUse) els.toastUse.setAttribute("href", `#${icon}`);
    if (actionLabel && typeof action === "function") {
      els.toastAction.hidden = false;
      els.toastAction.textContent = actionLabel;
      els.toastAction.onclick = () => {
        hideToast();
        action();
      };
    } else {
      els.toastAction.hidden = true;
      els.toastAction.onclick = null;
    }
    els.toast.hidden = false;
    window.requestAnimationFrame(() => els.toast.classList.add("is-visible"));
    toastTimer = window.setTimeout(hideToast, 6000);
  }

  function hideToast() {
    window.clearTimeout(toastTimer);
    els.toast.classList.remove("is-visible");
    window.clearTimeout(toastHideTimer);
    toastHideTimer = window.setTimeout(() => {
      els.toast.hidden = true;
    }, 340);
  }

  function downloadFile(filename, contents, type) {
    const blob = new Blob([contents], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  function buildMarkdown() {
    const now = new Date();
    const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    const pending = sortOpen(state.tasks.filter((task) => !task.completed));
    const done = sortDone(state.tasks.filter((task) => task.completed));
    const cell = (value) => String(value ?? "").replace(/\|/g, "\\|");

    let output = "# Task Report\n\n";
    output += `Generated: ${stamp}\n\n`;
    output += "## Pending Tasks\n\n";
    if (pending.length) {
      output += "| ID | Title | Category | Priority | Due Date |\n";
      output += "|----|-------|----------|----------|----------|\n";
      pending.forEach((task) => {
        output += `| ${task.id} | ${cell(task.title)} | ${cell(task.category)} | ${task.priority} | ${task.due_date || "N/A"} |\n`;
      });
    } else {
      output += "No pending tasks.\n";
    }
    output += "\n## Completed Tasks\n\n";
    if (done.length) {
      output += "| ID | Title | Category | Completed At |\n";
      output += "|----|-------|----------|--------------|\n";
      done.forEach((task) => {
        output += `| ${task.id} | ${cell(task.title)} | ${cell(task.category)} | ${task.completed_at || "N/A"} |\n`;
      });
    } else {
      output += "No completed tasks.\n";
    }
    return output;
  }

  function buildCsv() {
    const columns = ["id", "title", "description", "category", "priority", "completed", "created_at", "completed_at", "due_date"];
    const cell = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const rows = state.tasks.map((task) => columns.map((column) => {
      if (column === "completed") return cell(task.completed ? "True" : "False");
      return cell(task[column]);
    }).join(","));
    return [columns.join(","), ...rows].join("\r\n");
  }

  function loadSamples() {
    const snapshot = state.tasks.map((task) => ({ ...task }));
    const samples = buildSamples();
    state.tasks = state.tasks.concat(samples);
    persist();
    render();
    announce("Sample tasks added.");
    showToast(`${samples.length} sample tasks added.`, "Undo", () => {
      state.tasks = snapshot;
      persist();
      render();
      announce("Sample tasks removed.");
    }, "i-plus");
  }

  function updateFilmButton() {
    const paused = els.film.paused;
    els.filmToggle.setAttribute("aria-label", paused ? "Play background film" : "Pause background film");
    const use = els.filmToggle.querySelector("use");
    if (use) use.setAttribute("href", paused ? "#i-play" : "#i-pause");
  }

  function setupReveal() {
    const items = $$(".reveal");
    if (!("IntersectionObserver" in window) || prefersReducedMotion.matches) {
      items.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    items.forEach((item) => observer.observe(item));
  }

  function onScroll() {
    els.header.classList.toggle("is-scrolled", window.scrollY > 10);
  }

  function setMobileMenu(open) {
    els.menuToggle.setAttribute("aria-expanded", String(open));
    els.menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    els.mobileMenu.hidden = !open;
    els.header.classList.toggle("menu-open", open);
  }

  els.menuToggle.addEventListener("click", () => {
    setMobileMenu(els.mobileMenu.hidden);
  });

  els.mobileMenu.addEventListener("click", (event) => {
    if (event.target.closest("a")) setMobileMenu(false);
  });

  document.addEventListener("click", (event) => {
    if (els.mobileMenu.hidden) return;
    if (event.target.closest("#menu-toggle") || event.target.closest("#mobile-menu")) return;
    setMobileMenu(false);
  });

  $$(".seg[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      if (state.filter === "done") state.doneOpen = true;
      render();
    });
  });

  els.search.addEventListener("input", () => {
    state.query = els.search.value;
    render();
  });

  els.categoryFilter.addEventListener("change", () => {
    state.category = els.categoryFilter.value;
    render();
  });

  els.toggleDone.addEventListener("click", () => {
    state.doneOpen = !state.doneOpen;
    render();
  });

  els.clearFilters.addEventListener("click", () => {
    state.filter = "all";
    state.query = "";
    state.category = "all";
    els.search.value = "";
    render();
    els.search.focus();
  });

  els.taskGroups.addEventListener("click", (event) => {
    const actionElement = event.target.closest("[data-action]");
    if (!actionElement) return;
    const row = actionElement.closest(".task");
    if (!row) return;
    const task = state.tasks.find((item) => item.id === row.dataset.id);
    if (!task) return;
    const action = actionElement.dataset.action;
    if (action === "toggle") toggleTask(task);
    else if (action === "edit") beginEdit(task);
    else if (action === "delete") deleteTask(task);
  });

  els.overdueList.addEventListener("click", (event) => {
    const target = event.target.closest("[data-goto]");
    if (!target) return;
    const task = state.tasks.find((item) => item.id === target.dataset.goto);
    if (!task) return;
    state.filter = "all";
    state.query = "";
    state.category = "all";
    els.search.value = "";
    render();
    const row = findRow(task.id);
    if (!row) return;
    row.scrollIntoView({ behavior: prefersReducedMotion.matches ? "auto" : "smooth", block: "center" });
    row.classList.add("is-flash");
    window.setTimeout(() => row.classList.remove("is-flash"), 1800);
    row.querySelector(".task__title")?.focus({ preventScroll: true });
  });

  els.composer.addEventListener("submit", (event) => {
    event.preventDefault();
    submitComposer();
  });

  els.composer.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      els.composer.requestSubmit();
      return;
    }
    if (event.key === "Escape") {
      event.stopPropagation();
      event.preventDefault();
      if (state.editingId || els.title.value || els.desc.value) {
        resetComposer();
        els.title.focus();
      } else {
        els.title.blur();
      }
    }
  });

  $$("input", els.composer).forEach((input) => {
    input.addEventListener("input", () => {
      if (!els.composerError.hidden) els.composerError.hidden = true;
    });
  });

  els.composerCancel.addEventListener("click", () => {
    resetComposer();
    els.title.focus();
  });

  $$("[data-new-task]").forEach((button) => {
    button.addEventListener("click", () => {
      setMobileMenu(false);
      focusComposer();
    });
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    const isField = target instanceof HTMLElement && target.matches("input, textarea, select, [contenteditable='true']");

    if (event.key === "Escape" && els.menuToggle.getAttribute("aria-expanded") === "true") {
      setMobileMenu(false);
      els.menuToggle.focus();
      return;
    }

    if (event.key === "Escape") {
      if (target === els.search && els.search.value) {
        els.search.value = "";
        state.query = "";
        render();
        return;
      }
      if (isField) target.blur();
      return;
    }

    if (isField) return;

    if (event.key === "n" || event.key === "N") {
      event.preventDefault();
      focusComposer();
    } else if (event.key === "/") {
      event.preventDefault();
      els.search.focus();
    }
  });

  els.filmToggle.addEventListener("click", () => {
    if (els.film.paused) {
      const playPromise = els.film.play();
      if (playPromise && typeof playPromise.catch === "function") playPromise.catch(() => {});
    } else {
      els.film.pause();
    }
    updateFilmButton();
  });

  ["play", "pause", "loadeddata"].forEach((eventName) => {
    els.film.addEventListener(eventName, updateFilmButton);
  });

  els.exportMd.addEventListener("click", () => {
    downloadFile(`todo-report-${todayISO()}.md`, buildMarkdown(), "text/markdown;charset=utf-8");
    showToast("Markdown report exported.", null, null, "i-download");
  });

  els.exportCsv.addEventListener("click", () => {
    downloadFile(`tasks-${todayISO()}.csv`, buildCsv(), "text/csv;charset=utf-8");
    showToast("CSV ledger exported.", null, null, "i-download");
  });

  els.loadSamples.addEventListener("click", loadSamples);
  els.toastClose.addEventListener("click", hideToast);

  window.addEventListener("scroll", onScroll, { passive: true });

  if (typeof prefersReducedMotion.addEventListener === "function") {
    prefersReducedMotion.addEventListener("change", () => {
      if (prefersReducedMotion.matches) els.film.pause();
      updateFilmButton();
    });
  }

  const desktopViewport = window.matchMedia("(min-width: 901px)");
  if (typeof desktopViewport.addEventListener === "function") {
    desktopViewport.addEventListener("change", (event) => {
      if (event.matches) setMobileMenu(false);
    });
  }

  function init() {
    currentDay = todayISO();
    restoreTasks();
    renderDates();
    render();
    setupReveal();
    if (prefersReducedMotion.matches) {
      els.film.removeAttribute("autoplay");
      els.film.pause();
    }
    updateFilmButton();
    onScroll();

    window.setInterval(() => {
      const day = todayISO();
      if (day === currentDay) return;
      currentDay = day;
      renderDates();
      render();
    }, 60000);
  }

  init();
})();
