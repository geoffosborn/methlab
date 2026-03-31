"""Run numbered SQL migrations against the database."""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def run_migrations(conn_string: str, migrations_dir: Path):
    """Run all .sql files in order."""
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("No migration files found.")
        return

    with psycopg.connect(conn_string) as conn:
        # Track applied migrations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        conn.commit()

        for sql_file in sql_files:
            # Check if already applied
            row = conn.execute(
                "SELECT 1 FROM _migrations WHERE filename = %s",
                [sql_file.name],
            ).fetchone()

            if row:
                print(f"  SKIP (applied): {sql_file.name}")
                continue

            print(f"  APPLYING: {sql_file.name}")
            sql = sql_file.read_text(encoding="utf-8")
            conn.execute(sql)
            conn.execute(
                "INSERT INTO _migrations (filename) VALUES (%s)",
                [sql_file.name],
            )
            conn.commit()
            print(f"  OK: {sql_file.name}")


def main():
    # Try loading .env from apps/api/ first, then root
    env_path = Path(__file__).parent.parent / "apps" / "api" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "methlab")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")

    from urllib.parse import quote_plus
    conn_string = f"postgresql://{quote_plus(db_user)}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"

    migrations_dir = Path(__file__).parent.parent / "migrations"
    print(f"Running migrations from {migrations_dir}...")
    run_migrations(conn_string, migrations_dir)
    print("Done.")


if __name__ == "__main__":
    main()
