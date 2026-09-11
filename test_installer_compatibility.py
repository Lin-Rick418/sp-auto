import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parent


class InstallerCompatibilityTests(unittest.TestCase):
    def test_windows_powershell_scripts_are_utf8_with_bom(self) -> None:
        for name in ("install_spiritvale_bot.ps1", "run_spiritvale_bot.ps1"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_single_steam_candidate_remains_an_array(self) -> None:
        source = (ROOT / "install_spiritvale_bot.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("$candidates = @(\n        @(\n", source)
        self.assertIn("if ($candidates.Count -gt 0)", source)

    def test_packaged_job_and_mouse_defaults_match_release_contract(self) -> None:
        bot_config = json.loads(
            (ROOT / "spiritvale_bot_config.json").read_text(encoding="utf-8")
        )
        self.assertEqual(bot_config["job_type"], 1)
        self.assertEqual(
            bot_config["_comment_job_type"],
            "0=未滿64等；1=召喚；2=牧師（F8 每 300-1300ms 短按 Left Shift）",
        )
        self.assertNotIn("always_hold_lshift", bot_config)

        mode_config = json.loads(
            (ROOT / "spiritvale_mode_config.json").read_text(encoding="utf-8")
        )
        self.assertFalse(mode_config["left_click_after_mouse_lock"])

    def test_release_uses_safe_equipment_filter_defaults(self) -> None:
        live_config = json.loads(
            (ROOT / "spiritvale_equipment_filter.json").read_text(
                encoding="utf-8"
            )
        )
        default_config = json.loads(
            (ROOT / "spiritvale_equipment_filter.default.json").read_text(
                encoding="utf-8"
            )
        )
        build_script = (ROOT / "build_release.ps1").read_text(
            encoding="utf-8-sig"
        )

        self.assertTrue(live_config["profiles"])
        self.assertEqual(default_config["schema_version"], 3)
        self.assertFalse(default_config["enabled"])
        self.assertEqual(default_config["profiles"], [])
        self.assertIn("spiritvale_equipment_filter.default.json", build_script)
        self.assertNotIn('    "spiritvale_equipment_filter.json",', build_script)


if __name__ == "__main__":
    unittest.main()
