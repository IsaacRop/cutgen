"""
Agente curator — versao callable (fora do Claude Code).
Consolida exemplos em padroes destilados. Retorna o relatorio do modelo
(o que reforcou/criou/deixou pendente); aplicar as edicoes nos arquivos de
knowledge/niches/<niche>/patterns/ e no PATTERNS.md e responsabilidade de
quem chama (dentro do Claude Code, isso e o proprio skill/Write; fora, cabe
ao core/agent orquestrar a partir do relatorio).
"""

from pathlib import Path

from cutgen_knowledge.llm.client import LLMConfig, call

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "curator.md"


def run(examples_md: list[str], patterns_md: list[str], index_md: str, niche: str,
        config: LLMConfig | None = None) -> str:
    """
    examples_md: conteudo de cada arquivo em knowledge/niches/<niche>/examples/.
    patterns_md: conteudo de cada arquivo em knowledge/niches/<niche>/patterns/.
    index_md: conteudo atual de knowledge/niches/<niche>/PATTERNS.md.

    Roda sob demanda (consolidacao manual), entao usa o modelo "heavy".
    """
    return call(
        str(PROMPT_PATH),
        {
            "niche": niche,
            "examples_md": examples_md,
            "patterns_md": patterns_md,
            "index_md": index_md,
        },
        heavy=True,
        config=config,
    )
