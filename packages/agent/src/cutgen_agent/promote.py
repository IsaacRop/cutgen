"""
Promove um padrao com evidencia suficiente (cutgen_agent.significance) pra
knowledge/niches/<niche>/patterns/<id>.md, seguindo as mesmas regras de
confianca do curator (packages/knowledge/prompts/curator.md): baixa=1
amostra, moderada=2-3, alta>=4-5.

Fecha o loop que o GTclips real ainda faz manualmente via /consolidate: aqui
a promocao acontece automaticamente a partir de performance medida.
"""

from datetime import UTC, datetime
from pathlib import Path

from cutgen_agent import significance, store

CONFIDENCE_THRESHOLDS = (
    (5, "alta"),
    (2, "moderada"),
    (1, "baixa"),
)

PATTERN_TEMPLATE = """# {pattern_id}

- confianca: {confidence}
- amostra: {sample_size}
- atualizado: {updated}
- razao vs baseline: {ratio:.2f}x (mediana {median_views:.0f} vs {baseline_median:.0f} views)

Promovido automaticamente pelo agent a partir de performance medida
(cutgen_agent.significance). Revise e complete a descricao do padrao.
"""


def confidence_for_sample(sample_size: int) -> str:
    for min_samples, label in CONFIDENCE_THRESHOLDS:
        if sample_size >= min_samples:
            return label
    return "baixa"


def promote_pattern(perf: dict, *, niche: str, knowledge_dir: Path = Path("knowledge"),
                     today: str | None = None) -> Path:
    """Escreve/atualiza knowledge/niches/<niche>/patterns/<pattern_id>.md."""
    patterns_dir = knowledge_dir / "niches" / niche / "patterns"
    patterns_dir.mkdir(parents=True, exist_ok=True)
    out = patterns_dir / f"{perf['pattern_id']}.md"
    out.write_text(
        PATTERN_TEMPLATE.format(
            pattern_id=perf["pattern_id"],
            confidence=confidence_for_sample(perf["sample_size"]),
            sample_size=perf["sample_size"],
            updated=today or datetime.now(UTC).date().isoformat(),
            ratio=perf["ratio"],
            median_views=perf["median_views"],
            baseline_median=perf["baseline_median"],
        ),
        encoding="utf-8",
    )
    return out


def update_index(index_path: Path, promoted: list[Path]) -> Path:
    """Atualiza (ou cria) knowledge/niches/<niche>/PATTERNS.md com uma linha por padrao novo."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Padrões\n\n"
    lines = existing.splitlines()
    known = {line[2:].split("—")[0].strip() for line in lines if line.startswith("- ")}
    for path in promoted:
        pattern_id = path.stem
        if pattern_id not in known:
            lines.append(f"- {pattern_id} — promovido pelo agent (ver {path.name})")
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def run_promotion_cycle(db_path: Path, niche: str, knowledge_dir: Path = Path("knowledge"),
                         **thresholds) -> list[Path]:
    """Le o store, mede significancia e promove os padroes qualificados. Retorna os arquivos escritos."""
    conn = store.open_db(db_path)
    try:
        clips = store.list_clips(conn, niche=niche)
    finally:
        conn.close()
    promotable = significance.promotable_patterns(clips, **thresholds)
    promoted_paths = [promote_pattern(p, niche=niche, knowledge_dir=knowledge_dir) for p in promotable]
    if promoted_paths:
        update_index(knowledge_dir / "niches" / niche / "PATTERNS.md", promoted_paths)
    return promoted_paths


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Roda o ciclo collect->store->significance->promote pra um nicho."
    )
    parser.add_argument("--niche", required=True)
    parser.add_argument("--db", default="agent.sqlite3")
    parser.add_argument("--knowledge-dir", default="knowledge")
    parser.add_argument("--min-sample-views", type=int, default=significance.DEFAULT_MIN_SAMPLE_VIEWS)
    parser.add_argument("--min-samples", type=int, default=significance.DEFAULT_MIN_SAMPLES)
    parser.add_argument("--min-ratio", type=float, default=significance.DEFAULT_MIN_RATIO)
    args = parser.parse_args()

    promoted = run_promotion_cycle(
        Path(args.db), args.niche, Path(args.knowledge_dir),
        min_sample_views=args.min_sample_views, min_samples=args.min_samples, min_ratio=args.min_ratio,
    )
    if promoted:
        for path in promoted:
            print(f"promovido -> {path}")
    else:
        print("nenhum padrao com evidencia suficiente ainda")


if __name__ == "__main__":
    main()
