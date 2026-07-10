<script lang="ts">
  import { Clapperboard, Music, RefreshCw, ScrollText } from "lucide-svelte";
  import { t } from "../store";
  import type { TabId } from "../lib/tabs";

  let { active, onselect }: { active: TabId; onselect: (id: TabId) => void } = $props();

  const tr = $derived($t);

  // Long label (desktop top bar) + short label (mobile bottom nav) per tab.
  const tabs: { id: TabId; icon: typeof Music; long: string; short: string }[] = $derived([
    { id: "video", icon: Clapperboard, long: tr("tab_video"), short: tr("nav_video") },
    { id: "music", icon: Music, long: tr("tab_music"), short: tr("nav_music") },
    { id: "convert", icon: RefreshCw, long: tr("tab_convert"), short: tr("nav_convert") },
    { id: "log", icon: ScrollText, long: tr("tab_log"), short: tr("nav_log") },
  ]);
</script>

<!-- Desktop / tablet (lg+): horizontal pill bar under the header -->
<nav class="hidden justify-center px-4 pt-4 lg:flex" aria-label="Sections">
  <div
    class="flex gap-1 rounded-xl border border-zinc-200 bg-white p-1 dark:border-zinc-800 dark:bg-zinc-900"
    role="tablist"
  >
    {#each tabs as tab}
      <button
        role="tab"
        aria-selected={active === tab.id}
        class="flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition-colors
               {active === tab.id
                 ? 'bg-indigo-500 font-medium text-white shadow-sm'
                 : 'text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'}"
        onclick={() => onselect(tab.id)}
      >
        <tab.icon class="size-4" aria-hidden="true" />
        {tab.long}
      </button>
    {/each}
  </div>
</nav>

<!-- Mobile (<lg): fixed bottom navigation, safe-area aware, ≥44px touch targets -->
<nav
  class="pb-safe fixed inset-x-0 bottom-0 z-30 border-t border-zinc-200 bg-white/95
         backdrop-blur lg:hidden dark:border-zinc-800 dark:bg-zinc-950/95"
  aria-label="Sections"
>
  <div class="grid grid-cols-4" role="tablist">
    {#each tabs as tab}
      <button
        role="tab"
        aria-selected={active === tab.id}
        class="flex min-h-14 flex-col items-center justify-center gap-0.5 text-[10px]
               {active === tab.id
                 ? 'font-semibold text-indigo-500'
                 : 'text-zinc-500 dark:text-zinc-400'}"
        onclick={() => onselect(tab.id)}
      >
        <tab.icon class="size-5" aria-hidden="true" />
        {tab.short}
      </button>
    {/each}
  </div>
</nav>
