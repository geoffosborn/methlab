"""Database connection helpers using psycopg3."""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


def get_connection_string() -> str:
    return get_settings().database_url


def db_execute(
    sql: str,
    params: list[Any] | None = None,
    fetch: str = "all",
) -> list[dict] | dict | None:
    """Execute a query and return results.

    Args:
        sql: SQL query string with %s placeholders
        params: Query parameters
        fetch: 'all', 'one', or 'none'
    """
    with psycopg.connect(get_connection_string()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or [])
            if fetch == "one":
                return cur.fetchone()
            elif fetch == "all":
                return cur.fetchall()
            else:
                conn.commit()
                return None


def db_execute_returning(
    sql: str,
    params: list[Any] | None = None,
) -> dict | None:
    """Execute a modification query with RETURNING clause."""
    with psycopg.connect(get_connection_string()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or [])
            result = cur.fetchone()
            conn.commit()
            return result
