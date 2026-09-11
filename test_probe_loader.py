from pathlib import Path
import unittest


ROOT = Path(__file__).parent
LOADER_SOURCE = ROOT / "SpiritValeProbeLoader.cs"
INSTALLER = ROOT / "install_spiritvale_bot.ps1"


class ProbeLoaderTests(unittest.TestCase):
    def test_loader_uses_public_chainloader_only_after_a_fresh_request(self) -> None:
        source = LOADER_SOURCE.read_text(encoding="utf-8")
        self.assertIn("RequestMaxAgeMilliseconds = 15000", source)
        self.assertIn("TryReadFreshRequest", source)
        self.assertIn('FindLoadedType("Game")', source)
        self.assertIn("IL2CPPChainloader.Instance.LoadPlugins", source)
        self.assertIn('"local.spiritvale.positionprobe"', source)

    def test_installer_separates_loader_and_on_demand_probe(self) -> None:
        source = INSTALLER.read_text(encoding="utf-8-sig")
        self.assertIn("BepInEx\\plugins\\SpiritValeProbeLoader", source)
        self.assertIn("BepInEx\\ondemand\\SpiritValePositionProbe", source)
        self.assertIn("Remove-Item -LiteralPath $legacyProbeDll", source)


if __name__ == "__main__":
    unittest.main()
