<script lang="ts">
  import { onMount } from "svelte";
  import { Play, Square, Link2, Clock, Loader2, CheckCircle2, XCircle } from "lucide-svelte";
  import Card from "../components/Card.svelte";
  import ProgressBar from "../components/ProgressBar.svelte";
  import { api, type Formats, type EngineEvent } from "../api";
  import { t, progress, busy } from "../store";
  import { toast } from "../lib/toast";

  let { mode, formats }: { mode: "video" | "audio"; formats: Formats | null } = $props();

  const tr = $derived($t);

  let urls = $state("");
  let videoFmt = $state("mp4");
  let audioFmt = $state("mp3");
  let quality = $state("best");
  // NOTE: bitrate is UI-only for now — the engine currently fixes audio at
  // 192 kbps (V3.0 parity). TODO(engine): pass preferredquality through.
  let bitrate = $state("192");
  let savePath = $state("");
  let browser = $state("none");

  // Per-batch item list so the user sees each URL's live status.
  type Item = { url: string; status: "pending" | "running" | "done" | "error" };
  let items = $state<Item[]>([]);

  onMount(() =>
    api.onEvent((e: EngineEvent) => {
      if (e.type === "item_start" && items[e.index - 1]) {
        items[e.index - 1].status = "running";
      } else if (e.type === "log" && e.fmt && typeof e.fmt.i === "number") {
        const idx = (e.fmt.i as number) - 1;
        if (!items[idx]) return;
        if (e.key === "log_item_done") items[idx].status = "done";
        else if (e.key === "log_item_error") items[idx].status = "error";
      }
    }),
  );

  const urlList = $derived(urls.split("\n").map((u) => u.trim()).filter(Boolean));

  async function start() {
    if (urlList.length === 0) return;
    items = urlList.map((url) => ({ url, status: "pending" }));
    busy.set(true);
    progress.set(null);
    try {
      await api.startDownload({
        urls: urlList, mode,
        video_fmt: videoFmt, audio_fmt: audioFmt,
        quality, save_path: savePath, browser,
      });
      toast(tr("status_all_done_dl", { t: urlList.length }), "ok");
    } catch (e) {
      toast(String(e instanceof Error ? e.message : e), "err");
    } finally {
      busy.set(false);
    }
  }
  function stop() { api.stop(); busy.set(false); }

  const inputCls =
    "w-full rounded-lg border border-zinc-300 bg-zinc-50 px-3 py-2.5 text-sm " +
    "placeholder:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-950 dark:placeholder:text-zinc-600";
  const labelCls = "mb-1.5 block text-xs font-medium text-zinc-600 dark:text-zinc-400";
</script>

<div class="flex flex-col gap-4">
  <Card title={tr("sec_urls")}>
    <textarea
      rows="4"
      class={inputCls + " resize-y font-mono text-[13px]"}
      bind:value={urls}
      placeholder={tr("web_url_placeholder")}
    ></textarea>
    <p class="mt-2 flex items-center gap-1.5 text-[11px] text-zinc-400 dark:text-zinc-500">
      <Link2 class="size-3 shrink-0" aria-hidden="true" />{tr("urls_caption")}
    </p>
  </Card>

  <Card title={tr("sec_format")}>
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {#if mode === "video"}
        <label>
          <span class={labelCls}>{tr("lbl_video_fmt")}</span>
          <select class={inputCls} bind:value={videoFmt}>
            {#each formats?.video ?? [] as f}<option>{f}</option>{/each}
          </select>
        </label>
        <label>
          <span class={labelCls}>{tr("lbl_quality")}</span>
          <select class={inputCls} bind:value={quality}>
            {#each formats?.quality ?? [] as q}<option>{q}</option>{/each}
          </select>
        </label>
      {:else}
        <label>
          <span class={labelCls}>{tr("lbl_audio_fmt")}</span>
          <select class={inputCls} bind:value={audioFmt}>
            {#each formats?.audio ?? [] as f}<option>{f}</option>{/each}
          </select>
        </label>
        <label>
          <span class={labelCls}>{tr("lbl_bitrate")}</span>
          <select class={inputCls} bind:value={bitrate}>
            <option value="192">192 kbps</option>
            <option value="320">320 kbps</option>
            <option value="128">128 kbps</option>
          </select>
        </label>
      {/if}
      <label>
        <span class={labelCls}>{tr("sec_save")}</span>
        <input class={inputCls} bind:value={savePath} placeholder="C:\Downloads" />
      </label>
    </div>
  </Card>

  <Card title={tr("sec_cookie")}>
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <label>
        <span class={labelCls}>{tr("cookie_m1")}</span>
        <select class={inputCls} bind:value={browser}>
          {#each formats?.browsers ?? [] as b}<option>{b}</option>{/each}
        </select>
      </label>
      <p class="self-end pb-1 text-[11px] leading-snug text-zinc-400 dark:text-zinc-500">
        {tr("cookie_warning")}
      </p>
    </div>
  </Card>

  {#if $progress}
    <Card>
      <ProgressBar
        pct={$progress.pct}
        label={tr("status_progress", { pct: $progress.pct, speed: $progress.speed, eta: $progress.eta })}
      />
    </Card>
  {/if}

  <!-- Actions -->
  <div class="flex gap-2.5">
    <button
      class="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-500
             text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-600
             active:scale-[0.99] disabled:opacity-50 sm:flex-none sm:px-6"
      onclick={start}
      disabled={$busy || urlList.length === 0}
    >
      <Play class="size-4" aria-hidden="true" />{tr("btn_start_download")}
    </button>
    <button
      class="flex min-h-11 items-center justify-center gap-2 rounded-xl border border-zinc-300
             px-4 text-sm text-zinc-600 hover:bg-zinc-100 disabled:opacity-40
             dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
      onclick={stop}
      disabled={!$busy}
    >
      <Square class="size-3.5" aria-hidden="true" />{tr("btn_stop")}
    </button>
  </div>

  <!-- Per-item batch status -->
  {#if items.length > 0}
    <Card title={tr("ai_tasks_title")}>
      <ul class="flex flex-col gap-1.5">
        {#each items as item}
          <li class="flex items-center gap-2.5 rounded-lg bg-zinc-50 px-3 py-2 text-xs dark:bg-zinc-950">
            {#if item.status === "pending"}<Clock class="size-3.5 shrink-0 text-zinc-400" aria-hidden="true" />
            {:else if item.status === "running"}<Loader2 class="size-3.5 shrink-0 animate-spin text-indigo-500" aria-hidden="true" />
            {:else if item.status === "done"}<CheckCircle2 class="size-3.5 shrink-0 text-emerald-500" aria-hidden="true" />
            {:else}<XCircle class="size-3.5 shrink-0 text-red-500" aria-hidden="true" />{/if}
            <span class="truncate font-mono text-zinc-700 dark:text-zinc-300">{item.url}</span>
          </li>
        {/each}
      </ul>
    </Card>
  {/if}
</div>
