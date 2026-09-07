from cutgen_core.render import (
    RenderConfig,
    ass_time,
    build_caption_events,
    build_ffmpeg_command,
    build_style_line,
    censor,
    pick_asset,
    write_ass,
)


def test_ass_time():
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(65.5) == "0:01:05.50"
    assert ass_time(3725.2) == "1:02:05.20"


def test_censor_uses_niche_config_not_hardcoded_list():
    config = RenderConfig.from_niche_config({"render": {"swears": ["DAMN"], "mask_from": "A", "mask_to": "@"}})
    assert censor("DAMN", config) == "D@MN"
    assert censor("fine", config) == "fine"


def test_build_caption_events_groups_and_highlights():
    words = [
        {"word": "oi", "start": 10.0, "end": 10.3},
        {"word": "tudo", "start": 10.3, "end": 10.6},
        {"word": "bem", "start": 10.6, "end": 11.0},
        {"word": "com", "start": 12.0, "end": 12.2},  # gap > 0.6s -> novo bloco
        {"word": "voce", "start": 12.2, "end": 12.5},
    ]
    config = RenderConfig()
    events = build_caption_events(words, start=10.0, end=13.0, dur=3.0, config=config)
    assert len(events) == 5
    assert events[0][0] == 0.0
    assert "{\\c&H00FFFF&}OI{\\c&HFFFFFF&}" in events[0][2]


def test_build_style_line_uses_config():
    style = build_style_line(RenderConfig())
    assert style.startswith("Style: Base,Arial,90,&H00FFFFFF,")


def test_write_ass_writes_real_file(tmp_path):
    config = RenderConfig()
    events = [(0.0, 1.0, "OI")]
    out = write_ass(events, tmp_path / "out.ass", config)
    text = out.read_text(encoding="utf-8")
    assert "[V4+ Styles]" in text
    assert "Dialogue: 0," in text


def test_pick_asset(tmp_path):
    assert pick_asset(tmp_path / "nao-existe") is None
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    (music_dir / "track1.mp3").write_bytes(b"fake")
    assert pick_asset(music_dir).name == "track1.mp3"


def test_build_ffmpeg_command_with_music(tmp_path):
    config = RenderConfig()
    cmd = build_ffmpeg_command(
        video_path=tmp_path / "in.mp4", ass_path=tmp_path / "out.ass", output_path=tmp_path / "out.mp4",
        start=10.0, end=13.0, music_path=tmp_path / "track1.mp3", config=config,
    )
    assert cmd[0] == "ffmpeg"
    assert "-filter_complex" in cmd
    assert any("loudnorm=I=-14.0" in c for c in cmd)
    assert any("loudnorm=I=-26.0" in c for c in cmd)


def test_build_ffmpeg_command_without_music(tmp_path):
    config = RenderConfig()
    cmd = build_ffmpeg_command(
        video_path=tmp_path / "in.mp4", ass_path=tmp_path / "out.ass", output_path=tmp_path / "out.mp4",
        start=10.0, end=13.0, music_path=None, config=config,
    )
    assert "-filter_complex" not in cmd
    assert "-af" in cmd
