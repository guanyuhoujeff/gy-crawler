import subprocess
import sys
import unittest
from pathlib import Path


class ScriptBootstrapTests(unittest.TestCase):
    def test_podcast_episode_analyze_help_runs_as_plain_script(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = repo_root / "scripts" / "podcast_episode_analyze.py"

        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--input-dir", completed.stdout)


if __name__ == "__main__":
    unittest.main()
