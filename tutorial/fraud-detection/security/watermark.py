"""Simple model watermark via sidecar manifest (week 13 lab)."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATERMARK_SALT = "mlops-course-week13"


def manifest_path(model_path: Path) -> Path:
    return model_path.with_suffix(model_path.suffix + ".manifest.json")


def apply_watermark(model_path: Path, owner: str = "mlops-team") -> dict:
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    manifest = {
        "model_path": str(model_path.relative_to(ROOT)),
        "sha256": digest,
        "watermark": hashlib.sha256(f"{digest}:{WATERMARK_SALT}".encode()).hexdigest()[:32],
        "owner": owner,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path(model_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_watermark(model_path: Path) -> dict:
    path = manifest_path(model_path)
    if not path.exists():
        return {"verified": False, "reason": "missing manifest"}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    expected = hashlib.sha256(f"{digest}:{WATERMARK_SALT}".encode()).hexdigest()[:32]
    ok = manifest.get("sha256") == digest and manifest.get("watermark") == expected
    return {
        "verified": ok,
        "owner": manifest.get("owner"),
        "applied_at": manifest.get("applied_at"),
        "reason": None if ok else "digest or watermark mismatch",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--model", default="models/model.pkl")
    args = parser.parse_args()
    model = ROOT / args.model
    if args.apply:
        print(json.dumps(apply_watermark(model), indent=2))
    elif args.verify:
        print(json.dumps(verify_watermark(model), indent=2))
    else:
        parser.error("use --apply or --verify")


if __name__ == "__main__":
    main()