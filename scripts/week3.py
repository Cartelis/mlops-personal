"""Week 3 checks. Uses only Python's standard library (Python >= 3.10)."""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "week3"
LABEL = "lt.vu.mlops.week3"
PROJECT_LABEL = f"{LABEL}.project"


def docker(*args: str) -> str:
    return subprocess.check_output(["docker", *args], text=True).strip()


def request(url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def record(name: str, value: dict) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    value["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    (EVIDENCE / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")


def cleanup(kind: str) -> None:
    name = f"week3-{kind}"
    found = subprocess.run(["docker", "inspect", name], capture_output=True, text=True)
    if found.returncode:
        # Also distinguish an absent name from a stopped/unreachable Docker daemon.
        docker("info", "--format", "{{.ServerVersion}}")
        return
    labels = json.loads(found.stdout)[0]["Config"].get("Labels") or {}
    if labels.get(LABEL) != "true":
        raise RuntimeError(f"Refusing to replace unrelated container {name}")
    if labels.get(PROJECT_LABEL) != str(ROOT):
        raise RuntimeError(f"Refusing to replace {name}: it belongs to a different project checkout")
    docker("rm", "-f", name)


def start(args: argparse.Namespace) -> None:
    cleanup(args.kind)
    name = f"week3-{args.kind}"
    command = ["run", "-d", "--name", name, "--label", f"{LABEL}=true",
               "--label", f"{PROJECT_LABEL}={ROOT}",
               "-p", f"127.0.0.1:{args.port}:8080"]
    if args.kind == "gpu":
        command += ["--gpus", "all"]
    started = time.monotonic()
    docker(*command, f"mlops-{args.kind}:local")
    ready = None
    deadline = started + args.timeout
    while time.monotonic() < deadline:
        state = json.loads(docker("inspect", name))[0]["State"]
        if not state["Running"]:
            raise RuntimeError(f"{name} exited: {docker('logs', name)}")
        try:
            status, body = request(f"http://127.0.0.1:{args.port}/health")
            if status == 200 and body.get("status") == "ok":
                if ready is None:
                    ready = time.monotonic() - started
                if state.get("Health", {}).get("Status") == "healthy":
                    uid = int(docker("exec", name, "id", "-u"))
                    if uid == 0:
                        raise RuntimeError(f"{name} runs as root")
                    result = {"image": f"mlops-{args.kind}:local", "container": name,
                              "image_id": json.loads(docker("inspect", name))[0]["Image"],
                              "url": f"http://127.0.0.1:{args.port}", "uid": uid,
                              "health": "healthy", "http_ready_seconds": round(ready, 3),
                              "cold_start_definition": "docker run invocation to first HTTP 200 /health; image already local",
                              "http_ready_within_5s": ready <= 5}
                    record(f"{args.kind}-runtime", result)
                    print(json.dumps(result, indent=2))
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(0.2)
    raise RuntimeError(f"{name}: no healthy /health in {args.timeout}s; inspect docker logs {name}")


def normalize_base_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url.strip())
    if (parts.scheme not in ("http", "https") or not parts.hostname
            or parts.username is not None or parts.password is not None
            or parts.query or parts.fragment):
        raise RuntimeError("API base URL must be HTTP(S), without credentials, query or fragment")
    host = parts.hostname.lower().rstrip(".")
    if ":" in host:
        host = f"[{host}]"
    port = parts.port
    if port is not None and port != (80 if parts.scheme == "http" else 443):
        host = f"{host}:{port}"
    return urllib.parse.urlunsplit((parts.scheme, host, parts.path.rstrip("/"), "", ""))


def api_check(args: argparse.Namespace) -> None:
    cpu_url = normalize_base_url(args.cpu)
    onnx_url = normalize_base_url(args.onnx)
    if cpu_url == onnx_url:
        raise RuntimeError("CPU and ONNX must have different API URLs; self-comparison proves no parity")
    rng = random.Random(42)
    rows = [{f"f{i}": rng.uniform(-3, 3) for i in range(10)} for _ in range(100)]
    checked = 0
    for row in rows:
        status, expected = request(cpu_url + "/predict", row)
        if status != 200 or expected.get("prediction") not in (0, 1):
            raise RuntimeError(f"CPU prediction failed: {status} {expected}")
        for url in (cpu_url, onnx_url):
            reversed_row = dict(reversed(list(row.items())))
            reversed_row["transaction_id"] = "week3-test"
            status, actual = request(url + "/predict", reversed_row)
            if status != 200 or actual != expected:
                raise RuntimeError(f"Prediction/order parity failed at {url}: {status} {actual} != {expected}")
            checked += 1
    row = rows[0]
    invalid = [dict(row, f0="wrong"), dict(row, f0=True), dict(row, unexpected=1),
               {key: value for key, value in row.items() if key != "f0"},
               dict(row, email="student@example.invalid"), dict(row, f0=float("inf"))]
    for url in (cpu_url, onnx_url):
        for payload in invalid:
            status, body = request(url + "/predict", payload)
            if status != 422:
                raise RuntimeError(f"Expected 422, got {status} at {url}: {body}")
            checked += 1
    result = {"status": "PASS", "parity_rows": len(rows), "order_and_metadata_checks": 200,
              "invalid_payload_checks": 12, "checks": checked,
              "cpu_url": cpu_url, "onnx_url": onnx_url}
    record("api-check", result)
    print(json.dumps(result, indent=2))


