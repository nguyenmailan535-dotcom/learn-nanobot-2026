from __future__ import annotations

import subprocess
from pathlib import Path

SNAPSHOT_DATE = "2026-09-24"
UPSTREAM = "https://github.com/HKUDS/nanobot.git"


def main() -> None:
    print(f"learn-nanobot snapshot date: {SNAPSHOT_DATE}")
    print(f"upstream: {UPSTREAM}")
    print()
    try:
        out = subprocess.check_output(
            ["git", "ls-remote", UPSTREAM, "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=15,
        ).strip()
        if out:
            print("Current upstream HEAD:")
            print(out)
            print("\nCompare this with the date/snapshot you are studying before trusting commands or source paths.")
        else:
            print("Could not read upstream HEAD.")
    except Exception as exc:
        print("Unable to query GitHub from this environment:")
        print(exc)
        print("\nFallback: open UPSTREAM_SNAPSHOT.md and the official current docs manually.")


if __name__ == "__main__":
    main()
