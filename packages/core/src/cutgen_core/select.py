"""
Escolhe o trecho do corte: le a transcricao + words.json de processing/,
chama o agente selector (cutgen_knowledge) e faz o parsing do formato
TRECHO/GANCHO/POR QUE/PADROES/RISCOS descrito em prompts/selector.md.
"""

import json
import re
from pathlib import Path

from cutgen_knowledge.agents import selector as selector_agent
from cutgen_knowledge.llm.client import LLMConfig

_TRECHO_RE = re.compile(r"TRECHO(?:\s*\(([^)]*)\))?:\s*start=([\d.]+)\s*end=([\d.]+)", re.IGNORECASE)
_GANCHO_RE = re.compile(r"GANCHO[^:]*:\s*(.+)")
_POR_QUE_RE = re.compile(r"POR QU[EÊ]:\s*(.+?)(?=\nPADR|\Z)", re.IGNORECASE | re.DOTALL)
_PADROES_RE = re.compile(r"PADR[ÕO]ES:\s*\[(.*?)\]", re.IGNORECASE)
_RISCOS_RE = re.compile(r"RISCOS:\s*(.+)")


def parse_selector_output(raw: str) -> list[dict]:
    """Um dict por candidato ('TRECHO: start=... end=...'), na ordem em que aparecem."""
    blocks = re.split(r"(?=TRECHO:)", raw)
    candidates = []
    for block in blocks:
        m = _TRECHO_RE.search(block)
        if not m:
            continue
        gancho_m = _GANCHO_RE.search(block)
        por_que_m = _POR_QUE_RE.search(block)
        padroes_m = _PADROES_RE.search(block)
        riscos_m = _RISCOS_RE.search(block)
        marker = m.group(1) or ""
        candidates.append({
            "start": float(m.group(2)),
            "end": float(m.group(3)),
            "gancho": gancho_m.group(1).strip().strip('"') if gancho_m else "",
            "why": por_que_m.group(1).strip() if por_que_m else "",
            "patterns": [p.strip() for p in padroes_m.group(1).split(",") if p.strip()] if padroes_m else [],
            "risks": riscos_m.group(1).strip() if riscos_m else "",
            "recommended": "recomendado" in marker.lower(),
        })
    return candidates


def load_selector_inputs(stem: str, niche: str, processing_dir: Path = Path("processing"),
                          knowledge_dir: Path = Path("knowledge")) -> tuple[str, list[dict], str | None]:
    """Le processing/<stem>.txt + .words.json e knowledge/niches/<niche>/PATTERNS.md (se existir)."""
    transcript = (processing_dir / f"{stem}.txt").read_text(encoding="utf-8")
    words = json.loads((processing_dir / f"{stem}.words.json").read_text(encoding="utf-8"))
    patterns_path = knowledge_dir / "niches" / niche / "PATTERNS.md"
    patterns_md = patterns_path.read_text(encoding="utf-8") if patterns_path.exists() else None
    return transcript, words, patterns_md


def select(stem: str, niche: str, processing_dir: Path = Path("processing"),
           knowledge_dir: Path = Path("knowledge"), llm_config: LLMConfig | None = None) -> list[dict]:
    """Roda o selector de verdade (chamada LLM) e retorna os candidatos ja parseados."""
    transcript, words, patterns_md = load_selector_inputs(stem, niche, processing_dir, knowledge_dir)
    raw = selector_agent.run(transcript, words, niche, patterns_md, config=llm_config)
    return parse_selector_output(raw)