def sizes(args: argparse.Namespace) -> None:
    rows = []
    for kind in args.kinds:
        image = f"mlops-{kind}:local"
        found = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True)
        if found.returncode:
            if kind == "gpu":
                continue
            raise RuntimeError(f"Required image missing: {image}")
        data = json.loads(found.stdout)[0]
        # Docker's containerd store reports compressed content in .Size; the
        # classic store has different accounting. Measure rootfs separately.
        rootfs_bytes = int(docker("run", "--rm", "--user", "0", "--entrypoint", "du",
                                  image, "-sx", "--apparent-size", "--block-size=1", "/").split()[0])
        rows.append({"image": image, "id": data["Id"], "platform": data["Os"] + "/" + data["Architecture"],
                     "docker_size_bytes": data["Size"], "docker_size_MB": round(data["Size"] / 1_000_000, 2),
                     "rootfs_bytes": rootfs_bytes, "rootfs_MB": round(rootfs_bytes / 1_000_000, 2)})
    record("image-sizes", {"images": rows, "definition": "rootfs: du -sx --apparent-size --block-size=1 /; Docker .Size accounting depends on image store"})
    lines = ["# Docker vaizdų dydžiai — 3 savaitė", "", "MB = 1 000 000 baitų. Rootfs: išpakuotų failų dydis (`du --apparent-size`). Docker `.Size` priklauso nuo image store; containerd atveju tai suspausto turinio dydis, todėl jo nepainioti su rootfs ar bendra disko vieta.", "",
             "| Vaizdas | Platforma | Docker .Size MB | Rootfs MB |", "|---|---|---:|---:|"]
    lines += [f"| {r['image']} | {r['platform']} | {r['docker_size_MB']} | {r['rootfs_MB']} |" for r in rows]
    lines += ["", "NFR-11: CPU rootfs <=500 MB, ONNX rootfs <=300 MB — tikslai; faktines neatitiktis aptarti."]
    if not any(r["image"] == "mlops-gpu:local" for r in rows):
        lines += ["", "GPU vaizdas šioje aplinkoje neišmatuotas."]
    (ROOT / "docs/image-sizes.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def scan_report(args: argparse.Namespace) -> None:
    lines = ["# Saugumo skenavimas — 3 savaitė", "", f"Laikas (UTC): {datetime.now(timezone.utc).isoformat()}", "",
             "| Vaizdas | HIGH | CRITICAL |", "|---|---:|---:|"]
    critical = 0
    for kind in args.kinds:
        path = EVIDENCE / f"trivy-{kind}.json"
        data = json.loads(path.read_text())
        results = data.get("Results")
        metadata = data.get("Metadata")
        if (data.get("SchemaVersion") != 2 or not isinstance(metadata, dict)
                or not isinstance(results, list) or not results
                or any(not isinstance(result, dict) for result in results)):
            raise RuntimeError(f"Incomplete Trivy report: {path}")
        # A same-image secret-only/partial scan is not vulnerability evidence.
        # All Week 3 images contain both Linux and Python packages, even when
        # the vulnerability arrays themselves are empty or omitted.
        os_results = [result for result in results if result.get("Class") == "os-pkgs"]
        python_results = [result for result in results
                          if result.get("Class") == "lang-pkgs" and result.get("Type") == "python-pkg"]
        for label, covered in (("OS", os_results), ("Python", python_results)):
            if not any(isinstance(result.get("Packages"), list) and result["Packages"]
                       for result in covered):
                raise RuntimeError(f"Trivy report lacks {label} package coverage: {path}; rescan")
        image = json.loads(docker("image", "inspect", f"mlops-{kind}:local"))[0]
        if metadata.get("ImageID") != image["Id"]:
            raise RuntimeError(f"Scan belongs to a different image: {path}; rescan")
        for result in results:
            found = result.get("Vulnerabilities", [])
            if (not isinstance(found, list)
                    or any(not isinstance(v, dict) or not isinstance(v.get("Severity"), str)
                           for v in found)):
                raise RuntimeError(f"Malformed Trivy vulnerability data: {path}")
        vulnerabilities = [v for result in results for v in result.get("Vulnerabilities", [])]
        high = sum(v["Severity"] == "HIGH" for v in vulnerabilities)
        count = sum(v["Severity"] == "CRITICAL" for v in vulnerabilities)
        critical += count
        lines.append(f"| mlops-{kind}:local | {high} | {count} |")
    lines += ["", "Žali JSON ir SBOM: `docs/week3/`. HIGH radinius peržiūrėti prieš viešinant. Kiekvieną išimtį pagrįsti, o ne pakeisti skaičių į nulį.", "",
              "CRITICAL vartas: " + ("PASS" if critical == 0 else "FAIL — publikavimas sustabdytas")]
    (ROOT / "docs/security-scan.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if args.gate and critical:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    run = subs.add_parser("start")
    run.add_argument("kind", choices=("cpu", "onnx", "gpu"))
    run.add_argument("--port", type=int, required=True)
    run.add_argument("--timeout", type=float, default=90)
    run.set_defaults(func=start)
    api = subs.add_parser("api-check")
    api.add_argument("--cpu", default="http://127.0.0.1:18080")
    api.add_argument("--onnx", default="http://127.0.0.1:18081")
    api.set_defaults(func=api_check)
    size = subs.add_parser("sizes")
    size.add_argument("--kinds", nargs="+", choices=("single", "cpu", "onnx", "gpu"),
                      default=["single", "cpu", "onnx", "gpu"])
    size.set_defaults(func=sizes)
    scan = subs.add_parser("scan-report")
    scan.add_argument("--kinds", nargs="+", choices=("cpu", "onnx", "gpu"), default=["cpu", "onnx"])
    scan.add_argument("--gate", action="store_true")
    scan.set_defaults(func=scan_report)
    clean = subs.add_parser("cleanup")
    clean.add_argument("--kinds", nargs="+", choices=("cpu", "onnx", "gpu"),
                       default=["cpu", "onnx", "gpu"])
    clean.set_defaults(func=lambda args: [cleanup(kind) for kind in args.kinds])
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
