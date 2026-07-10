<script lang="ts">
  import { Download, Sun, Moon, Monitor, Sparkles } from "lucide-svelte";
  import { lang, t } from "../store";
  import { theme, cycleTheme } from "../lib/theme";
  import { SUPPORTED, type Lang } from "../i18n";

  let {
    langNames,
    onToggleAi,
  }: { langNames: Record<string, string>; onToggleAi: () => void } = $props();

  const tr = $derived($t);
  // Icon reflects the CURRENT mode; clicking cycles light → dark → system.
  const ThemeIcon = $derived($theme === "light" ? Sun : $theme === "dark" ? Moon : Monitor);
  const themeLabel = $derived(
    $theme === "light" ? tr("theme_light") : $theme === "dark" ? tr("theme_dark") : tr("theme_system"),
  );
</script>

<header
  class="pt-safe sticky top-0 z-30 border-b border-zinc-200 bg-white/85 backdrop-blur
         dark:border-zinc-800 dark:bg-zinc-950/85"
>
  <div class="mx-auto flex h-14 max-w-5xl items-center gap-3 px-4">
    <!-- Brand -->
    <div class="flex min-w-0 items-center gap-2.5">
      <div class="grid size-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-sm">
        <Download class="size-4.5" aria-hidden="true" />
      </div>
      <div class="min-w-0 leading-tight">
        <h1 class="truncate text-sm font-semibold">{tr("app_title")}</h1>
        <p class="hidden truncate text-[10px] text-zinc-500 sm:block dark:text-zinc-400">
          {tr("app_subtitle")}
        </p>
      </div>
    </div>

    <div class="ms-auto flex items-center gap-1.5">
      <!-- Language -->
      <select
        aria-label={tr("language")}
        class="h-9 rounded-lg border border-zinc-300 bg-white px-2 text-xs
               dark:border-zinc-700 dark:bg-zinc-900"
        value={$lang}
        onchange={(e) => lang.set((e.currentTarget as HTMLSelectElement).value as Lang)}
      >
        {#each SUPPORTED as code}
          <option value={code}>{langNames[code] ?? code}</option>
        {/each}
      </select>

      <!-- Theme cycle -->
      <button
        class="grid size-9 place-items-center rounded-lg border border-zinc-300 bg-white
               text-zinc-600 hover:bg-zinc-100
               dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
        onclick={cycleTheme}
        aria-label={`${tr("theme_toggle")}: ${themeLabel}`}
        title={`${tr("theme_toggle")}: ${themeLabel}`}
      >
        <ThemeIcon class="size-4" aria-hidden="true" />
      </button>

      <!-- AI Assistant — hidden on mobile (the FAB covers it there) -->
      <button
        class="hidden h-9 items-center gap-1.5 rounded-lg bg-gradient-to-r from-indigo-500
               to-violet-600 px-3 text-xs font-semibold text-white shadow-sm
               transition-transform hover:scale-[1.03] active:scale-95 lg:flex"
        onclick={onToggleAi}
        title="Ctrl/Cmd + K"
      >
        <Sparkles class="size-4" aria-hidden="true" />
        {tr("ai_assistant")}
        <kbd class="ms-1 rounded bg-white/20 px-1 font-mono text-[9px] font-normal">⌘K</kbd>
      </button>
    </div>
  </div>
</header>
