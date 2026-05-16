"""
Checkpoint system for the sentience engine.

Auto-checkpoints every 30 minutes, keeps up to 96 (48 hours of history).
Manual create/restore/list via CLI.

Checkpoints include brain/ state AND engine/ source code — full rollback.
Stored outside the agent's workspace view (checkpoints/ is gitignored).

Usage:
    python checkpoint.py create "before-experiment"
    python checkpoint.py list
    python checkpoint.py restore "before-experiment"
    python checkpoint.py restore --latest
    python checkpoint.py delete "old-checkpoint"
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
# Checkpoints stored outside the agent's workspace sandbox.
# In Docker: /checkpoints (separate volume, not under /workspace)
# On host: ~/.sentience_checkpoints
_DOCKER_CHECKPOINT_DIR = Path("/checkpoints")
_HOST_CHECKPOINT_DIR = Path("C:/.sentience_checkpoints")
CHECKPOINT_DIR = _DOCKER_CHECKPOINT_DIR if _DOCKER_CHECKPOINT_DIR.exists() or os.environ.get("DOCKER") else _HOST_CHECKPOINT_DIR
MANIFEST_PATH = CHECKPOINT_DIR / "manifest.json"

# What to snapshot — everything that constitutes the agent's state + code
SNAPSHOT_DIRS = ["brain", "engine", "perception"]
SNAPSHOT_FILES = ["main.py", "restart_watchdog.py"]
# Exclude from snapshots
EXCLUDE_PATTERNS = {"__pycache__", ".pyc", "checkpoints"}

MAX_AUTO_CHECKPOINTS = 96  # 96 * 30min = 48 hours


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"checkpoints": []}


def _save_manifest(manifest: dict):
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_PATTERNS or part.endswith(".pyc"):
            return True
    return False


def create_checkpoint(name: str, auto: bool = False) -> str:
    """Create a full snapshot of the agent's state and code."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = name.replace(" ", "_").replace("/", "_")
    checkpoint_id = f"{ts}_{safe_name}"
    checkpoint_path = CHECKPOINT_DIR / checkpoint_id

    checkpoint_path.mkdir(parents=True, exist_ok=True)

    file_count = 0

    # Copy directories
    for dir_name in SNAPSHOT_DIRS:
        src = WORKSPACE / dir_name
        if src.exists():
            dst = checkpoint_path / dir_name
            for item in src.rglob("*"):
                if item.is_file() and not _should_exclude(item.relative_to(WORKSPACE)):
                    rel = item.relative_to(WORKSPACE)
                    target = checkpoint_path / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                    file_count += 1

    # Copy individual files
    for fname in SNAPSHOT_FILES:
        src = WORKSPACE / fname
        if src.exists():
            shutil.copy2(src, checkpoint_path / fname)
            file_count += 1

    # Snapshot list of all root .py files (so restore can clean up extras)
    root_py_files = [f.name for f in WORKSPACE.glob("*.py")
                     if f.name not in ("checkpoint.py",)]
    (checkpoint_path / "_root_py_manifest.json").write_text(
        json.dumps(root_py_files), encoding="utf-8"
    )

    # Record metadata
    manifest = _load_manifest()

    # Get current soul state if available
    soul_state = {}
    soul_path = WORKSPACE / "brain" / "soul.json"
    if soul_path.exists():
        try:
            soul_state = json.loads(soul_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    entry = {
        "id": checkpoint_id,
        "name": name,
        "timestamp": datetime.now().isoformat(),
        "unix_time": time.time(),
        "auto": auto,
        "file_count": file_count,
        "soul_state": soul_state,
    }
    manifest["checkpoints"].append(entry)

    # Prune old auto-checkpoints if over limit
    if auto:
        auto_checkpoints = [c for c in manifest["checkpoints"] if c.get("auto")]
        if len(auto_checkpoints) > MAX_AUTO_CHECKPOINTS:
            to_remove = auto_checkpoints[:-MAX_AUTO_CHECKPOINTS]
            for old in to_remove:
                old_path = CHECKPOINT_DIR / old["id"]
                if old_path.exists():
                    shutil.rmtree(old_path)
                manifest["checkpoints"].remove(old)

    _save_manifest(manifest)
    return checkpoint_id


def restore_checkpoint(name_or_id: str, stop_agent: bool = True) -> bool:
    """Restore the agent's state from a checkpoint.
    
    This REPLACES brain/ and engine/ with the checkpoint contents.
    The agent must be stopped first.
    """
    manifest = _load_manifest()

    # Find the checkpoint
    entry = None
    for c in manifest["checkpoints"]:
        if c["id"] == name_or_id or c["name"] == name_or_id:
            entry = c
            break

    if not entry:
        print(f"Checkpoint not found: {name_or_id}")
        return False

    checkpoint_path = CHECKPOINT_DIR / entry["id"]
    if not checkpoint_path.exists():
        print(f"Checkpoint directory missing: {checkpoint_path}")
        return False

    if stop_agent:
        print("Stopping agent...")
        os.system("docker compose -f {} stop".format(WORKSPACE / "docker-compose.yml"))
        time.sleep(3)

    # Restore directories
    for dir_name in SNAPSHOT_DIRS:
        src = checkpoint_path / dir_name
        dst = WORKSPACE / dir_name
        if src.exists():
            # Remove current, replace with checkpoint
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  Restored {dir_name}/")

    # Restore individual files
    for fname in SNAPSHOT_FILES:
        src = checkpoint_path / fname
        if src.exists():
            shutil.copy2(src, WORKSPACE / fname)
            print(f"  Restored {fname}")

    # Clean up root .py files that didn't exist at checkpoint time
    manifest_file = checkpoint_path / "_root_py_manifest.json"
    if manifest_file.exists():
        allowed = set(json.loads(manifest_file.read_text(encoding="utf-8")))
        allowed.add("checkpoint.py")  # never delete ourselves
        for f in WORKSPACE.glob("*.py"):
            if f.name not in allowed:
                f.unlink()
                print(f"  Removed post-checkpoint file: {f.name}")
    
    print(f"\nRestored checkpoint: {entry['name']} ({entry['timestamp']})")

    if stop_agent:
        print("Restarting agent...")
        os.system("docker compose -f {} restart".format(WORKSPACE / "docker-compose.yml"))

    return True


def restore_latest():
    """Restore the most recent checkpoint."""
    manifest = _load_manifest()
    if not manifest["checkpoints"]:
        print("No checkpoints found.")
        return False
    latest = manifest["checkpoints"][-1]
    print(f"Restoring latest: {latest['name']} ({latest['timestamp']})")
    return restore_checkpoint(latest["id"])


def list_checkpoints():
    """List all checkpoints."""
    manifest = _load_manifest()
    if not manifest["checkpoints"]:
        print("No checkpoints.")
        return

    print(f"{'ID':<35} {'Name':<25} {'Time':<20} {'Type':<6} {'Mood'}")
    print("-" * 110)
    for c in manifest["checkpoints"]:
        mood = c.get("soul_state", {}).get("mood", "?")
        auto = "auto" if c.get("auto") else "manual"
        ts = c["timestamp"][:19]
        print(f"{c['id']:<35} {c['name']:<25} {ts:<20} {auto:<6} {mood}")


def delete_checkpoint(name_or_id: str):
    """Delete a checkpoint."""
    manifest = _load_manifest()
    entry = None
    for c in manifest["checkpoints"]:
        if c["id"] == name_or_id or c["name"] == name_or_id:
            entry = c
            break

    if not entry:
        print(f"Checkpoint not found: {name_or_id}")
        return

    checkpoint_path = CHECKPOINT_DIR / entry["id"]
    if checkpoint_path.exists():
        shutil.rmtree(checkpoint_path)
    manifest["checkpoints"].remove(entry)
    _save_manifest(manifest)
    print(f"Deleted: {entry['name']} ({entry['id']})")


# ── Auto-checkpoint function (called from heartbeat) ──────────────

def auto_checkpoint():
    """Called every 30 minutes from the heartbeat. Non-blocking."""
    name = f"auto_{datetime.now().strftime('%Y%m%d_%H%M')}"
    try:
        checkpoint_id = create_checkpoint(name, auto=True)
        return checkpoint_id
    except Exception as e:
        return f"[ERROR] {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentience Engine Checkpoint Manager")
    sub = parser.add_subparsers(dest="command")

    create_p = sub.add_parser("create", help="Create a checkpoint")
    create_p.add_argument("name", help="Checkpoint name")

    restore_p = sub.add_parser("restore", help="Restore a checkpoint")
    restore_p.add_argument("name", nargs="?", help="Checkpoint name or ID")
    restore_p.add_argument("--latest", action="store_true", help="Restore most recent")

    sub.add_parser("list", help="List all checkpoints")

    delete_p = sub.add_parser("delete", help="Delete a checkpoint")
    delete_p.add_argument("name", help="Checkpoint name or ID")

    args = parser.parse_args()

    if args.command == "create":
        cid = create_checkpoint(args.name)
        print(f"Created checkpoint: {cid}")
    elif args.command == "restore":
        if args.latest:
            restore_latest()
        elif args.name:
            restore_checkpoint(args.name)
        else:
            print("Specify a checkpoint name or --latest")
    elif args.command == "list":
        list_checkpoints()
    elif args.command == "delete":
        delete_checkpoint(args.name)
    else:
        parser.print_help()
