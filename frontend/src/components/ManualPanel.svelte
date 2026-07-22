<script lang="ts">
  import { BookOpen, X, Download, RefreshCw, Cookie, ScrollText, Sparkles, Palette, HelpCircle } from "lucide-svelte";
  import { t } from "../store";

  let { onclose }: { onclose: () => void } = $props();

  const tr = $derived($t);

  type SectionIcon = typeof Download;
  const sections: { id: string; icon: SectionIcon; titleKey: string; bodyKey: string }[] = [
    { id: "download", icon: Download, titleKey: "manual_sec_download_title", bodyKey: "manual_sec_download_body" },
    { id: "convert", icon: RefreshCw, titleKey: "manual_sec_convert_title", bodyKey: "manual_sec_convert_body" },
    { id: "cookies", icon: Cookie, titleKey: "manual_sec_cookies_title", bodyKey: "manual_sec_cookies_body" },
    { id: "log", icon: ScrollText, titleKey: "manual_sec_log_title", bodyKey: "manual_sec_log_body" },
    { id: "ai", icon: Sparkles, titleKey: "manual_sec_ai_title", bodyKey: "manual_sec_ai_body" },
    { id: "settings", icon: Palette, titleKey: "manual_sec_settings_title", bodyKey: "manual_sec_settings_body" },
    { id: "help", icon: HelpCircle, titleKey: "manual_sec_help_title", bodyKey: "manual_sec_help_body" },
  ];

  let sectionEls = $state<Record<string, HTMLElement>>({});
  function jumpTo(id: string) {
    sectionEls[id]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
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
  aria-label={tr("manual_title")}
>
  <!-- Mobile drag handle -->
  <div class="grid place-items-center py-2 lg:hidden" aria-hidden="true">
    <div class="h-1 w-10 rounded-full bg-zinc-300 dark:bg-zinc-700"></div>
  </div>

  <header class="flex items-center gap-2 border-b border-zinc-200 px-4 pb-3 lg:pt-4 dark:border-zinc-800">
    <div class="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
      <BookOpen class="size-3.5" aria-hidden="true" />
    </div>
    <strong class="flex-1 text-sm">{tr("manual_title")}</strong>
    <button
      class="grid size-9 place-items-center rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
      onclick={onclose}
      aria-label={tr("btn_cancel")}
    ><X class="size-4" aria-hidden="true" /></button>
  </header>

  <!-- Section nav chips -->
  <div class="flex gap-1.5 overflow-x-auto border-b border-zinc-200 px-4 py-2.5 dark:border-zinc-800">
    {#each sections as s}
      <button
        class="flex shrink-0 items-center gap-1.5 rounded-full border border-zinc-300 px-3 py-1.5
               text-[11px] whitespace-nowrap text-zinc-600 hover:border-indigo-400 hover:text-indigo-500
               dark:border-zinc-700 dark:text-zinc-400 dark:hover:border-indigo-500"
        onclick={() => jumpTo(s.id)}
      >
        <s.icon class="size-3.5" aria-hidden="true" />
        {tr(s.titleKey)}
      </button>
    {/each}
  </div>

  <div class="pb-safe flex-1 space-y-5 overflow-y-auto p-4">
    <p class="text-xs text-zinc-500 dark:text-zinc-400">{tr("manual_intro")}</p>

    {#each sections as s}
      <section bind:this={sectionEls[s.id]} class="scroll-mt-2 space-y-1.5">
        <h3 class="flex items-center gap-2 text-sm font-semibold">
          <s.icon class="size-4 shrink-0 text-indigo-500" aria-hidden="true" />
          {tr(s.titleKey)}
        </h3>
        <p class="text-xs leading-relaxed whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">
          {tr(s.bodyKey)}
        </p>
      </section>
    {/each}
  </div>
</div>
