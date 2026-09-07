"""
Carrega niches/<niche>/config.yaml — o unico lugar onde valores especificos
de nicho (fontes de conteudo, template visual, hashtags-base, marca) entram
no pipeline. O core em si nao hardcoda nada disso.
"""

import os
from pathlib import Path

import yaml


def niches_root() -> Path:
    """Raiz do diretorio niches/, por padrao relativa ao cwd (override via CUTGEN_NICHES_DIR)."""
    return Path(os.environ.get("CUTGEN_NICHES_DIR", "niches"))


def load_niche_config(niche: str, niches_dir: Path | None = None) -> dict:
    """Le niches/<niche>/config.yaml e retorna o dict resultante."""
    root = niches_dir or niches_root()
    config_path = root / niche / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"config nao encontrado para o nicho {niche!r}: {config_path}")
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
