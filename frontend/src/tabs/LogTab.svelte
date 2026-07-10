<script lang="ts">
  import { Search, Trash2, FileDown, ArrowDownToLine } from "lucide-svelte";
  import { t, logs, clearLogs } from "../store";

  const tr = $derived($t);

  let search = $state("");
  let level = $state<"all" | "info" | "ok" | "warn" | "err">("all");
  let autoScroll = $state(true);
  let consoleEl = $state<HTMLDivElement | null>(null);

  const filtered = $derived(
    $logs.filter(
      (l) =>
        (level === "all" || l.level === level) &&
        (!search || l.text.toLowerCase().includes(search.toLowerCase())),
    ),
  );

  // Follow the tail whenever new lines arrive (unless the user opted out).
  $effect(() => {
    filtered.length;
    if (autoScroll && consoleEl) consoleEl.scrollTop = consoleEl.scrollHeight;
  });

  function exportLog() {
    const text = $logs.map((l) => `[${l.ts}] [${l.level.toUpperCase().padEnd(4)}] ${l.text}`).join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "mmdl_log.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  const levelColor: Record<string, string> = {
    ok: "text-emerald-500",
    warn: "text-amber-500",
    err: "text-red-500",
    info: "text-zinc-500 dark:text-zinc-400",
  };
  const btnCls =
    "flex h-9 items-center gap-1.5 rounded-lg border border-zinc-300 px-2.5 text-xs " +
    "text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800";
</script>

<div class="flex h-full flex-col gap-3">
  <!-- Toolbar -->
  <div class="flex flex-wrap items-center gap-2">
    <div class="relative min-w-40 flex-1">
      <Search class="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-zinc-400" aria-hidden="true" />
      <input
        class="h-9 w-full rounded-lg border border-zinc-300 bg-white ps-8 pe-3 text-xs
               dark:border-zinc-700 dark:bg-zinc-900"
        bind:value={search}
        placeholder={tr("log_search")}
        aria-label={tr("log_search")}
      />
    </div>
    <select
      class="h-9 rounded-lg border border-zinc-300 bg-white px-2 text-xs dark:border-zinc-700 dark:bg-zinc-900"
      bind:value={level}
      aria-label="Level"
    >
      <option value="all">{tr("log_level_all")}</option>
      <option value="info">info</option>
      <option value="ok">ok</option>
      <option value="warn">warn</option>
      <option value="err">err</option>
    </select>
    <button
      class="{btnCls} {autoScroll ? 'border-indigo-400 text-indigo-500 dark:border-indigo-600' : ''}"
      onclick={() => (autoScroll = !autoScroll)}
      aria-pressed={autoScroll}
    >
      <ArrowDownToLine class="size-3.5" aria-hidden="true" />{tr("log_autoscroll")}
    </button>
    <button class={btnCls} onclick={exportLog} disabled={$logs.length === 0}>
      <FileDown class="size-3.5" aria-hidden="true" />{tr("log_export")}
    </button>
    <button class={btnCls} onclick={clearLogs} disabled={$logs.length === 0}>
      <Trash2 class="size-3.5" aria-hidden="true" />{tr("btn_clear")}
    </button>
  </div>

  <!-- Console -->
  <div
    bind:this={consoleEl}
    class="min-h-72 flex-1 overflow-auto rounded-xl border border-zinc-200 bg-white p-3
           font-mono text-xs leading-relaxed dark:border-zinc-800 dark:bg-zinc-950"
  >
    {#if filtered.length === 0}
      <p class="p-4 text-center text-zinc-400 dark:text-zinc-600">{tr("web_no_jobs")}</p>
    {:else}
      {#each filtered as line (line.seq)}
        <div class="flex gap-2 whitespace-pre-wrap">
          <span class="shrink-0 text-zinc-300 select-none dark:text-zinc-600">{line.ts}</span>
          <span class="{levelColor[line.level] ?? levelColor.info} break-all">{line.text}</span>
        </div>
      {/each}
    {/if}
  </div>
</div>
