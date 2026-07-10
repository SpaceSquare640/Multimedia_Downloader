/**
 * i18n loader for the V4.0 frontend.
 *
 * Loads the same `locales/*.json` files the Python side uses, so both stay in
 * lockstep. Fallback chain matches V3.0: requested lang -> English -> raw key.
 * Interpolation uses `{token}` placeholders (same style as the JSON), e.g.
 *   t("log_item_done", { i: 1, t: 3 })  ->  "[1/3]  ✓  Done"
 *
 * The locale JSON is imported at build time by Vite (`import.meta.glob`), so
 * no runtime fetch / network is involved.
 */

export type Lang = "en" | "zh_tw" | "zh_cn";
export const DEFAULT_LANG: Lang = "en";
export const SUPPORTED: Lang[] = ["en", "zh_tw", "zh_cn"];

type Dict = Record<string, string>;
type Meta = { lang: string; name: string };
type LocaleDoc = Dict & { _meta?: Meta };

// Eagerly bundle every locale file at ../../../locales/*.json.
// (Vite resolves this glob at build time; keys are file paths.)
const modules = import.meta.glob<LocaleDoc>("../../../locales/*.json", {
  eager: true,
  import: "default",
});

const STRINGS: Record<string, Dict> = {};
const NAMES: Record<string, string> = {};

for (const path in modules) {
  const doc = modules[path];
  const meta = doc._meta;
  const code = meta?.lang ?? path.replace(/^.*\/(.+)\.json$/, "$1");
  const { _meta, ...rest } = doc;
  STRINGS[code] = rest as Dict;
  NAMES[code] = meta?.name ?? code;
}

function interpolate(template: string, params?: Record<string, unknown>): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (m, key) =>
    key in params ? String(params[key]) : m,
  );
}

export class Translator {
  lang: Lang;

  constructor(lang: Lang = DEFAULT_LANG) {
    this.lang = lang in STRINGS ? lang : DEFAULT_LANG;
  }

  /** Translate `key`, applying `{token}` interpolation from `params`. */
  t(key: string, params?: Record<string, unknown>): string {
    const s =
      STRINGS[this.lang]?.[key] ??
      STRINGS[DEFAULT_LANG]?.[key] ??
      key;
    return interpolate(s, params);
  }

  /** Switch active language. Returns true if the language is installed. */
  setLanguage(lang: Lang): boolean {
    if (lang in STRINGS) {
      this.lang = lang;
      return true;
    }
    return false;
  }

  /** `{ code: displayName }` for every installed locale. */
  static available(): Record<string, string> {
    return { ...NAMES };
  }
}
