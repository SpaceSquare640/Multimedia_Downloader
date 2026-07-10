<script lang="ts">
  let { pct, label }: { pct: number; label?: string } = $props();
</script>

<div class="flex flex-col gap-1.5">
  <div
    class="h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800"
    role="progressbar"
    aria-valuenow={Math.round(pct)}
    aria-valuemin={0}
    aria-valuemax={100}
  >
    <div
      class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-[width] duration-200"
      style="width: {Math.min(100, Math.max(0, pct))}%"
    ></div>
  </div>
  {#if label}
    <p class="text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
  {/if}
</div>
