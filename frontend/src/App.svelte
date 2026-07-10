<script lang="ts">
  import { onMount } from "svelte";
  import { Sparkles } from "lucide-svelte";
  import { api, IS_MOCK, type Formats, type EngineEvent } from "./api";
  import { lang, t, pushLog, progress, busy } from "./store";
  import { Translator } from "./i18n";
  import Header from "./components/Header.svelte";
  import TabBar from "./components/TabBar.svelte";
  import type { TabId } from "./lib/tabs";
  import Toasts from "./components/Toasts.svelte";
  import DownloadTab from "./tabs/DownloadTab.svelte";
  import ConvertTab from "./tabs/ConvertTab.svelte";
  import LogTab from "./tabs/LogTab.svelte";
  import AiPanel from "./ai/AiPanel.svelte";

  let active = $state<TabId>("video");
  let showAi = $state(false);
  let formats = $state<Formats | null>(null);
  let langNames = $state<Record<string, string>>({});

  const tr = $derived($t);

  onMount(() => {
    api.getFormats().then((f) => (formats = f));
    api.getLocales().then((n) => (langNames = n));

    // Single global subscription: engine emits i18n KEYS; we translate here
    // with the language active at the moment the line arrives.
    const offEvents = api.onEvent((e: EngineEvent) => {
      if (e.type === "log") {
        const translate = new Translator($lang);
        pushLog(e.level, translate.t(e.key, e.fmt));
      } else if (e.type === "progress") {
        progress.set({ pct: e.pct, speed: e.speed, eta: e.eta });
        if (e.pct >= 100) busy.set(false);
      } else if (e.type === "item_start") {
        progress.set({ pct: 0, speed: "--", eta: "--" });
      }
    });

    // Ctrl/Cmd+K toggles the AI assistant (desktop power-user shortcut).
    const onKey = (ev: KeyboardEvent) => {
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "k") {
        ev.preventDefault();
        showAi = !showAi;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      offEvents();
      window.removeEventListener("keydown", onKey);
    };
  });
</script>

<div class="flex min-h-dvh flex-col">
  <Header {langNames} onToggleAi={() => (showAi = !showAi)} />

  {#if IS_MOCK}
    <div class="bg-amber-100 py-1 text-center text-[11px] text-amber-800 dark:bg-amber-950/60 dark:text-amber-400">
      {tr("mock_banner")}
    </div>
  {/if}

  <TabBar {active} onselect={(id) => (active = id)} />

  <!-- pb-24 on mobile clears the fixed bottom nav + FAB -->
  <main class="mx-auto w-full max-w-5xl flex-1 px-4 pt-4 pb-24 lg:pb-8">
    {#if active === "video"}
      <DownloadTab mode="video" {formats} />
    {:else if active === "music"}
      <DownloadTab mode="audio" {formats} />
    {:else if active === "convert"}
      <ConvertTab {formats} />
    {:else}
      <LogTab />
    {/if}
  </main>

  <!-- Mobile FAB for the AI assistant (header button is lg+ only) -->
  {#if !showAi}
    <button
      class="fixed right-4 bottom-20 z-30 flex size-14 items-center justify-center rounded-full
             bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg
             shadow-indigo-500/30 transition-transform active:scale-90 lg:hidden"
      style="margin-bottom: env(safe-area-inset-bottom)"
      onclick={() => (showAi = true)}
      aria-label={tr("ai_assistant")}
    >
      <Sparkles class="size-6" aria-hidden="true" />
    </button>
  {/if}

  {#if showAi}
    <AiPanel onclose={() => (showAi = false)} />
  {/if}

  <Toasts />
</div>
