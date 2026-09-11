import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import spiritvale_paths as paths
from spiritvale_paths import request_probe_load, resolve_ipc_directory


class PortablePathTests(unittest.TestCase):
    def test_prefers_fresh_portable_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            portable = root / "portable"
            legacy = root / "legacy"
            portable.mkdir()
            legacy.mkdir()
            (portable / "spiritvale_memory_state.json").write_text("{}")
            (legacy / "spiritvale_memory_state.json").write_text("{}")
            os.utime(portable / "spiritvale_memory_state.json", (100.0, 100.0))
            os.utime(legacy / "spiritvale_memory_state.json", (100.0, 100.0))

            self.assertEqual(
                resolve_ipc_directory(portable, legacy, now=101.0),
                portable,
            )

    def test_uses_fresh_legacy_state_when_portable_probe_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            portable = root / "portable"
            legacy = root / "legacy"
            portable.mkdir()
            legacy.mkdir()
            state = legacy / "spiritvale_memory_state.json"
            state.write_text("{}")
            os.utime(state, (100.0, 100.0))

            self.assertEqual(
                resolve_ipc_directory(portable, legacy, now=101.0),
                legacy,
            )

    def test_stale_legacy_state_does_not_disable_portable_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            portable = root / "portable"
            legacy = root / "legacy"
            portable.mkdir()
            legacy.mkdir()
            state = legacy / "spiritvale_memory_state.json"
            state.write_text("{}")
            os.utime(state, (100.0, 100.0))

            self.assertEqual(
                resolve_ipc_directory(portable, legacy, now=200.0),
                portable,
            )

    def test_explicit_override_has_highest_priority(self) -> None:
        override = "D:/SpiritValeSharedIpc"
        self.assertEqual(
            resolve_ipc_directory(
                Path("portable"), Path("legacy"), override=override, now=0.0
            ),
            Path(override),
        )

    def test_on_demand_load_request_accepts_matching_loader_ack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.mkdir(exist_ok=True)
            (root / paths.PROBE_LOADER_STATE_FILE_NAME).write_text(
                '{"schema_version":1,"request_id":123,"status":"loaded"}',
                encoding="utf-8",
            )
            with patch.object(paths, "PORTABLE_IPC_DIR", root), patch.object(
                paths, "IPC_DIR", root
            ), patch.object(paths.time, "time_ns", side_effect=[123_000, 124_000]):
                result = request_probe_load(timeout_sec=0.1)
            self.assertEqual(result, "loaded_on_demand")
            request = (
                root / paths.PROBE_LOAD_REQUEST_FILE_NAME
            ).read_text(encoding="utf-8")
            self.assertIn('"request_id":123', request)


if __name__ == "__main__":
    unittest.main()
