from pathlib import Path

import pytest

from cutgen_core.config import load_niche_config


def test_load_niche_config_reads_yaml(tmp_path):
    niche_dir = tmp_path / "niches" / "example-niche"
    niche_dir.mkdir(parents=True)
    (niche_dir / "config.yaml").write_text("download:\n  format: bv*+ba/b\n", encoding="utf-8")

    config = load_niche_config("example-niche", niches_dir=tmp_path / "niches")
    assert config["download"]["format"] == "bv*+ba/b"


def test_load_niche_config_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_niche_config("nao-existe", niches_dir=tmp_path / "niches")


def test_example_niche_config_loads_from_repo():
    repo_root = Path(__file__).resolve().parents[3]
    config = load_niche_config("example-niche", niches_dir=repo_root / "niches")
    assert config["niche"] == "example-niche"
    assert "download" in config and "render" in config and "publish" in config
