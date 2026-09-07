"""
Agente writer — versao callable (fora do Claude Code).
Dentro do core, cutgen_core.write.write chama isso (ou a skill make-cut,
se estiver rodando dentro do Claude Code).
"""

from pathlib import Path

from cutgen_knowledge.llm.client import LLMConfig, call

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "writer.md"


def run(clip_transcript: str, theme: str, niche: str, niche_config: dict,
        patterns_md: str | None, config: LLMConfig | None = None) -> str:
    """
    clip_transcript: transcricao do trecho ja escolhido pelo selector.
    theme: tema/resumo curto do trecho.
    niche_config: conteudo relevante de niches/<niche>/config.yaml (idioma,
    hashtags-base, convencoes de marca).

    Retorna o texto cru no formato TITULO/DESCRICAO/HASHTAGS descrito em
    prompts/writer.md — quem chama grava em output/<name>.txt.

    Roda por clipe, entao usa o modelo "fast" por padrao.
    """
    return call(
        str(PROMPT_PATH),
        {
            "niche": niche,
            "clip_transcript": clip_transcript,
            "theme": theme,
            "niche_config": niche_config,
            "patterns_md": patterns_md or "",
        },
        heavy=False,
        config=config,
    )
