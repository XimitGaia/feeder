"""Persistência em SQLite (v1). Simples, zero infra; migrar para Postgres é um
ADR futuro. Guarda o item serializado (JSON) + dedup_key única para idempotência
entre execuções do feeder.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.core.interfaces import IStorage
from src.core.models import Item

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id         TEXT PRIMARY KEY,
    dedup_key  TEXT UNIQUE,
    tipo       TEXT NOT NULL,
    titulo     TEXT NOT NULL,
    url        TEXT,
    fonte      TEXT,
    coletado_em TEXT,
    payload    TEXT NOT NULL
);
"""


class SQLiteStorage(IStorage):
    def __init__(self, db_path: str):
        self._path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def exists(self, dedup_key: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute("SELECT 1 FROM items WHERE dedup_key = ?", (dedup_key,))
            return cur.fetchone() is not None

    def list_recent(self, tipo: str | None = None, limit: int = 20) -> list[Item]:
        sql = "SELECT payload FROM items"
        params: list = []
        if tipo:
            sql += " WHERE tipo = ?"
            params.append(tipo)
        sql += " ORDER BY coletado_em DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Item.model_validate_json(payload) for (payload,) in rows]

    def save(self, item: Item) -> bool:
        try:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO items (id, dedup_key, tipo, titulo, url, fonte, coletado_em, payload)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.id,
                        item.dedup_key,
                        item.tipo.value,
                        item.titulo,
                        item.url,
                        item.fonte,
                        item.coletado_em.isoformat(),
                        item.model_dump_json(),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False  # já existia (dedup_key UNIQUE) — idempotente
