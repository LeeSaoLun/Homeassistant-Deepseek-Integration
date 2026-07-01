#!/usr/bin/env python3
"""Bump manifest version, draft CHANGELOG.md, commit and push to dev.

Workflow (via bump.bat):
  1. prepare  - manifest + CHANGELOG entwurf
  2. (pause)  - CHANGELOG manuell anpassen
  3. finalize - commit + push origin dev

Release auf GitHub: dev testen, dann dev -> main mergen. Der Release-Workflow
(.github/workflows/release.yml) laeuft nur bei Push auf main mit geaenderter
manifest.json und nutzt den passenden CHANGELOG-Abschnitt.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "custom_components" / "deepseek_conversation" / "manifest.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
PUSH_BRANCH = "dev"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+([-.][\w.]+)?$")


def _run_git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def _run_git_ok(*args: str) -> None:
    subprocess.run(["git", *args], cwd=REPO_ROOT, check=True)


def _current_branch() -> str:
    return _run_git("branch", "--show-current")


def _ensure_push_branch() -> None:
    branch = _current_branch()
    if branch != PUSH_BRANCH:
        print(
            f"Abbruch: Aktueller Branch ist {branch!r}, erwartet {PUSH_BRANCH!r}.\n"
            f"  git checkout {PUSH_BRANCH}",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _validate_version(version: str) -> None:
    if not VERSION_RE.match(version):
        print(
            f"Ungültige Version: {version!r} (erwartet z. B. 1.3.1)",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _ensure_git_repo() -> None:
    try:
        _run_git("rev-parse", "--is-inside-work-tree")
    except subprocess.CalledProcessError:
        print("Kein Git-Repository.", file=sys.stderr)
        raise SystemExit(1)


def _last_tag() -> str | None:
    try:
        return _run_git("describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None


def _commits_since(tag: str | None) -> list[str]:
    log_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        out = _run_git(
            "log",
            "--no-merges",
            "--pretty=format:%s (%h)",
            log_range,
        )
    except subprocess.CalledProcessError:
        return []
    if not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _read_manifest_version() -> str:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return str(data["version"])


def _write_manifest_version(version: str) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["version"] = version
    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _section_heading(version: str) -> str:
    return f"## [{version}]"


def _build_section(version: str, commits: list[str]) -> str:
    lines = [f"## [{version}] - {date.today().isoformat()}", ""]
    if commits:
        lines.extend(f"- {commit}" for commit in commits)
    else:
        lines.append("- (keine Commits seit letztem Release-Tag)")
    lines.append("")
    return "\n".join(lines)


def _changelog_has_version(version: str) -> bool:
    if not CHANGELOG.exists():
        return False
    content = CHANGELOG.read_text(encoding="utf-8")
    # Do not use \b after "]" — it does not match before " - date" (] and space are
    # both non-word characters). Release workflow uses the same heading format.
    heading = re.escape(_section_heading(version))
    return bool(
        re.search(rf"^{heading}(?:\s|$)", content, flags=re.MULTILINE)
    )


def _merge_changelog(new_section: str) -> None:
    header = "# Changelog\n\n"
    intro = "All notable changes to this integration.\n\n"

    if not CHANGELOG.exists():
        CHANGELOG.write_text(header + intro + new_section, encoding="utf-8")
        return

    content = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(r"^## \[", content, flags=re.MULTILINE)
    if match:
        prefix = content[: match.start()]
        rest = content[match.start() :]
    else:
        prefix = content if content.endswith("\n") else content + "\n"
        rest = ""

    if not prefix.strip():
        prefix = header + intro
    elif not prefix.lstrip().startswith("# Changelog"):
        prefix = header + intro + prefix

    CHANGELOG.write_text(prefix + new_section + rest, encoding="utf-8")


def cmd_prepare(version: str) -> int:
    """Update manifest.json and draft CHANGELOG.md (no git commit)."""
    _ensure_git_repo()
    _ensure_push_branch()
    _validate_version(version)

    if not MANIFEST.is_file():
        print(f"manifest.json nicht gefunden: {MANIFEST}", file=sys.stderr)
        return 1

    if _changelog_has_version(version):
        print(
            f"Hinweis: CHANGELOG.md enthält bereits {_section_heading(version)}.",
            file=sys.stderr,
        )
        if _read_manifest_version() == version:
            print(
                f"Release {version} ist vorbereitet. Nur noch committen und pushen:\n"
                f"  python scripts\\bump.py finalize {version}",
                file=sys.stderr,
            )
        return 1

    old_version = _read_manifest_version()
    if version == old_version:
        print(
            f"Hinweis: manifest steht bereits auf {old_version}; wird neu geschrieben.",
            file=sys.stderr,
        )

    tag = _last_tag()
    commits = _commits_since(tag)

    _write_manifest_version(version)
    section = _build_section(version, commits)
    _merge_changelog(section)

    print(f"[Debug bump]: manifest {old_version} -> {version}")
    print(f"[Debug bump]: letzter Tag: {tag or '(keiner)'}")
    print(f"[Debug bump]: {len(commits)} Commit(s) in CHANGELOG übernommen")
    print()
    print("Entwurf erstellt:")
    print(f"  - {MANIFEST.relative_to(REPO_ROOT)}")
    print(f"  - {CHANGELOG.relative_to(REPO_ROOT)}")
    return 0


def _unpushed_on_branch() -> str:
    """Return non-empty git log if local branch is ahead of origin/PUSH_BRANCH."""
    try:
        return _run_git("log", f"origin/{PUSH_BRANCH}..HEAD", "--oneline")
    except subprocess.CalledProcessError:
        return ""


def cmd_finalize(version: str) -> int:
    """Commit manifest + CHANGELOG and push to origin/dev."""
    _ensure_git_repo()
    _ensure_push_branch()
    _validate_version(version)

    manifest_version = _read_manifest_version()
    if manifest_version != version:
        print(
            f"Abbruch: manifest.json ist {manifest_version!r}, erwartet {version!r}.",
            file=sys.stderr,
        )
        return 1

    if not _changelog_has_version(version):
        print(
            f"Abbruch: CHANGELOG.md fehlt {_section_heading(version)}.",
            file=sys.stderr,
        )
        return 1

    manifest_rel = MANIFEST.relative_to(REPO_ROOT).as_posix()
    changelog_rel = CHANGELOG.relative_to(REPO_ROOT).as_posix()

    try:
        dirty = _run_git(
            "status",
            "--porcelain",
            "--",
            manifest_rel,
            changelog_rel,
        )
    except subprocess.CalledProcessError as err:
        print(err.output, file=sys.stderr)
        return 1

    if not dirty:
        unpushed = _unpushed_on_branch()
        if unpushed:
            print(
                "[Debug bump]: working tree clean; pushing existing commits to "
                f"origin/{PUSH_BRANCH}"
            )
            print(unpushed)
            print()
            try:
                _run_git_ok("push", "origin", PUSH_BRANCH)
            except subprocess.CalledProcessError:
                print("Git push fehlgeschlagen.", file=sys.stderr)
                return 1
            print(f"[Debug bump]: pushed to origin/{PUSH_BRANCH}")
            return 0

        print(
            "Abbruch: manifest.json und CHANGELOG.md sind unverändert "
            "(nichts zu committen oder zu pushen).",
            file=sys.stderr,
        )
        return 1

    commit_msg = f"chore: release {version}"
    try:
        _run_git_ok("add", manifest_rel, changelog_rel)
        _run_git_ok("commit", "-m", commit_msg)
        _run_git_ok("push", "origin", PUSH_BRANCH)
    except subprocess.CalledProcessError as err:
        print("Git-Befehl fehlgeschlagen.", file=sys.stderr)
        return getattr(err, "returncode", 1) or 1

    print(f"[Debug bump]: committed and pushed to origin/{PUSH_BRANCH}")
    print()
    print("Nächster Schritt für GitHub-Release:")
    print(f"  1. Auf {PUSH_BRANCH} testen (CI / manuell)")
    print("  2. dev -> main mergen und main pushen")
    print(f"  3. Release-Workflow erstellt Tag {version} (manifest-Änderung auf main)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek integration version bump")
    parser.add_argument(
        "command",
        choices=("prepare", "finalize"),
        help="prepare: Entwurf | finalize: commit + push dev",
    )
    parser.add_argument("version", help="SemVer, z. B. 1.3.1")
    args = parser.parse_args()

    if args.command == "prepare":
        return cmd_prepare(args.version.strip())
    return cmd_finalize(args.version.strip())


if __name__ == "__main__":
    raise SystemExit(main())
