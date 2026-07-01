"""Build deepseek_conversation.zip for HACS zip_release (see hacs.json, release.yml)."""

from __future__ import annotations

import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "custom_components" / "deepseek_conversation"
OUT = REPO_ROOT / "deepseek_conversation.zip"


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Missing integration directory: {SRC}")

    if OUT.exists():
        OUT.unlink()

    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SRC.rglob("*")):
            if path.is_dir():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            arc = path.relative_to(REPO_ROOT / "custom_components").as_posix()
            zf.write(path, arc)
            count += 1

    print(f"[Debug build_hacs_zip]: wrote {OUT.name} ({OUT.stat().st_size} bytes, {count} files)")


if __name__ == "__main__":
    main()
