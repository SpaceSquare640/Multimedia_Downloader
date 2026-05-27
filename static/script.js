/* =============================================================================
 *  Multimedia Downloader — client-side controller
 *
 *  Responsibilities
 *    • Submit URL batches to POST /api/jobs
 *    • Poll GET /api/jobs every second and re-render the job list
 *    • Stop the active download
 *    • Live language switching without a full page reload
 * ========================================================================== */

(function () {
  "use strict";

  // ── State ────────────────────────────────────────────────────────────────
  let strings = {};                              // current language strings
  let lang    = window.INITIAL_LANG || "en";
  let pollTimer = null;

  // ── DOM refs ─────────────────────────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const urlsEl   = $("#urls");
  const modeEl   = $("#mode");
  const vfmtEl   = $("#video_fmt");
  const afmtEl   = $("#audio_fmt");
  const qualEl   = $("#quality");
  const brEl     = $("#browser");
  const jobsEl   = $("#job-list");
  const submitBt = $("#submit-btn");
  const stopBt   = $("#stop-btn");
  const clearBt  = $("#clear-btn");
  const langSel  = $("#lang-select");
  const vfmtWrap = $("#video-fmt-wrap");
  const afmtWrap = $("#audio-fmt-wrap");

  // ── Translation helpers ──────────────────────────────────────────────────
  function t(key, vars) {
    let s = strings[key] || key;
    if (vars) {
      for (const k in vars) {
        s = s.replace(new RegExp("\\{" + k + "\\}", "g"), vars[k]);
      }
    }
    return s;
  }

  async function loadStrings(code) {
    const r = await fetch("/api/strings/" + code);
    const d = await r.json();
    strings = d.strings;
    lang    = d.lang;
    applyStaticI18n();
  }

  function applyStaticI18n() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    document.title = t("app_title") + " · v3.0";
  }

  // ── Mode switching: show only the relevant format selector ───────────────
  modeEl.addEventListener("change", () => {
    const audio = modeEl.value === "audio";
    vfmtWrap.hidden = audio;
    afmtWrap.hidden = !audio;
  });

  // ── Language switching: persists server-side and re-renders client-side ──
  langSel.addEventListener("change", async () => {
    const code = langSel.value;
    // Persist on server so the next full refresh keeps the choice.
    await fetch("/lang/" + code, { redirect: "manual" }).catch(() => {});
    await loadStrings(code);
    renderJobs(window.LAST_JOBS || []);
  });

  // ── Job submission ───────────────────────────────────────────────────────
  submitBt.addEventListener("click", async () => {
    const urls = urlsEl.value.trim();
    if (!urls) {
      alert(t("msg_no_url_body"));
      return;
    }
    submitBt.disabled = true;
    try {
      const r = await fetch("/api/jobs", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
          urls,
          mode:      modeEl.value,
          video_fmt: vfmtEl.value,
          audio_fmt: afmtEl.value,
          quality:   qualEl.value,
          browser:   brEl.value,
        }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        alert(e.error || "submission failed");
      } else {
        urlsEl.value = "";
        await refreshJobs();
      }
    } finally {
      submitBt.disabled = false;
    }
  });

  stopBt.addEventListener("click", async () => {
    await fetch("/api/stop", { method: "POST" });
  });

  clearBt.addEventListener("click", async () => {
    await fetch("/api/clear", { method: "POST" });
    await refreshJobs();
  });

  // ── Polling + rendering ──────────────────────────────────────────────────
  async function refreshJobs() {
    try {
      const r = await fetch("/api/jobs");
      const d = await r.json();
      window.LAST_JOBS = d.jobs;
      renderJobs(d.jobs);
    } catch (_) { /* ignore transient network blips */ }
  }

  function renderJobs(jobs) {
    if (!jobs || jobs.length === 0) {
      jobsEl.innerHTML =
        '<p class="empty">' + t("web_no_jobs") + "</p>";
      return;
    }
    // Reverse so newest first.
    const html = jobs.slice().reverse().map(jobCard).join("");
    jobsEl.innerHTML = html;
  }

  function jobCard(j) {
    const statusLabel = {
      pending:  t("web_job_pending"),
      running:  t("web_job_running"),
      done:     t("web_job_done"),
      error:    t("web_job_error"),
      stopped:  t("log_stopped_dl"),
    }[j.status] || j.status;

    const pct  = (j.progress || 0).toFixed(1);
    const link = j.filename
      ? '<a href="/files/' + encodeURIComponent(j.filename) +
        '" target="_blank">📥 ' + t("web_download_file") +
        " — " + escapeHtml(j.filename) + "</a>"
      : "";

    const meta = [];
    if (j.status === "running")
      meta.push(t("status_progress",
        { pct, speed: j.speed, eta: j.eta }));
    if (j.error) meta.push("⚠ " + escapeHtml(j.error));
    if (link)    meta.push(link);

    const logHtml = (j.log || []).map(L => {
      // Re-translate the log line using current language if we know the key.
      const msg = strings[L.key]
        ? formatTemplate(strings[L.key], L.fmt)
        : L.msg;
      return '<span class="' + L.level + '">[' + L.ts + "] " +
             escapeHtml(msg) + "</span>";
    }).join("\n");

    return `
      <div class="job">
        <div class="job-head">
          <div class="job-url">${escapeHtml(j.url)}</div>
          <div class="job-status ${j.status}">${escapeHtml(statusLabel)}</div>
        </div>
        <div class="job-progress"><div style="width:${pct}%"></div></div>
        ${meta.length ? '<div class="job-meta">' + meta.join(" · ") + "</div>" : ""}
        ${logHtml ? '<div class="job-log">' + logHtml + "</div>" : ""}
      </div>
    `;
  }

  function formatTemplate(template, vars) {
    let s = template;
    if (vars) {
      for (const k in vars) {
        s = s.replace(new RegExp("\\{" + k + "\\}", "g"), vars[k]);
      }
    }
    return s;
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;",
    }[c]));
  }

  // ── Bootstrap ────────────────────────────────────────────────────────────
  (async function init() {
    await loadStrings(lang);
    await refreshJobs();
    pollTimer = setInterval(refreshJobs, 1000);
  })();
})();
