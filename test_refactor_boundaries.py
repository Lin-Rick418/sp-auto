"""Verify module independence and the release's actual runtime imports."""
import ast
import importlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).parent
PURE_MODULES = (
    'spiritvale_models', 'spiritvale_config', 'spiritvale_navigation',
    'spiritvale_snapshot', 'spiritvale_loot', 'spiritvale_upkeep', 'spiritvale_earnings',
)


class RefactorBoundaryTests(unittest.TestCase):
    def test_decision_modules_import_without_windows_or_site_packages(self) -> None:
        result = subprocess.run(
            [sys.executable, '-S', '-c', '; '.join(f'import {name}' for name in PURE_MODULES)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_old_entry_point_exports_the_same_model_and_decision_objects(self) -> None:
        import spiritvale_red_dot_bot as bot
        for module_name, symbol in (
            ('spiritvale_models', 'MemorySnapshot'),
            ('spiritvale_config', 'BotConfig'),
            ('spiritvale_loot', 'select_memory_loot'),
            ('spiritvale_navigation', 'request_path_matches'),
        ):
            with self.subTest(symbol=symbol):
                self.assertIs(getattr(bot, symbol), getattr(importlib.import_module(module_name), symbol))

    def test_release_contains_transitive_local_imports_and_can_start_help(self) -> None:
        script = (ROOT / 'build_release.ps1').read_text(encoding='utf-8-sig')
        manifest = script.split('$files = @(', 1)[1].split('\n)', 1)[0]
        files = re.findall(r'"([^"\n]+)"', manifest)
        self.assertIn('spiritvale_red_dot_bot.py', files)
        for filename in files:
            if not filename.endswith('.py'):
                continue
            tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                modules = (
                    [alias.name for alias in node.names] if isinstance(node, ast.Import)
                    else [node.module] if isinstance(node, ast.ImportFrom) else []
                )
                for module in modules:
                    if module and module.startswith('spiritvale_'):
                        self.assertIn(module + '.py', files, f'{filename} requires {module}')
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            for filename in files:
                shutil.copy2(ROOT / filename, stage / filename)
            # Isolated mode excludes the script directory as well as PYTHONPATH.
            # Explicitly add only the staged directory, never the checkout.
            result = subprocess.run(
                [sys.executable, '-I', '-c',
                 'import runpy,sys; sys.path.insert(0,sys.argv[1]); '
                 'sys.argv=[sys.argv[1]+"/spiritvale_red_dot_bot.py","--help"]; '
                 'runpy.run_path(sys.argv[0],run_name="__main__")', str(stage)],
                cwd=stage, capture_output=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            self.assertIn(b'--run', result.stdout)


if __name__ == '__main__':
    unittest.main()
