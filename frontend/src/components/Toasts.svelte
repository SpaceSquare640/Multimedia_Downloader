<script lang="ts">
  import { CheckCircle2, XCircle, Info } from "lucide-svelte";
  import { toasts } from "../lib/toast";
</script>

<!-- Sits above the mobile bottom nav; centered on desktop -->
<div class="pointer-events-none fixed inset-x-0 bottom-20 z-50 flex flex-col items-center gap-2 px-4 lg:bottom-6">
  {#each $toasts as t (t.id)}
    <div
      class="pointer-events-auto flex max-w-sm items-center gap-2 rounded-xl border px-3.5 py-2.5
             text-sm shadow-lg backdrop-blur
             {t.kind === 'ok'
               ? 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/90 dark:text-emerald-200'
               : t.kind === 'err'
                 ? 'border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/90 dark:text-red-200'
                 : 'border-zinc-200 bg-white text-zinc-800 dark:border-zinc-700 dark:bg-zinc-900/95 dark:text-zinc-100'}"
      role="status"
    >
      {#if t.kind === "ok"}<CheckCircle2 class="size-4 shrink-0" aria-hidden="true" />
      {:else if t.kind === "err"}<XCircle class="size-4 shrink-0" aria-hidden="true" />
      {:else}<Info class="size-4 shrink-0" aria-hidden="true" />{/if}
      {t.text}
    </div>
  {/each}
</div>
