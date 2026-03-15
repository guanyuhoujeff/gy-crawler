import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_login_session_module():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "facebook_login_session.py"
    spec = importlib.util.spec_from_file_location("facebook_login_session", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakePage:
    def __init__(self):
        self.goto_calls = []

    def goto(self, url, wait_until=None):
        self.goto_calls.append({"url": url, "wait_until": wait_until})


class FakeContext:
    def __init__(self):
        self.storage_state_calls = []
        self.closed = False
        self.page = FakePage()

    def new_page(self):
        return self.page

    def storage_state(self, path):
        self.storage_state_calls.append(path)

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.context = FakeContext()
        self.new_context_calls = 0
        self.closed = False

    def new_context(self):
        self.new_context_calls += 1
        return self.context

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self):
        self.browser = FakeBrowser()
        self.launch_calls = []

    def launch(self, **kwargs):
        self.launch_calls.append(kwargs)
        return self.browser


class FakePlaywrightRuntime:
    def __init__(self):
        self.chromium = FakeChromium()
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeSyncPlaywrightFactory:
    def __init__(self, runtime):
        self.runtime = runtime

    def start(self):
        return self.runtime


class LoginSessionScriptTests(unittest.TestCase):
    def test_parse_args_requires_storage_state(self):
        module = load_login_session_module()

        with self.assertRaises(SystemExit) as exc_info:
            module.parse_args([])

        self.assertEqual(exc_info.exception.code, 2)

    def test_main_launches_headed_browser_and_saves_storage_state(self):
        module = load_login_session_module()
        runtime = FakePlaywrightRuntime()

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_state_path = Path(tmpdir) / "facebook-state.json"

            with mock.patch.object(
                module,
                "sync_playwright",
                return_value=FakeSyncPlaywrightFactory(runtime),
            ):
                with mock.patch.object(module, "input", return_value=""):
                    exit_code = module.main(
                        ["--storage-state", str(storage_state_path), "--headed"]
                    )

        self.assertEqual(exit_code, 0)
        self.assertEqual(runtime.chromium.launch_calls, [{"headless": False}])
        self.assertEqual(runtime.chromium.browser.context.storage_state_calls, [str(storage_state_path)])

    def test_main_creates_parent_directories_for_storage_state(self):
        module = load_login_session_module()
        runtime = FakePlaywrightRuntime()

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_state_path = Path(tmpdir) / ".secrets" / "facebook-state.json"

            with mock.patch.object(
                module,
                "sync_playwright",
                return_value=FakeSyncPlaywrightFactory(runtime),
            ):
                with mock.patch.object(module, "input", return_value=""):
                    exit_code = module.main(["--storage-state", str(storage_state_path)])

            self.assertTrue(storage_state_path.parent.exists())

        self.assertEqual(exit_code, 0)
        self.assertEqual(runtime.chromium.browser.context.storage_state_calls, [str(storage_state_path)])


if __name__ == "__main__":
    unittest.main()
