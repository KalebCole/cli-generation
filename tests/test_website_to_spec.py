import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "website_to_spec.py"


class WebsiteToSpecTests(unittest.TestCase):
    def make_fake_press(self, root: Path) -> tuple[Path, Path]:
        log = root / "press.log"
        binary = root / "cli-printing-press"
        binary.write_text(
            """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ['FAKE_PRESS_LOG'], 'a') as f:
    f.write(json.dumps(args) + '\\n')
if args[0] == 'probe-reachability':
    print(json.dumps({'mode': 'standard', 'url': args[1]}))
elif args[0] == 'browser-sniff':
    out = pathlib.Path(args[args.index('--output') + 1])
    analysis = pathlib.Path(args[args.index('--analysis-output') + 1])
    if os.environ.get('MALFORMED_SPEC'):
        out.write_text("name: demo\\nbase_url: https://api.example.test\\nresources:\\n  search:\\n    endpoints:\\n      query:\\n        method: POST\\n        path: /query\\n        body:\\n          - name: '{\\\"query\\\":\\\"test\\\"}'\\n            type: string\\n")
    else:
        out.write_text('name: demo\\nbase_url: https://api.example.test\\nresources:\\n  items:\\n    endpoints:\\n      list:\\n        method: GET\\n        path: /items\\n')
    analysis.write_text(json.dumps({'endpoints': 1}))
    print(str(out))
elif args[0] == 'generate' and '--dry-run' in args:
    print(json.dumps({'valid': True, 'resources': 1}))
else:
    raise SystemExit('unexpected command: ' + repr(args))
"""
        )
        binary.chmod(0o755)
        return binary, log

    def run_script(self, *args: str, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=REPO,
            text=True,
            capture_output=True,
            env=env,
        )

    def test_har_pipeline_probes_sniffs_and_validates_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary, log = self.make_fake_press(root)
            har = root / "capture.har"
            har.write_text('{"log":{"entries":[]}}')
            run_dir = root / "run"
            env = os.environ.copy()
            env["FAKE_PRESS_LOG"] = str(log)

            result = self.run_script(
                "https://app.example.test",
                "--name", "demo",
                "--har", str(har),
                "--run-dir", str(run_dir),
                "--pp-bin", str(binary),
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(manifest["status"], "spec_validated")
            self.assertEqual(manifest["target_url"], "https://app.example.test")
            self.assertTrue((run_dir / "demo.yaml").exists())
            self.assertTrue((run_dir / "traffic-analysis.json").exists())
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([call[0] for call in calls], [
                "probe-reachability", "browser-sniff", "generate"
            ])
            self.assertIn("--dry-run", calls[2])
            self.assertIn("--spec-source", calls[2])
            self.assertIn("browser-sniffed", calls[2])

    def test_missing_capture_returns_resumable_capture_required_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary, log = self.make_fake_press(root)
            run_dir = root / "run"
            env = os.environ.copy()
            env["FAKE_PRESS_LOG"] = str(log)

            result = self.run_script(
                "https://app.example.test",
                "--run-dir", str(run_dir),
                "--pp-bin", str(binary),
                env=env,
            )

            self.assertEqual(result.returncode, 2)
            manifest = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(manifest["status"], "capture_required")
            self.assertIn("--har", result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([call[0] for call in calls], ["probe-reachability"])

    def test_rejects_missing_har_without_overwriting_existing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary, log = self.make_fake_press(root)
            run_dir = root / "run"
            run_dir.mkdir()
            original = {"status": "spec_validated", "target_url": "https://old.test"}
            (run_dir / "run.json").write_text(json.dumps(original))
            env = os.environ.copy()
            env["FAKE_PRESS_LOG"] = str(log)

            result = self.run_script(
                "https://app.example.test",
                "--har", str(root / "missing.har"),
                "--run-dir", str(run_dir),
                "--pp-bin", str(binary),
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads((run_dir / "run.json").read_text()), original)
            self.assertFalse((run_dir / "reachability.json").exists())
            self.assertFalse((run_dir / "traffic-analysis.json").exists())
            self.assertFalse(log.exists())

    def test_quality_gate_rejects_json_document_as_body_parameter_name(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary, log = self.make_fake_press(root)
            har = root / "capture.har"
            har.write_text('{"log":{"entries":[]}}')
            run_dir = root / "run"
            env = os.environ.copy()
            env["FAKE_PRESS_LOG"] = str(log)
            env["MALFORMED_SPEC"] = "1"

            result = self.run_script(
                "https://app.example.test",
                "--name", "demo",
                "--har", str(har),
                "--run-dir", str(run_dir),
                "--pp-bin", str(binary),
                env=env,
            )

            self.assertEqual(result.returncode, 3, result.stderr)
            manifest = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(manifest["status"], "spec_needs_review")
            self.assertIn("JSON document", manifest["quality_findings"][0])
            self.assertNotIn("handoff_command", manifest)

    def test_rejects_name_that_can_escape_run_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "run"
            result = self.run_script(
                "https://app.example.test",
                "--name", "../escaped",
                "--run-dir", str(run_dir),
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("slug", result.stderr)
            self.assertFalse(run_dir.exists())
            self.assertFalse((root / "escaped.yaml").exists())


if __name__ == "__main__":
    unittest.main()
