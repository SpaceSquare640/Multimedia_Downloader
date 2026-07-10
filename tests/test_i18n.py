import unittest

import _path  # noqa: F401
import i18n
from i18n import Translator

# Log keys emitted by the engine — every locale MUST define them so no log
# line ever falls through to a raw key at runtime.
ENGINE_LOG_KEYS = [
    "log_start_batch", "log_stopped_dl", "log_item_downloading", "log_item_done",
    "log_item_error", "log_all_done", "log_cookie_file", "log_cookie_browser",
    "log_convert_start", "log_convert_done", "log_convert_error", "log_no_ffmpeg",
    "log_convert_stopped", "log_all_converted",
    "log_queue_start", "log_queue_stopped", "log_queue_done",
    "log_ai_planning_start", "log_ai_executing", "log_ai_checking",
    "log_ai_plan_ready", "log_ai_plan_error",
]


class LoaderTests(unittest.TestCase):
    def test_three_locales_available(self):
        av = Translator.available()
        self.assertEqual(set(av), {"en", "zh_tw", "zh_cn"})
        self.assertEqual(av["zh_tw"], "繁體中文")

    def test_key_parity_across_locales(self):
        all_strings = i18n._load_all()
        base = set(all_strings["en"])
        for lang, d in all_strings.items():
            self.assertEqual(set(d), base, f"{lang} key set differs from en")

    def test_engine_log_keys_present_everywhere(self):
        all_strings = i18n._load_all()
        for lang, d in all_strings.items():
            for k in ENGINE_LOG_KEYS:
                self.assertIn(k, d, f"{k} missing in {lang}")


class TranslateTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(Translator("en").t("app_title"), "Multimedia Downloader")
        self.assertEqual(Translator("zh_tw").t("app_title"), "多媒體下載器")
        self.assertEqual(Translator("zh_cn").t("tab_video"), "视频格式下载")

    def test_interpolation(self):
        self.assertEqual(
            Translator("en").t("log_item_done", i=1, t=3),
            "[1/3]  ✓  Done",
        )
        self.assertEqual(
            Translator("en").t("log_queue_done", ok=2, fail=1, t=3),
            "✓  Queue done — 2 ok, 1 failed (of 3).",
        )

    def test_unknown_key_returns_key(self):
        self.assertEqual(Translator("en").t("nope_not_a_key"), "nope_not_a_key")

    def test_missing_kwargs_does_not_raise(self):
        # template has {i}/{t} but we pass none -> return raw, no crash
        out = Translator("en").t("log_item_done")
        self.assertIn("{i}", out)

    def test_unknown_lang_falls_back_to_default(self):
        self.assertEqual(Translator("kl_ingon").lang, "en")

    def test_set_language(self):
        tr = Translator("en")
        self.assertTrue(tr.set_language("zh_cn"))
        self.assertEqual(tr.t("app_title"), "多媒体下载器")
        self.assertFalse(tr.set_language("xx"))
        self.assertEqual(tr.lang, "zh_cn")  # unchanged on reject


if __name__ == "__main__":
    unittest.main()
