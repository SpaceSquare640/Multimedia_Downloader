<script lang="ts">
  import {
    Sparkles, X, Settings, Lock, Loader2, RotateCcw,
    Download, RefreshCw, Clock, CheckCircle2, XCircle, SkipForward,
  } from "lucide-svelte";
  import { t } from "../store";
  import { api, IS_MOCK, type AiPlan, type AiTask, type EngineEvent } from "../api";
  import { toast } from "../lib/toast";

  const tr = $derived($t);

  let { onclose }: { onclose: () => void } = $props();

  // Interim storage: the OpenRouter key lives in this device's localStorage
  // only — never committed, never sent anywhere except the OpenRouter API
  // itself. Hardening to the Tauri OS keychain is deferred (documented).
  const KEY_STORAGE = "mmdl_or_api_key";
  const SAVE_PATH_STORAGE = "mmdl_ai_save_path";

  const storedApiKey = localStorage.getItem(KEY_STORAGE) ?? "";
  let apiKey = $state(storedApiKey);
  let defaultSavePath = $state(localStorage.getItem(SAVE_PATH_STORAGE) ?? "");
  let showSettings = $state(!storedApiKey && !IS_MOCK);

  $effect(() => { localStorage.setItem(KEY_STORAGE, apiKey); });
  $effect(() => { localStorage.setItem(SAVE_PATH_STORAGE, defaultSavePath); });

  type Phase = "idle" | "planning" | "review" | "running" | "done" | "error";
  let phase = $state<Phase>("idle");
  let prompt = $state("");
  let plan = $state<AiPlan | null>(null);
  let taskStatus = $state<Record<number, string>>({});
  let errorText = $state("");

  const examples = $derived([tr("ai_example_1"), tr("ai_example_2"), tr("ai_example_3"), tr("ai_example_4")]);

  function reset() {
    phase = "idle"; plan = null; taskStatus = {}; errorText = ""; prompt = "";
  }

  async function getPlan() {
    if (!IS_MOCK && !apiKey.trim()) {
      errorText = tr("ai_no_key"); phase = "error"; showSettings = true; return;
    }
    if (!prompt.trim()) return;
    phase = "planning"; errorText = "";
    try {
      const result = await api.aiPlan(apiKey, prompt, { save_path: defaultSavePath, browser: "none" });
      plan = result;
      taskStatus = Object.fromEntries(result.tasks.map((_, i) => [i, "pending"]));
      phase = "review";
    } catch (e) {
      errorText = String(e instanceof Error ? e.message : e); phase = "error";
    }
  }

  // D4 gate: this is the ONLY place execution starts, and only on user click.
  async function confirmAndRun() {
    if (!plan || plan.tasks.length === 0) return;
    phase = "running";
    const off = api.onEvent((e: EngineEvent) => {
      if (e.type === "task_update") {
        const idx = plan!.tasks.findIndex((t) => t.label === e.label);
        if (idx >= 0) taskStatus = { ...taskStatus, [idx]: e.status };
      }
    });
    try {
      const res = await api.runQueue(plan.tasks);
      const ok = res.tasks.filter((t) => t.status === "done").length;
      toast(tr("log_queue_done", { ok, fail: res.tasks.length - ok, t: res.tasks.length }),
            ok === res.tasks.length ? "ok" : "err");
    } catch (e) {
      errorText = String(e instanceof Error ? e.message : e);
      toast(errorText, "err");
    } finally {
      off(); phase = "done";
    }
  }

  function taskLine(task: AiTask): string {
    return task.kind === "download" ? task.url : `${task.src_path} → ${task.dst_path}`;
  }

  const statusIcons: Record<string, { icon: typeof Clock; cls: string }> = {
    pending: { icon: Clock, cls: "text-zinc-400" },
    running: { icon: Loader2, cls: "animate-spin text-indigo-500" },
    done: { icon: CheckCircle2, cls: "text-emerald-500" },
    error: { icon: XCircle, cls: "text-red-500" },
    skipped: { icon: SkipForward, cls: "text-amber-500" },
  };

  const inputCls =
    "w-full rounded-lg border border-zinc-300 bg-zinc-50 px-3 py-2.5 text-sm " +
    "placeholder:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:placeholder:text-zinc-600";
</script>

