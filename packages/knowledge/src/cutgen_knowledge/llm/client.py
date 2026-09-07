"""
Abstracao de chamada de LLM, usada pelos quatro agentes quando rodam FORA do
Claude Code (fora de skill). Dentro do Claude Code, a skill nao passa por
aqui — o proprio modelo da sessao executa o prompt direto, sem chamada de API
extra.

Configuravel por env var pra nao prender ninguem a uma unica conta:
- CUTGEN_LLM_API_KEY       — chave da API (obrigatoria pra usar call())
- CUTGEN_LLM_BASE_URL      — endpoint, default e a API da Anthropic;
                                aceita qualquer endpoint compativel
- CUTGEN_LLM_MODEL_HEAVY   — modelo pra analyst/curator (roda sob demanda,
                                tolera latencia/custo maior)
- CUTGEN_LLM_MODEL_FAST    — modelo pra selector/writer (roda por clipe,
                                merece default mais barato/rapido)
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import anthropic


@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model_heavy: str
    model_fast: str

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            api_key=os.environ["CUTGEN_LLM_API_KEY"],
            base_url=os.environ.get("CUTGEN_LLM_BASE_URL", "https://api.anthropic.com"),
            model_heavy=os.environ.get("CUTGEN_LLM_MODEL_HEAVY", "claude-opus-5"),
            model_fast=os.environ.get("CUTGEN_LLM_MODEL_FAST", "claude-haiku-4-5"),
        )


def render_input(variables: dict) -> str:
    """Formata as variaveis do agente como um bloco de input legivel (secoes '## chave')."""
    lines = []
    for key, value in variables.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        lines.append(f"## {key}\n{value}")
    return "\n\n".join(lines)


def call(prompt_path: str, variables: dict, *, heavy: bool, config: LLMConfig | None = None) -> str:
    """
    Carrega o prompt em prompt_path como system prompt, renderiza variables como
    o turno do usuario, chama o modelo heavy ou fast conforme o parametro, e
    retorna o texto da resposta.
    """
    config = config or LLMConfig.from_env()
    system_prompt = Path(prompt_path).read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=config.api_key, base_url=config.base_url)
    response = client.messages.create(
        model=config.model_heavy if heavy else config.model_fast,
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": render_input(variables)}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
