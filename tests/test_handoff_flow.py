"""插件 Handoff 流程测试。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent.parent
HOOKS_DIR = ROOT / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import handoff

SESSION_START = HOOKS_DIR / "session-start.py"
PRE_COMPACT = HOOKS_DIR / "pre-compact.py"


class TemporaryProject(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / ".claude").mkdir()
        self.env = os.environ.copy()
        self.env["CLAUDE_PROJECT_DIR"] = str(self.root)
        self.env["CLAUDE_SESSION_CONTINUITY_HANDLER"] = "project"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook(self, script: Path, data: dict, extra_env: dict | None = None):
        env = self.env.copy()
        if extra_env:
            env.update(extra_env)
        process = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(data, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=10,
        )
        return process, json.loads(process.stdout) if process.stdout.strip() else None

    def write_handoff(self, secret: str = "NEVER_INJECT_THIS_BODY") -> Path:
        path = self.root / ".claude" / "HANDOFF.md"
        path.write_text(
            "---\n"
            "type: handoff\n"
            "source: save-state\n"
            "quality: curated\n"
            "updated_at: \"2026-07-14T12:00:00\"\n"
            "trigger: manual-save-state\n"
            "---\n\n"
            "# Handoff — 测试\n\n"
            "## 完成的工作\n"
            f"{secret}\n",
            encoding="utf-8",
        )
        return path


class TestHandoffFlow(TemporaryProject):
    def test_session_start_never_injects_body_and_prompts_once(self):
        target = self.write_handoff()
        data = {"session_id": "plugin-session", "source": "clear", "cwd": str(self.root)}
        process, first = self.run_hook(SESSION_START, data)
        self.assertEqual(process.returncode, 0, process.stderr)
        serialized = json.dumps(first, ensure_ascii=False)
        self.assertNotIn("NEVER_INJECT_THIS_BODY", serialized)
        self.assertIn("直接 Read", serialized)
        self.assertIn("session-continuity/history", serialized)

        _, second = self.run_hook(SESSION_START, data)
        self.assertIsNone(second)
        self.assertTrue(target.exists())

    def test_inherited_project_owner_does_not_disable_plugin(self):
        self.write_handoff()
        _, output = self.run_hook(
            SESSION_START,
            {"session_id": "inherited-owner", "source": "startup", "cwd": str(self.root)},
        )
        self.assertIsNotNone(output)
        self.assertIn("待处理 HANDOFF", output["hookSpecificOutput"]["additionalContext"])

    def test_project_config_disables_plugin_hooks(self):
        self.write_handoff()
        (self.root / ".claude" / "session-continuity.json").write_text(
            json.dumps({"handler": "project"}),
            encoding="utf-8",
        )
        _, output = self.run_hook(
            SESSION_START,
            {"session_id": "disabled", "source": "startup", "cwd": str(self.root)},
        )
        self.assertIsNone(output)

    def test_consume_archives_confirmed_handoff(self):
        target = self.write_handoff(secret="正文秘密")
        with patch.dict(os.environ, self.env, clear=True):
            metadata = handoff.read_metadata(target)
            archived = handoff.consume(metadata, datetime(2026, 7, 14, 12, 30, 0))
        self.assertFalse(target.exists())
        self.assertTrue(archived.exists())
        self.assertIn("正文秘密", archived.read_text(encoding="utf-8"))

    def test_precompact_only_reminds_and_never_writes_handoff(self):
        process, output = self.run_hook(PRE_COMPACT, {"trigger": "auto", "cwd": str(self.root)})
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("/save-state", output["systemMessage"])
        self.assertFalse((self.root / ".claude" / "HANDOFF.md").exists())


if __name__ == "__main__":
    unittest.main()
