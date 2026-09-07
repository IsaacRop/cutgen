"""
Agente analyst — versao callable (fora do Claude Code).
Preenche estrutura/porque/padroes de uma referencia ja transcrita. Retorna o
markdown pronto pra sobrescrever o proprio arquivo do exemplo (nao ha
parsing: o texto do modelo E o conteudo final das secoes).
"""

from pathlib import Path

from cutgen_knowledge.llm.client import LLMConfig, call

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "analyst.md"


def run(example_md: str, patterns_md: str, niche: str, config: LLMConfig | None = None) -> str:
    """
    example_md: conteudo atual do arquivo em knowledge/niches/<niche>/examples/
    (frontmatter + transcricao, secoes Estrutura/Por que/Padroes vazias).
    patterns_md: conteudo de knowledge/niches/<niche>/PATTERNS.md, pra reusar IDs.

    Roda sob demanda (por referencia ingerida), entao usa o modelo "heavy".
    """
    return call(
        str(PROMPT_PATH),
        {"niche": niche, "example_md": example_md, "patterns_md": patterns_md},
        heavy=True,
        config=config,
    )
