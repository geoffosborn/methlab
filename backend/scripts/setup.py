"""One-shot setup: create database, run migrations, seed data."""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv()

    db_name = os.getenv("DB_NAME", "methlab")
    db_user = os.getenv("DB_USER", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    print(f"=== MethLab Setup ===")
    print(f"Database: {db_name} @ {db_host}:{db_port}")
    print()

    # 1. Create database if not exists
    print("1. Creating database (if needed)...")
    try:
        subprocess.run(
            ["createdb", "-h", db_host, "-p", db_port, "-U", db_user, db_name],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"   Created database '{db_name}'")
    except subprocess.CalledProcessError as e:
        if "already exists" in (e.stderr or ""):
            print(f"   Database '{db_name}' already exists")
        else:
            print(f"   Warning: {e.stderr}")

    # 2. Run migrations
    print("\n2. Running migrations...")
    subprocess.run(
        [sys.executable, str(Path(__file__).parent / "run_migrations.py")],
        check=True,
    )

    # 3. Seed data
    print("\n3. Seeding coal mine registry...")
    subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "apps/registry/seed_coal_mines.py")],
        check=True,
    )

    print("\n=== Setup complete ===")


if __name__ == "__main__":
    main()
