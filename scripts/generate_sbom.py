"""Generate SPDX SBOM for container image using Trivy."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate_sbom(image: str, output: Path) -> dict:
    trivy = shutil.which("trivy")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not trivy:
        stub = {
            "spdxVersion": "SPDX-2.3",
            "name": image,
            "packages": [],
            "note": "trivy not installed; stub SBOM for lab structure",
        }
        output.write_text(json.dumps(stub, indent=2), encoding="utf-8")
        return {"status": "stub", "output": str(output), "packages": 0}

    cmd = [trivy, "image", "--format", "spdx-json", "-o", str(output), image]
    subprocess.run(cmd, check=True)
    data = json.loads(output.read_text(encoding="utf-8"))
    packages = len(data.get("packages", []))
    return {"status": "ok", "output": str(output), "packages": packages}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="mlops-cpu:local")
    parser.add_argument("--output", default="docs/sbom-cpu.json")
    args = parser.parse_args()
    out = ROOT / args.output
    result = generate_sbom(args.image, out)
    print(json.dumps(result, indent=2))
    if result["status"] == "stub":
        sys.exit(0)


if __name__ == "__main__":
    main()