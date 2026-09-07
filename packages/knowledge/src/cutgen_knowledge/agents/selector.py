"""
Agente selector — versao callable (fora do Claude Code).
Dentro do core, cutgen_core.select.select chama isso (ou a skill make-cut,
se estiver rodando dentro do Claude Code).
"""

from pathlib import Path

from cutgen_knowledge.llm.client import LLMConfig, call

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "selector.md"


def run(transcript: str, words: list[dict], niche: str, patterns_md: str | None,
        config: LLMConfig | None = None) -> str:
    """
    transcript: texto legivel com timestamps (processing/<stem>.txt).
    words: timestamps por palavra (processing/<stem>.words.json), pra cravar start/end.

    Retorna o texto cru no formato TRECHO/GANCHO/POR QUE/PADROES/RISCOS
    descrito em prompts/selector.md — quem chama faz o parsing conforme o
    proprio formato do pipeline.

    Roda por video fonte, entao usa o modelo "fast" por padrao.
    """
    return call(
        str(PROMPT_PATH),
        {"niche": niche, "transcript": transcript, "words": words, "patterns_md": patterns_md or ""},
        heavy=False,
        config=config,
    )
