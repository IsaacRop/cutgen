"""cutgen_shared — contrato entre core e agent. So schema, sem logica de negocio."""
import json
from importlib import resources


def load_metrics_schema() -> dict:
    """Carrega o metrics_schema.json como dict, pra quem quiser validar contra ele."""
    with resources.files("cutgen_shared").joinpath("metrics_schema.json").open("r", encoding="utf-8") as f:
        return json.load(f)
