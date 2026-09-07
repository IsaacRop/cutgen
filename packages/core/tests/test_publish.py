from cutgen_core.publish import DEFAULT_PUBLISH_CONFIG, build_video_body


def test_build_video_body_truncates_title_and_uses_generic_defaults():
    body = build_video_body(title="X" * 150, description="desc", tags=["a", "b"], niche_config={})
    assert len(body["snippet"]["title"]) == 100
    assert body["snippet"]["categoryId"] == DEFAULT_PUBLISH_CONFIG["category_id"]
    assert body["status"]["privacyStatus"] == "public"


def test_build_video_body_respects_niche_overrides():
    body = build_video_body(
        title="curto", description="d", tags=[],
        niche_config={"publish": {"category_id": "20", "default_language": "pt-BR", "privacy": "unlisted"}},
    )
    assert body["snippet"]["categoryId"] == "20"
    assert body["snippet"]["defaultLanguage"] == "pt-BR"
    assert body["status"]["privacyStatus"] == "unlisted"
