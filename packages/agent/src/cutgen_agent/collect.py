"""
Coleta performance publicada (views/likes/comentarios) via YouTube Data API
(so uma API key publica, videos.list — sem OAuth, diferente do publish que
precisa do token de upload) e atualiza o registro do clipe em
cutgen_agent.store.
"""

import json
import sqlite3
import urllib.request
from datetime import UTC, datetime

from cutgen_agent import store


def fetch_youtube_stats(video_id: str, api_key: str) -> dict:
    """Chamada real a Data API v3 (videos.list?part=statistics). Precisa de rede."""
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=statistics&key={api_key}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("items") or []
    if not items:
        raise ValueError(f"video nao encontrado: {video_id}")
    stats = items[0]["statistics"]
    return {
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats["likeCount"]) if "likeCount" in stats else None,
        "comments": int(stats["commentCount"]) if "commentCount" in stats else None,
        "collected_at": datetime.now(UTC).isoformat(),
    }


def collect_and_store(conn: sqlite3.Connection, clip_id: str, video_id: str, api_key: str,
                       fetch_fn=fetch_youtube_stats) -> dict:
    """
    Busca performance atual e grava em cutgen_agent.store. fetch_fn e
    injetavel pra testar a integracao com o store sem bater na rede.
    """
    performance = fetch_fn(video_id, api_key)
    store.update_performance(conn, clip_id, performance)
    return performance
