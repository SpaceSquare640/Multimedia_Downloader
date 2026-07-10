<script lang="ts">
  import type { Snippet } from "svelte";
  let { title, children }: { title?: string; children: Snippet } = $props();
</script>

<section
  class="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
>
  {#if title}
    <h2 class="mb-3 text-[11px] font-semibold tracking-wide text-zinc-500 uppercase dark:text-zinc-400">
      {title}
    </h2>
  {/if}
  {@render children()}
</section>
