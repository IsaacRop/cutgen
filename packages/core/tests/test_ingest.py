import json

import pytest
from cutgen_core import ingest


def test_platform_of():
    assert ingest.platform_of("https://www.youtube.com/watch?v=abc") == "youtube"
    assert ingest.platform_of("https://www.instagram.com/reel/xyz") == "instagram"
    assert ingest.platform_of("https://example.com/v") == "other"


def test_slugify():
    assert ingest.slugify("Um Titulo Bem Louco! Com Pontuacao...") == "um-titulo-bem-louco-com-pontuacao"
    assert ingest.slugify("") == "ref"


def test_build_download_command_with_options():
    cmd = ingest.build_download_command(
        "URL", "out/%(id)s.%(ext)s",
        {"cookies_from_browser": "firefox", "js_runtimes": "node"},
        write_info_json=True,
    )
    assert cmd[0] == "yt-dlp"
    assert "--cookies-from-browser" in cmd and "firefox" in cmd
    assert "--js-runtimes" in cmd and "node" in cmd
    assert "--write-info-json" in cmd
    assert cmd[-2:] == ["out/%(id)s.%(ext)s", "URL"]


def test_build_download_command_defaults():
    cmd = ingest.build_download_command("URL", "out/%(id)s.%(ext)s")
    assert "--cookies-from-browser" not in cmd
    assert "--write-info-json" not in cmd


def test_read_info_json(tmp_path):
    (tmp_path / "abc123.info.json").write_text(json.dumps({"id": "abc123"}), encoding="utf-8")
    info = ingest.read_info_json(tmp_path)
    assert info["id"] == "abc123"


def test_read_info_json_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest.read_info_json(tmp_path)


def test_write_reference_example(tmp_path):
    examples_dir = tmp_path / "examples"
    out = ingest.write_reference_example(
        examples_dir=examples_dir,
        info={
            "title": "Um Corte Incrivel", "uploader": "canal_x", "view_count": 12345,
            "like_count": 900, "comment_count": 10, "duration": 42,
            "webpage_url": "https://youtu.be/abc123",
        },
        transcript="isso e uma transcricao de teste",
        language="pt",
        video_id="abc123",
        url="https://youtu.be/abc123",
    )
    text = out.read_text(encoding="utf-8")
    assert "link: https://youtu.be/abc123" in text
    assert "platform: youtube" in text
    assert "author: canal_x" in text
    assert "views: 12345" in text
    assert "isso e uma transcricao de teste" in text
    assert "## Padrões identificados" in text