<!-- Backdrop (click to close) -->
<div
  class="fixed inset-0 z-40 bg-black/45 backdrop-blur-[2px]"
  onclick={onclose}
  aria-hidden="true"
></div>

<!-- Panel: right sidebar on lg+, bottom sheet (with drag handle + safe area) below -->
<div
  class="fixed z-50 flex flex-col border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900
         inset-x-0 bottom-0 max-h-[85dvh] rounded-t-2xl border-t
         lg:inset-x-auto lg:top-0 lg:right-0 lg:h-full lg:max-h-none lg:w-105 lg:rounded-none lg:border-t-0 lg:border-l"
  role="dialog"
  aria-modal="true"
  aria-label={tr("ai_assistant")}
>
  <!-- Mobile drag handle -->
  <div class="grid place-items-center py-2 lg:hidden" aria-hidden="true">
    <div class="h-1 w-10 rounded-full bg-zinc-300 dark:bg-zinc-700"></div>
  </div>

  <header class="flex items-center gap-2 border-b border-zinc-200 px-4 pb-3 lg:pt-4 dark:border-zinc-800">
    <div class="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
      <Sparkles class="size-3.5" aria-hidden="true" />
    </div>
    <div class="min-w-0 flex-1 leading-tight">
      <strong class="block text-sm">{tr("ai_assistant")}</strong>
      <span class="text-[10px] text-zinc-400 dark:text-zinc-500">{tr("ai_powered_by")}</span>
    </div>
    <button
      class="grid size-9 place-items-center rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
      onclick={() => (showSettings = !showSettings)}
      aria-label={tr("ai_settings")}
      aria-expanded={showSettings}
    ><Settings class="size-4" aria-hidden="true" /></button>
    <button
      class="grid size-9 place-items-center rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
      onclick={onclose}
      aria-label={tr("btn_cancel")}
    ><X class="size-4" aria-hidden="true" /></button>
  </header>

  <div class="pb-safe flex-1 space-y-4 overflow-y-auto p-4">
    {#if IS_MOCK}
      <p class="rounded-lg bg-amber-50 px-3 py-2 text-[11px] text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
        {tr("ai_mock_notice")}
      </p>
    {/if}

    {#if showSettings}
      <div class="space-y-3 rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
        <label class="block">
          <span class="mb-1.5 block text-xs font-medium text-zinc-600 dark:text-zinc-400">{tr("ai_api_key_label")}</span>
          <input type="password" class={inputCls} bind:value={apiKey} placeholder={tr("ai_api_key_placeholder")} />
        </label>
        <p class="text-[10px] text-zinc-400 dark:text-zinc-500">{tr("ai_api_key_hint")}</p>
        <label class="block">
          <span class="mb-1.5 block text-xs font-medium text-zinc-600 dark:text-zinc-400">{tr("ai_default_save_path")}</span>
          <input class={inputCls} bind:value={defaultSavePath} placeholder="C:\Downloads" />
        </label>
      </div>
    {/if}

    {#if phase === "idle" || phase === "error"}
      <!-- Example prompt chips -->
      <div>
        <p class="mb-2 text-xs text-zinc-500 dark:text-zinc-400">{tr("ai_examples_title")}</p>
        <div class="flex flex-wrap gap-1.5">
          {#each examples as ex}
            <button
              class="max-w-full truncate rounded-full border border-zinc-300 px-3 py-1.5 text-[11px]
                     text-zinc-600 hover:border-indigo-400 hover:text-indigo-500
                     dark:border-zinc-700 dark:text-zinc-400 dark:hover:border-indigo-500"
              onclick={() => (prompt = ex)}
            >{ex}</button>
          {/each}
        </div>
      </div>

      <textarea rows="4" class={inputCls + " resize-y"} bind:value={prompt} placeholder={tr("ai_prompt_placeholder")}></textarea>

      {#if phase === "error"}
        <p class="text-xs text-red-500">{errorText}</p>
      {/if}

      <button
        class="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r
               from-indigo-500 to-violet-600 text-sm font-semibold text-white shadow-sm
               transition hover:opacity-95 active:scale-[0.99] disabled:opacity-50"
        onclick={getPlan}
        disabled={!prompt.trim()}
      >
        <Sparkles class="size-4" aria-hidden="true" />{tr("ai_btn_plan")}
      </button>

    {:else if phase === "planning"}
      <div class="grid place-items-center gap-3 py-10 text-zinc-500 dark:text-zinc-400">
        <Loader2 class="size-7 animate-spin text-indigo-500" aria-hidden="true" />
        <p class="text-sm">{tr("ai_planning")}</p>
      </div>

    {:else if plan}
      <p class="text-sm font-semibold">{plan.summary}</p>

      {#if plan.tasks.length === 0}
        <p class="text-xs text-zinc-500 dark:text-zinc-400">{tr("ai_no_tasks")}</p>
      {:else}
        <div>
          <p class="mb-2 text-[11px] font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400">
            {tr("ai_tasks_title")}
          </p>
          <ul class="flex flex-col gap-1.5">
            {#each plan.tasks as task, i}
              {@const s = statusIcons[taskStatus[i] ?? "pending"]}
              <li class="flex items-center gap-2.5 rounded-lg bg-zinc-50 px-3 py-2.5 text-xs dark:bg-zinc-950">
                <s.icon class="size-4 shrink-0 {s.cls}" aria-hidden="true" />
                {#if task.kind === "download"}
                  <Download class="size-3.5 shrink-0 text-zinc-400" aria-hidden="true" />
                {:else}
                  <RefreshCw class="size-3.5 shrink-0 text-zinc-400" aria-hidden="true" />
                {/if}
                <div class="min-w-0 flex-1">
                  <span class="block text-[10px] text-zinc-400">
                    {task.kind === "download" ? tr("ai_task_download") : tr("ai_task_convert")}
                  </span>
                  <span class="block truncate font-mono text-zinc-700 dark:text-zinc-300">{taskLine(task)}</span>
                </div>
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      {#if plan.warnings.length > 0}
        <div>
          <p class="mb-1.5 text-[11px] font-semibold tracking-wide text-amber-500 uppercase">{tr("ai_warnings_title")}</p>
          <ul class="space-y-1 text-[11px] text-amber-600 dark:text-amber-400">
            {#each plan.warnings as w}<li>• {w}</li>{/each}
          </ul>
        </div>
      {/if}

      {#if phase === "review"}
        <!-- Safety gate (D4): nothing has run yet; execution needs this click. -->
        <p class="flex items-start gap-2 rounded-lg bg-zinc-100 px-3 py-2.5 text-[11px] leading-snug text-zinc-600 dark:bg-zinc-950 dark:text-zinc-400">
          <Lock class="mt-0.5 size-3.5 shrink-0 text-emerald-500" aria-hidden="true" />
          {tr("ai_safety_note")}
        </p>
        <div class="flex flex-col gap-2">
          <button
            class="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-emerald-600
                   text-sm font-bold text-white shadow-sm transition hover:bg-emerald-500
                   active:scale-[0.99] disabled:opacity-50"
            onclick={confirmAndRun}
            disabled={plan.tasks.length === 0}
          >
            <CheckCircle2 class="size-4.5" aria-hidden="true" />{tr("btn_confirm")}
          </button>
          <div class="flex gap-2">
            <button
              class="flex min-h-10 flex-1 items-center justify-center gap-1.5 rounded-xl border border-zinc-300
                     text-xs text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              onclick={getPlan}
            ><RotateCcw class="size-3.5" aria-hidden="true" />{tr("ai_regenerate")}</button>
            <button
              class="flex min-h-10 flex-1 items-center justify-center rounded-xl border border-zinc-300
                     text-xs text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              onclick={reset}
            >{tr("btn_cancel")}</button>
          </div>
        </div>
      {:else if phase === "running"}
        <div class="flex items-center justify-center gap-2 py-3 text-sm text-zinc-500 dark:text-zinc-400">
          <Loader2 class="size-4 animate-spin text-indigo-500" aria-hidden="true" />{tr("ai_running")}
        </div>
      {:else if phase === "done"}
        {#if errorText}<p class="text-xs text-red-500">{errorText}</p>{/if}
        <div class="flex gap-2">
          <button
            class="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-500
                   text-sm font-semibold text-white hover:bg-indigo-600"
            onclick={reset}
          ><Sparkles class="size-4" aria-hidden="true" />{tr("ai_new_request")}</button>
          <button
            class="flex min-h-11 items-center justify-center rounded-xl border border-zinc-300 px-4
                   text-sm text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            onclick={onclose}
          >{tr("btn_cancel")}</button>
        </div>
      {/if}
    {/if}
  </div>
</div>
