"""bootstrap — set up this machine from the dotfiles repo."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from scripts.common import (
    Entry,
    ask_overwrite,
    checksum,
    info,
    load_state,
    now_iso,
    save_state,
    warn,
)
from scripts.modules import tmux

REPO_ROOT = Path(__file__).parent.parent


def handle_file(
    repo_rel: str,
    dest: Path,
    state: dict,
    *,
    force: bool,
    dry_run: bool,
) -> str:
    """
    Copy repo_rel → dest, respecting state and user preferences.
    Returns one of: 'copied', 'skipped', 'warned'.
    """
    src = REPO_ROOT / repo_rel

    if not src.exists():
        warn(f"repo file missing, skipping: {repo_rel}")
        return "warned"

    current_repo_cs = checksum(src)
    dest_key = str(dest)
    entry: Entry | None = state["entries"].get(dest_key)

    # Destination does not exist — just copy.
    if not dest.exists():
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            state["entries"][dest_key] = {
                "repo_rel": repo_rel,
                "repo_checksum": current_repo_cs,
                "dest_checksum": current_repo_cs,
                "bootstrapped_at": now_iso(),
            }
        info(f"{'[dry-run] ' if dry_run else ''}copied → {dest}")
        return "copied"

    current_dest_cs = checksum(dest)

    if entry is None:
        # File exists but we've never managed it — treat as a conflict.
        repo_changed = True
        dest_changed = True
    else:
        repo_changed = current_repo_cs != entry["repo_checksum"]
        dest_changed = current_dest_cs != entry["dest_checksum"]

    if not repo_changed and not dest_changed:
        # Nothing to do.
        return "skipped"

    if repo_changed and not dest_changed:
        # Safe update from repo.
        if not dry_run:
            shutil.copy2(src, dest)
            state["entries"][dest_key] = {
                "repo_rel": repo_rel,
                "repo_checksum": current_repo_cs,
                "dest_checksum": current_repo_cs,
                "bootstrapped_at": now_iso(),
            }
        info(f"{'[dry-run] ' if dry_run else ''}updated → {dest}")
        return "copied"

    if not repo_changed and dest_changed:
        # Local customization — leave it alone.
        warn(f"locally modified, skipping: {dest}")
        return "warned"

    # Both changed — conflict.
    warn(f"conflict (both repo and local changed): {dest}")
    do_overwrite = force or (not dry_run and ask_overwrite(dest))
    if do_overwrite:
        if not dry_run:
            shutil.copy2(src, dest)
            state["entries"][dest_key] = {
                "repo_rel": repo_rel,
                "repo_checksum": current_repo_cs,
                "dest_checksum": current_repo_cs,
                "bootstrapped_at": now_iso(),
            }
        info(f"{'[dry-run] ' if dry_run else ''}overwritten → {dest}")
        return "copied"

    info(f"skipped (kept local): {dest}")
    return "warned"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap this machine from dotfiles repo.")
    parser.add_argument("--force", action="store_true", help="overwrite all conflicts without prompting")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without making changes")
    args = parser.parse_args()

    if args.dry_run:
        print("→ Bootstrapping (dry run — no changes will be made)")
    else:
        print("→ Bootstrapping from repo")

    state = load_state()
    counts = {"copied": 0, "skipped": 0, "warned": 0}

    # tmux
    print("\n[tmux]")
    for repo_rel, dest in tmux.BOOTSTRAP_MAPPINGS:
        result = handle_file(repo_rel, dest, state, force=args.force, dry_run=args.dry_run)
        counts[result] += 1

    # tmux themes
    themes_src = REPO_ROOT / tmux.BOOTSTRAP_THEMES_SRC_REL
    if themes_src.is_dir():
        for theme in sorted(themes_src.glob("*.sh")):
            dest = tmux.BOOTSTRAP_THEMES_DEST / theme.name
            result = handle_file(
                f"{tmux.BOOTSTRAP_THEMES_SRC_REL}/{theme.name}",
                dest,
                state,
                force=args.force,
                dry_run=args.dry_run,
            )
            counts[result] += 1

    if not args.dry_run:
        save_state(state)

    print(
        f"\n✓ Done — {counts['copied']} copied, "
        f"{counts['skipped']} skipped, "
        f"{counts['warned']} warned"
    )

    if counts["warned"] and not args.force:
        print("  Run with --force to overwrite conflicts automatically.")


if __name__ == "__main__":
    sys.exit(main())
