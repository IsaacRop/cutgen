from cutgen_core.transcribe import TranscribeConfig, format_line, format_timestamp


def test_format_timestamp():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(65) == "01:05"
    assert format_timestamp(3725) == "62:05"


def test_format_line():
    assert format_line(1.2, 3.4, "  oi tudo bem  ") == "[00:01 - 00:03] oi tudo bem"


def test_transcribe_config_defaults_match_original_transcribe_py():
    config = TranscribeConfig()
    assert (config.model_size, config.sample_rate, config.chunk_seconds) == ("small", 16000, 180)


def test_transcribe_config_from_niche_config_partial_override():
    config = TranscribeConfig.from_niche_config({"transcribe": {"model_size": "medium", "chunk_seconds": 60}})
    assert config.model_size == "medium"
    assert config.chunk_seconds == 60
    assert config.sample_rate == 16000


def test_transcribe_config_from_niche_config_no_section():
    config = TranscribeConfig.from_niche_config({})
    assert config.model_size == "small"
