from cutgen_shared import load_metrics_schema


def test_schema_has_expected_required_fields():
    schema = load_metrics_schema()
    assert schema["title"] == "cutgen clip metrics"
    assert set(schema["required"]) == {
        "clip_id", "niche", "source_url", "duration_seconds", "format", "platform", "published_at",
    }


def test_schema_defines_performance_object():
    schema = load_metrics_schema()
    performance = schema["properties"]["performance"]["properties"]
    assert {"views", "likes", "comments", "retention_pct", "collected_at"} <= set(performance.keys())
