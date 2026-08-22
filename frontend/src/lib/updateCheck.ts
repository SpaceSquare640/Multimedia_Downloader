/**
 * Best-effort check against the GitHub Releases API for a newer version than
 * the one currently running. Never throws — a network hiccup or rate limit
 * just means no update banner, not a broken app.
 */

const REPO = "SpaceSquare640/Multimedia_Downloader";
const DISMISSED_KEY = "mmdl_update_dismissed";

export type UpdateInfo = { latest: string; url: string };

/** Compares dotted version strings numerically (e.g. "4.3.10" > "4.3.9"). */
function isNewer(latest: string, current: string): boolean {
  const a = latest.split(".").map(Number);
  const b = current.split(".").map(Number);
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = a[i] ?? 0;
    const y = b[i] ?? 0;
    if (x !== y) return x > y;
  }
  return false;
}

/** Returns update info if a newer release exists and hasn't been dismissed, else null. */
export async function checkForUpdate(): Promise<UpdateInfo | null> {
  try {
    const res = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
      headers: { Accept: "application/vnd.github+json" },
    });
    if (!res.ok) return null;
    const data = await res.json();
    const latest = String(data.tag_name ?? "").replace(/^v/, "");
    if (!latest || !isNewer(latest, __APP_VERSION__)) return null;
    if (localStorage.getItem(DISMISSED_KEY) === latest) return null;
    return { latest, url: data.html_url ?? `https://github.com/${REPO}/releases/latest` };
  } catch {
    return null; // offline, rate-limited, blocked network, etc. -- fail silently
  }
}

/** Suppresses the banner for this specific version (shown again on the next release). */
export function dismissUpdate(version: string): void {
  localStorage.setItem(DISMISSED_KEY, version);
}
