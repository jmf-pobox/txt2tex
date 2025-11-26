#!/usr/bin/env python3
"""Rollback migration script: restore files from backups

Usage:
    python scripts/rollback_migration.py --date 2025-01-26  # Restore from date
    python scripts/rollback_migration.py --file FILE        # Restore single file
    python scripts/rollback_migration.py --list             # List all backups
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


def find_backups(root_dir: Path = Path(".")) -> list[Path]:
    """Find all backup files.

    Args:
        root_dir: Root directory to search

    Returns:
        List of backup file paths
    """
    return sorted(root_dir.rglob("*.backup.*"))


def parse_backup_timestamp(backup_path: Path) -> datetime | None:
    """Extract timestamp from backup filename.

    Args:
        backup_path: Path like file.txt.backup.20250126-120000

    Returns:
        datetime object or None if parse fails
    """
    try:
        # Extract timestamp part
        parts = backup_path.name.split(".backup.")
        if len(parts) != 2:
            return None
        timestamp_str = parts[1]

        # Parse: YYYYMMDD-HHMMSS
        return datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
    except (ValueError, IndexError):
        return None


def get_original_path(backup_path: Path) -> Path:
    """Get original file path from backup path.

    Args:
        backup_path: Path like file.txt.backup.20250126-120000

    Returns:
        Original file path like file.txt
    """
    # Remove .backup.TIMESTAMP suffix
    name_parts = backup_path.name.split(".backup.")
    if len(name_parts) != 2:
        raise ValueError(f"Invalid backup filename: {backup_path.name}")

    original_name = name_parts[0]
    return backup_path.parent / original_name


def restore_backup(backup_path: Path, dry_run: bool = False) -> None:
    """Restore a file from backup.

    Args:
        backup_path: Path to backup file
        dry_run: If True, only print what would be done
    """
    original_path = get_original_path(backup_path)

    if dry_run:
        print(f"WOULD RESTORE: {backup_path} → {original_path}")
    else:
        shutil.copy2(backup_path, original_path)
        print(f"RESTORED: {backup_path} → {original_path}")


def list_backups() -> None:
    """List all backups with timestamps."""
    backups = find_backups()

    if not backups:
        print("No backups found.")
        return

    print("\nFound backups:")
    print("=" * 80)

    for backup in backups:
        timestamp = parse_backup_timestamp(backup)
        original = get_original_path(backup)
        fmt = "%Y-%m-%d %H:%M:%S"
        timestamp_str = timestamp.strftime(fmt) if timestamp else "unknown"

        print(f"{timestamp_str}  {backup}")
        print(f"  → {original}")
        print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rollback migration by restoring from backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--date",
        help="Restore all backups from this date (YYYY-MM-DD)",
    )
    group.add_argument(
        "--file",
        type=Path,
        help="Restore single file (provide original path)",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="List all available backups",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be restored without doing it",
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        list_backups()
        return 0

    # Restore by date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"ERROR: Invalid date format: {args.date}", file=sys.stderr)
            print("Expected: YYYY-MM-DD", file=sys.stderr)
            return 1

        backups = find_backups()
        matching = []

        for backup in backups:
            timestamp = parse_backup_timestamp(backup)
            if timestamp and timestamp.date() == target_date:
                matching.append(backup)

        if not matching:
            print(f"No backups found for date: {args.date}")
            return 0

        print(f"Found {len(matching)} backups from {args.date}:")
        for backup in matching:
            print(f"  {backup}")

        if not args.dry_run:
            response = input("\nRestore all? [y/N]: ")
            if response.lower() != "y":
                print("Cancelled.")
                return 0

        for backup in matching:
            restore_backup(backup, dry_run=args.dry_run)

        print(f"\nRestored {len(matching)} files.")
        return 0

    # Restore single file
    if args.file:
        # Find most recent backup for this file
        pattern = f"{args.file.name}.backup.*"
        backups = sorted(
            args.file.parent.glob(pattern),
            key=lambda p: parse_backup_timestamp(p) or datetime.min,
            reverse=True,
        )

        if not backups:
            print(f"ERROR: No backup found for {args.file}", file=sys.stderr)
            return 1

        latest = backups[0]
        timestamp = parse_backup_timestamp(latest)
        fmt = "%Y-%m-%d %H:%M:%S"
        timestamp_str = timestamp.strftime(fmt) if timestamp else "unknown"

        print(f"Latest backup: {latest}")
        print(f"Timestamp: {timestamp_str}")

        if not args.dry_run:
            response = input("Restore? [y/N]: ")
            if response.lower() != "y":
                print("Cancelled.")
                return 0

        restore_backup(latest, dry_run=args.dry_run)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
