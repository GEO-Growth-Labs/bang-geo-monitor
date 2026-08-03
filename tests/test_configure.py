from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "bang" / "scripts" / "configure.py"
SPEC = importlib.util.spec_from_file_location("bang_configure", SCRIPT)
assert SPEC and SPEC.loader
CONFIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIGURE)


class ConfigureTests(unittest.TestCase):
    def test_validates_expected_fields(self):
        self.assertEqual(CONFIGURE.validate_config({
            "mcp_server": "wanhu-admin",
            "feishu_parent_url": "https://your-team.feishu.cn/wiki/EXAMPLE_TOKEN",
        }), [])
        self.assertTrue(CONFIGURE.validate_config({
            "mcp_server": "",
            "feishu_parent_url": "http://example.com/file",
        }))
        self.assertIn("mcp_server must be wanhu-admin", CONFIGURE.validate_config({
            "mcp_server": "another-name",
            "feishu_parent_url": "https://your-team.feishu.cn/wiki/EXAMPLE_TOKEN",
        }))

    def test_writes_private_config_and_redacts_show_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            write = subprocess.run([
                sys.executable,
                str(SCRIPT),
                "--config", str(path),
                "--mcp-server", "wanhu-admin",
                "--feishu-parent-url", "https://your-team.feishu.cn/wiki/EXAMPLE_TOKEN",
            ], check=False, capture_output=True, text=True)
            self.assertEqual(write.returncode, 0, write.stderr)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["mcp_server"], "wanhu-admin")

            show = subprocess.run([
                sys.executable, str(SCRIPT), "--config", str(path), "--show"
            ], check=False, capture_output=True, text=True)
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertNotIn("EXAMPLE_TOKEN", show.stdout)
            self.assertIn("https://***/wiki/***", show.stdout)
            self.assertNotIn(str(path), show.stdout)


if __name__ == "__main__":
    unittest.main()
