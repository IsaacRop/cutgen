"""
Gera a metadata de publicacao do corte: chama o agente writer (cutgen_knowledge)
e escreve output/<name>.txt. O parsing de titulo/descricao/hashtags (usado
pelo manifest, ver GTclips real manifest.py:parse_writer_txt) mora aqui
porque e o formato que o proprio writer produz.
"""

from pathlib import Path

from cutgen_knowledge.agents import writer as writer_agent
from cutgen_knowledge.llm.client import LLMConfig

_HEADERS = {
    "TÍTULO": "title", "TITULO": "title",
    "DESCRIÇÃO": "description", "DESCRICAO": "description",
    "HASHTAGS": "hashtags",
}


def parse_writer_output(raw: str) -> dict:
    """
    Extrai title/description/hashtags/tags do texto do writer (secoes
    TITULO/DESCRICAO/HASHTAGS), ignorando titulos alternativos/notas depois
    de uma linha '---'.
    """
    raw = raw.split("\n---", 1)[0]
    sections: dict[str, list[str]] = {}
    current = None
    for line in raw.splitlines():
        key = _HEADERS.get(line.strip().upper())
        if key:
            current = key
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    out: dict = {}
    if sections.get("title"):
        lines = [l.strip() for l in sections["title"] if l.strip()]
        out["title"] = lines[0] if lines else None
    if "description" in sections:
        out["description"] = "\n".join(sections["description"]).strip()
    if "hashtags" in sections:
        tags_line = " ".join(l.strip() for l in sections["hashtags"]).strip()
        out["hashtags"] = tags_line
        out["tags"] = [t.lstrip("#") for t in tags_line.split() if t.startswith("#")]
    return out


def write(clip_transcript: str, theme: str, niche: str, niche_config: dict, name: str,
          output_dir: Path = Path("output"), knowledge_dir: Path = Path("knowledge"),
          llm_config: LLMConfig | None = None) -> Path:
    """Roda o writer de verdade (chamada LLM) e escreve output/<name>.txt."""
    patterns_path = knowledge_dir / "niches" / niche / "PATTERNS.md"
    patterns_md = patterns_path.read_text(encoding="utf-8") if patterns_path.exists() else None

    raw = writer_agent.run(clip_transcript, theme, niche, niche_config, patterns_md, config=llm_config)
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{name}.txt"
    out.write_text(raw, encoding="utf-8")
    return out
