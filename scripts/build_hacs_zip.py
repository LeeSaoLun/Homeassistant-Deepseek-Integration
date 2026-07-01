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
    _validate_zip(OUT)


def _validate_zip(path: Path) -> None:
    """Fail fast if the archive does not match HACS zip_release expectations."""
    required = (
        "deepseek_conversation/manifest.json",
        "deepseek_conversation/__init__.py",
    )
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        roots = {n.split("/")[0] for n in names if "/" in n}
        if roots != {"deepseek_conversation"}:
            raise SystemExit(
                f"Invalid zip layout: expected only deepseek_conversation/ at root, got {roots}"
            )
        missing = [entry for entry in required if entry not in names]
        if missing:
            raise SystemExit(f"Zip missing required paths: {missing}")
        if any(n.startswith("custom_components/") for n in names):
            raise SystemExit("Zip must not include custom_components/ prefix (content_in_root: false)")


if __name__ == "__main__":
    main()
