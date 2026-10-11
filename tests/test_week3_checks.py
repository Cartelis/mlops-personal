"""Fail-closed checks for Week 3 evidence; only the standard library is needed."""
from __future__ import annotations

import argparse
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/week3.py"
SPEC = importlib.util.spec_from_file_location("week3_checks", SCRIPT)
week3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(week3)


class ScanReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="week3-checks-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        evidence = root / "docs/week3"
        evidence.mkdir(parents=True)
        for name, value in (("ROOT", root), ("EVIDENCE", evidence)):
            patcher = patch.object(week3, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(week3, "docker", return_value=json.dumps([{"Id": "sha256:current"}]))
        self.docker = patcher.start()
        self.addCleanup(patcher.stop)
        self.valid = {
            "SchemaVersion": 2,
            "Metadata": {"ImageID": "sha256:current"},
            "Results": [
                {"Class": "os-pkgs", "Type": "debian", "Packages": [{"Name": "libc6"}]},
                {"Class": "lang-pkgs", "Type": "python-pkg", "Packages": [{"Name": "fastapi"}]},
            ],
        }
        self.args = argparse.Namespace(kinds=["cpu"], gate=True)

    def run_report(self, data):
        (week3.EVIDENCE / "trivy-cpu.json").write_text(json.dumps(data))
        with contextlib.redirect_stdout(io.StringIO()):
            week3.scan_report(self.args)

    def test_complete_zero_critical_report_passes(self):
        self.valid["Results"][0]["Vulnerabilities"] = [{"Severity": "HIGH"}]
        self.run_report(self.valid)
        report = (week3.ROOT / "docs/security-scan.md").read_text()
        self.assertIn("| mlops-cpu:local | 1 | 0 |", report)
        self.assertIn("CRITICAL vartas: PASS", report)
        self.docker.assert_called_once_with("image", "inspect", "mlops-cpu:local")

    def test_empty_or_non_list_results_are_rejected(self):
        for results in ([], None, {}, [None]):
            with self.subTest(results=results):
                data = copy.deepcopy(self.valid)
                data["Results"] = results
                with self.assertRaisesRegex(RuntimeError, "Incomplete Trivy report"):
                    self.run_report(data)
        self.docker.assert_not_called()

    def test_missing_os_or_python_package_coverage_is_rejected(self):
        for omitted, label in ((0, "OS"), (1, "Python")):
            with self.subTest(omitted=label):
                data = copy.deepcopy(self.valid)
                del data["Results"][omitted]
                with self.assertRaisesRegex(RuntimeError, f"lacks {label} package coverage"):
                    self.run_report(data)
        self.docker.assert_not_called()

    def test_empty_package_inventory_is_rejected(self):
        for index, label in ((0, "OS"), (1, "Python")):
            with self.subTest(empty=label):
                data = copy.deepcopy(self.valid)
                data["Results"][index]["Packages"] = []
                with self.assertRaisesRegex(RuntimeError, f"lacks {label} package coverage"):
                    self.run_report(data)

    def test_scan_for_another_image_is_rejected(self):
        self.valid["Metadata"]["ImageID"] = "sha256:old"
        with self.assertRaisesRegex(RuntimeError, "different image"):
            self.run_report(self.valid)

    def test_critical_fails_and_preserves_the_finding(self):
        self.valid["Results"][0]["Vulnerabilities"] = [{"Severity": "CRITICAL"}]
        with self.assertRaises(SystemExit) as caught:
            self.run_report(self.valid)
        self.assertEqual(caught.exception.code, 1)
        report = (week3.ROOT / "docs/security-scan.md").read_text()
        self.assertIn("| mlops-cpu:local | 0 | 1 |", report)
        self.assertIn("CRITICAL vartas: FAIL", report)

    def test_malformed_vulnerability_data_is_rejected(self):
        for findings in (None, {}, [None], [{"Severity": None}]):
            with self.subTest(findings=findings):
                data = copy.deepcopy(self.valid)
                data["Results"][0]["Vulnerabilities"] = findings
                with self.assertRaisesRegex(RuntimeError, "Malformed Trivy vulnerability data"):
                    self.run_report(data)


class APIEndpointTests(unittest.TestCase):
    def test_same_normalized_endpoint_is_rejected_before_requests(self):
        args = argparse.Namespace(cpu="HTTP://LOCALHOST:80/", onnx="http://localhost")
        with patch.object(week3, "request") as request:
            with self.assertRaisesRegex(RuntimeError, "different API URLs"):
                week3.api_check(args)
            request.assert_not_called()

    def test_normalization_preserves_distinct_ports_and_base_paths(self):
        self.assertEqual(week3.normalize_base_url("http://LOCALHOST:18080/api/"),
                         "http://localhost:18080/api")
        self.assertNotEqual(week3.normalize_base_url("http://localhost:18080"),
                            week3.normalize_base_url("http://localhost:18081"))
        self.assertEqual(week3.normalize_base_url("https://[::1]:443/"), "https://[::1]")

    def test_invalid_base_url_is_rejected(self):
        for url in ("localhost:18080", "file:///tmp/api", "http://host?query=1",
                    "http://host#fragment", "http://user:password@host"):
            with self.subTest(url=url):
                with self.assertRaisesRegex(RuntimeError, "API base URL"):
                    week3.normalize_base_url(url)


class CleanupTests(unittest.TestCase):
    def test_only_current_checkout_containers_can_be_removed(self):
        for label_name, labels, allowed in (
            ("unrelated", {}, False),
            ("old generic label", {week3.LABEL: "true"}, False),
            ("other checkout", {week3.LABEL: "true", week3.PROJECT_LABEL: "/other/project"}, False),
            ("this checkout", {week3.LABEL: "true", week3.PROJECT_LABEL: str(week3.ROOT)}, True),
        ):
            with self.subTest(container=label_name):
                found = subprocess.CompletedProcess([], 0, json.dumps([{"Config": {"Labels": labels}}]), "")
                with patch.object(week3.subprocess, "run", return_value=found), \
                        patch.object(week3, "docker") as docker:
                    if allowed:
                        week3.cleanup("cpu")
                        docker.assert_called_once_with("rm", "-f", "week3-cpu")
                    else:
                        with self.assertRaisesRegex(RuntimeError, "Refusing to replace"):
                            week3.cleanup("cpu")
                        docker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
