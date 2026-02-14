#!/usr/bin/env python3
"""One-time bootstrap: copy scaffold banner + thumbnail images to itingen cache.

Copies finalized banner images and event thumbnails from the scaffold Dropbox
cache to itingen's output directory, producing a manifest JSON that maps
dates → banner paths and event slugs → thumbnail paths.

Usage:
    python scripts/copy_scaffold_images.py [--dry-run]
"""

import json
import os
import shutil
import sys
from pathlib import Path

# Source directories (scaffold Dropbox cache)
SCAFFOLD_DATA = Path(
    os.environ.get(
        "SCAFFOLD_DATA_DIR",
        os.path.expanduser(
            "~/Library/CloudStorage/Dropbox/scaffold-data/data/cache"
        ),
    )
)
BANNER_SRC = SCAFFOLD_DATA / "nz_trip_day_banners_final"
THUMB_SRC = SCAFFOLD_DATA / "nz_trip_event_thumbs"

# Target directory
TARGET = Path("output/nz_2026/.ai_cache/images")
MANIFEST_PATH = TARGET / "manifest.json"


def copy_banners(dry_run: bool = False) -> dict:
    """Copy banner images, return {date_str: relative_path}."""
    banner_map = {}
    if not BANNER_SRC.exists():
        print(f"[WARN] Banner source not found: {BANNER_SRC}")
        return banner_map

    banner_dir = TARGET / "banners"
    if not dry_run:
        banner_dir.mkdir(parents=True, exist_ok=True)

    for f in sorted(BANNER_SRC.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        dest = banner_dir / f.name
        # Key: date part (e.g., "2026-01-05" or "2026-01-05-david")
        key = f.stem
        banner_map[key] = str(dest)
        if dry_run:
            print(f"  [DRY] {f.name} → {dest}")
        elif not dest.exists():
            shutil.copy2(f, dest)
            print(f"  [COPY] {f.name}")
        else:
            print(f"  [SKIP] {f.name} (exists)")

    return banner_map


def copy_thumbs(dry_run: bool = False) -> dict:
    """Copy event thumbnails, return {event_slug: relative_path}."""
    thumb_map = {}
    if not THUMB_SRC.exists():
        print(f"[WARN] Thumbnail source not found: {THUMB_SRC}")
        return thumb_map

    thumb_dir = TARGET / "thumbs"
    if not dry_run:
        thumb_dir.mkdir(parents=True, exist_ok=True)

    for date_dir in sorted(THUMB_SRC.iterdir()):
        if not date_dir.is_dir():
            continue
        for event_dir in sorted(date_dir.iterdir()):
            if not event_dir.is_dir():
                continue
            # Find the most recent image file (by name — timestamp-based)
            images = sorted(
                [
                    f
                    for f in event_dir.iterdir()
                    if f.suffix.lower() in (".png", ".jpg", ".jpeg")
                ],
                reverse=True,
            )
            if not images:
                continue

            latest = images[0]
            # event_slug is the directory name (e.g., "2025-12-29t0900-breakfast-ho")
            event_slug = event_dir.name
            dest_dir = thumb_dir / date_dir.name / event_slug
            dest = dest_dir / latest.name

            thumb_map[event_slug] = str(dest)
            if dry_run:
                print(f"  [DRY] {event_slug}/{latest.name}")
            elif not dest.exists():
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(latest, dest)
                print(f"  [COPY] {event_slug}/{latest.name}")
            else:
                print(f"  [SKIP] {event_slug}/{latest.name} (exists)")

    return thumb_map


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Banner source: {BANNER_SRC}")
    print(f"Thumb source:  {THUMB_SRC}")
    print(f"Target:        {TARGET}")
    print()

    print("=== Banners ===")
    banners = copy_banners(dry_run)
    print(f"  {len(banners)} banners")

    print()
    print("=== Thumbnails ===")
    thumbs = copy_thumbs(dry_run)
    print(f"  {len(thumbs)} thumbnails")

    manifest = {"banners": banners, "thumbs": thumbs}

    if not dry_run:
        TARGET.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest written to {MANIFEST_PATH}")
    else:
        print(f"\n[DRY RUN] Would write manifest to {MANIFEST_PATH}")

    print("Done.")


if __name__ == "__main__":
    main()
