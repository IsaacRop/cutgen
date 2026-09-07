"""
Banco local (SQLite) dos clipes publicados e sua performance — a memoria
persistente do agent entre execucoes. Cada linha segue o contrato de
packages/shared/metrics_schema.json (cutgen_shared): so os campos ali
listados como obrigatorios sao exigidos na escrita.
"""

import json
import sqlite3
from pathlib import Path

from cutgen_shared import load_metrics_schema

REQUIRED_FIELDS = load_metrics_schema()["required"]


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clips (
            clip_id TEXT PRIMARY KEY,
            niche TEXT NOT NULL,
            source_url TEXT NOT NULL,
            duration_seconds REAL NOT NULL,
            format TEXT NOT NULL,
            platform TEXT NOT NULL,
            published_at TEXT NOT NULL,
            pattern_refs TEXT,
            performance TEXT
        )
        """
    )
    conn.commit()
    return conn


def validate_clip(clip: dict) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in clip]
    if missing:
        raise ValueError(f"clip invalido, faltam campos obrigatorios: {missing}")


def upsert_clip(conn: sqlite3.Connection, clip: dict) -> None:
    """Insere ou atualiza um clipe. Preserva performance ja coletada se o
    upsert nao trouxer uma nova (ex.: reprocessar metadata sem re-medir)."""
    validate_clip(clip)
    conn.execute(
        """
        INSERT INTO clips (clip_id, niche, source_url, duration_seconds, format, platform,
                            published_at, pattern_refs, performance)
        VALUES (:clip_id, :niche, :source_url, :duration_seconds, :format, :platform,
                :published_at, :pattern_refs, :performance)
        ON CONFLICT(clip_id) DO UPDATE SET
            niche=excluded.niche, source_url=excluded.source_url,
            duration_seconds=excluded.duration_seconds, format=excluded.format,
            platform=excluded.platform, published_at=excluded.published_at,
            pattern_refs=excluded.pattern_refs,
            performance=COALESCE(excluded.performance, clips.performance)
        """,
        {
            "clip_id": clip["clip_id"],
            "niche": clip["niche"],
            "source_url": clip["source_url"],
            "duration_seconds": clip["duration_seconds"],
            "format": clip["format"],
            "platform": clip["platform"],
            "published_at": clip["published_at"],
            "pattern_refs": json.dumps(clip.get("pattern_refs", []), ensure_ascii=False),
            "performance": json.dumps(clip["performance"], ensure_ascii=False) if clip.get("performance") else None,
        },
    )
    conn.commit()


def update_performance(conn: sqlite3.Connection, clip_id: str, performance: dict) -> None:
    conn.execute(
        "UPDATE clips SET performance = ? WHERE clip_id = ?",
        (json.dumps(performance, ensure_ascii=False), clip_id),
    )
    conn.commit()


def _row_to_clip(row: sqlite3.Row) -> dict:
    clip = dict(row)
    clip["pattern_refs"] = json.loads(clip["pattern_refs"]) if clip["pattern_refs"] else []
    clip["performance"] = json.loads(clip["performance"]) if clip["performance"] else None
    return clip


def get_clip(conn: sqlite3.Connection, clip_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM clips WHERE clip_id = ?", (clip_id,)).fetchone()
    return _row_to_clip(row) if row else None


def list_clips(conn: sqlite3.Connection, *, niche: str | None = None) -> list[dict]:
    if niche:
        rows = conn.execute("SELECT * FROM clips WHERE niche = ?", (niche,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM clips").fetchall()
    return [_row_to_clip(r) for r in rows]
