import pytest

from cutgen_agent import collect, promote, significance, store

BASE_CLIP = dict(
    niche="example-niche", source_url="https://youtu.be/x", duration_seconds=28.0,
    format="causo", platform="youtube_shorts", published_at="2026-01-01T00:00:00Z",
)


def test_store_rejects_incomplete_clip(tmp_path):
    conn = store.open_db(tmp_path / "agent.sqlite3")
    with pytest.raises(ValueError):
        store.upsert_clip(conn, {"clip_id": "c1"})
    conn.close()


def _seed(conn):
    clips = [
        ("c1", ["padrao-a"]), ("c2", ["padrao-a"]), ("c3", ["padrao-a"]),
        ("c4", []), ("c5", []), ("c6", []),
        ("c7", ["padrao-b"]), ("c8", []),
    ]
    for clip_id, patterns in clips:
        store.upsert_clip(conn, {**BASE_CLIP, "clip_id": clip_id, "pattern_refs": patterns})


def test_collect_and_store_writes_real_performance(tmp_path):
    conn = store.open_db(tmp_path / "agent.sqlite3")
    _seed(conn)

    result = collect.collect_and_store(
        conn, "c1", video_id="yt-c1", api_key="fake",
        fetch_fn=lambda vid, key: {"views": 500, "likes": None, "comments": None, "collected_at": "x"},
    )
    assert result["views"] == 500

    clip = store.get_clip(conn, "c1")
    assert clip["performance"]["views"] == 500
    assert clip["pattern_refs"] == ["padrao-a"]
    conn.close()


def _views(clip_id):
    return {
        "c1": 500, "c2": 600, "c3": 550, "c4": 80, "c5": 90, "c6": 100, "c7": 120, "c8": 110,
    }[clip_id]


def test_full_promotion_cycle(tmp_path):
    db_path = tmp_path / "agent.sqlite3"
    conn = store.open_db(db_path)
    _seed(conn)
    for clip_id in ("c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"):
        collect.collect_and_store(
            conn, clip_id, video_id=f"yt-{clip_id}", api_key="fake",
            fetch_fn=lambda vid, key, v=_views(clip_id): {
                "views": v, "likes": None, "comments": None, "collected_at": "x",
            },
        )
    clips = store.list_clips(conn, niche="example-niche")
    conn.close()
    assert len(clips) == 8

    perf_a = significance.pattern_performance(clips, "padrao-a")
    assert perf_a["sample_size"] == 3
    assert perf_a["ratio"] > 1.5

    promotable = significance.promotable_patterns(clips, min_samples=3, min_ratio=1.5, min_sample_views=100)
    ids = [p["pattern_id"] for p in promotable]
    assert ids == ["padrao-a"]  # padrao-b fica de fora: so 1 amostra

    knowledge_dir = tmp_path / "knowledge"
    promoted_paths = [
        promote.promote_pattern(p, niche="example-niche", knowledge_dir=knowledge_dir) for p in promotable
    ]
    text = promoted_paths[0].read_text(encoding="utf-8")
    assert "# padrao-a" in text
    assert "confianca: moderada" in text  # 3 amostras -> moderada pelas regras do curator

    index_path = knowledge_dir / "niches" / "example-niche" / "PATTERNS.md"
    promote.update_index(index_path, promoted_paths)
    assert "padrao-a" in index_path.read_text(encoding="utf-8")

    promoted2 = promote.run_promotion_cycle(
        db_path, "example-niche", knowledge_dir, min_samples=3, min_ratio=1.5, min_sample_views=100,
    )
    assert len(promoted2) == 1


def test_confidence_bands_match_curator_rules():
    assert promote.confidence_for_sample(1) == "baixa"
    assert promote.confidence_for_sample(3) == "moderada"
    assert promote.confidence_for_sample(5) == "alta"
