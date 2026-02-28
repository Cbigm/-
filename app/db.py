from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable

DB_PATH = Path("data/app.db")


SCHEMA_STATEMENTS: Iterable[str] = (
    """
    CREATE TABLE IF NOT EXISTS competitors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      asin TEXT NOT NULL UNIQUE,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competitor_assets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      competitor_id INTEGER NOT NULL,
      asset_type TEXT NOT NULL,
      module_index INTEGER,
      blob_id TEXT NOT NULL,
      FOREIGN KEY (competitor_id) REFERENCES competitors(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competitor_text (
      competitor_id INTEGER PRIMARY KEY,
      title_text TEXT NOT NULL,
      bullets_json TEXT NOT NULL,
      aplus_text_json TEXT NOT NULL,
      FOREIGN KEY (competitor_id) REFERENCES competitors(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competitor_analysis (
      competitor_id INTEGER PRIMARY KEY,
      analysis_json TEXT NOT NULL,
      embeddings TEXT,
      FOREIGN KEY (competitor_id) REFERENCES competitors(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS my_product (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS my_product_assets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      my_product_id INTEGER NOT NULL,
      asset_type TEXT NOT NULL,
      file_id TEXT,
      text_description TEXT,
      FOREIGN KEY (my_product_id) REFERENCES my_product(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS my_product_analysis (
      my_product_id INTEGER PRIMARY KEY,
      analysis_json TEXT NOT NULL,
      FOREIGN KEY (my_product_id) REFERENCES my_product(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS generated_plans (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      my_product_id INTEGER NOT NULL,
      plan_json TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (my_product_id) REFERENCES my_product(id)
    )
    """,
)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def dumps_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)
