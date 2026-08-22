<script lang="ts">
  import { onMount } from "svelte";
  import { X } from "lucide-svelte";
  import { t } from "../store";
  import { openExternal } from "../api";
  import { checkForUpdate, dismissUpdate, type UpdateInfo } from "../lib/updateCheck";

  const tr = $derived($t);
  let info = $state<UpdateInfo | null>(null);

  onMount(() => {
    checkForUpdate().then((r) => (info = r));
  });

  function dismiss() {
    if (info) dismissUpdate(info.latest);
    info = null;
  }
</script>

{#if info}
  <div
    class="flex items-center justify-center gap-3 bg-indigo-100 py-1.5 text-center text-[11px]
           text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
  >
    <span>{tr("update_available", { v: info.latest, cur: __APP_VERSION__ })}</span>
    <button class="font-semibold underline underline-offset-2" onclick={() => openExternal(info!.url)}>
      {tr("update_view")}
    </button>
    <button
      class="grid size-4 place-items-center rounded hover:bg-indigo-200 dark:hover:bg-indigo-900"
      onclick={dismiss}
      aria-label={tr("update_dismiss")}
      title={tr("update_dismiss")}
    >
      <X class="size-3" aria-hidden="true" />
    </button>
  </div>
{/if}
