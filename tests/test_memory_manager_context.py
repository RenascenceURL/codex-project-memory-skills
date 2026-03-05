import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "memory_manager.py"


class ContextInitBehaviorTests(unittest.TestCase):
    def run_cmd(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.fail(f"Command failed: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
        return proc

    def run_cmd_with_input(self, *args: str, stdin_data: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(cwd),
            input=stdin_data,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.fail(
                f"Command failed: {' '.join(args)}\nINPUT:\n{stdin_data}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )
        return proc

    def test_context_is_read_only_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rules = root / "GLOBAL_ENGINEERING_RULES.md"

            proc = self.run_cmd(
                "context",
                "--project-path",
                str(root),
                "--global-rules",
                str(rules),
                "--json",
                cwd=root,
            )
            payload = json.loads(proc.stdout)

            self.assertIn("missing docs/memory.md", payload["terminal_summary"])
            self.assertFalse((root / "docs" / "memory.md").exists())
            self.assertFalse((root / "docs" / "tasks" / "index.md").exists())
            self.assertFalse(rules.exists())

    def test_context_can_initialize_when_explicitly_requested(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rules = root / "GLOBAL_ENGINEERING_RULES.md"

            self.run_cmd(
                "context",
                "--project-path",
                str(root),
                "--global-rules",
                str(rules),
                "--ensure-init",
                "--json",
                cwd=root,
            )

            self.assertTrue((root / "docs" / "memory.md").exists())
            self.assertTrue((root / "docs" / "tasks" / "index.md").exists())
            self.assertTrue(rules.exists())

    def test_menu_option_4_runs_init(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rules = root / "GLOBAL_ENGINEERING_RULES.md"

            proc = self.run_cmd_with_input(
                "menu",
                "--project-path",
                str(root),
                "--global-rules",
                str(rules),
                stdin_data="4\n0\n",
                cwd=root,
            )

            self.assertIn("4) Init", proc.stdout)
            self.assertIn("Initialization complete.", proc.stdout)
            self.assertTrue((root / "docs" / "memory.md").exists())
            self.assertTrue((root / "docs" / "tasks" / "index.md").exists())
            self.assertTrue(rules.exists())


if __name__ == "__main__":
    unittest.main()
