"""
Decide se um padrao tem evidencia suficiente pra ser promovido: descarta
clipes com amostra abaixo de um piso minimo de views (metrica de amostra
pequena e ruido — o mecanismo, nao o valor especifico de nenhum canal) e
compara a mediana de quem cita o padrao contra a mediana geral dos clipes
com amostra suficiente.

Os limiares (piso de amostra, minimo de clipes, razao minima) vem de
niches/<niche>/config.yaml, secao `agent` — os defaults aqui sao
conservadores e genericos, nao os valores medidos por nenhum canal real.
"""

import statistics

DEFAULT_MIN_SAMPLE_VIEWS = 100
DEFAULT_MIN_SAMPLES = 3
DEFAULT_MIN_RATIO = 1.5


def has_sufficient_sample(clip: dict, min_sample_views: int = DEFAULT_MIN_SAMPLE_VIEWS) -> bool:
    performance = clip.get("performance") or {}
    views = performance.get("views")
    return views is not None and views >= min_sample_views


def pattern_performance(clips: list[dict], pattern_id: str,
                         min_sample_views: int = DEFAULT_MIN_SAMPLE_VIEWS) -> dict | None:
    """
    {pattern_id, sample_size, median_views, baseline_median, ratio} pra um
    padrao, ou None se nao houver amostra suficiente pra medir.
    """
    sufficient = [c for c in clips if has_sufficient_sample(c, min_sample_views)]
    if not sufficient:
        return None
    baseline_median = statistics.median(c["performance"]["views"] for c in sufficient)

    matching = [c for c in sufficient if pattern_id in (c.get("pattern_refs") or [])]
    if not matching:
        return None
    median_views = statistics.median(c["performance"]["views"] for c in matching)

    return {
        "pattern_id": pattern_id,
        "sample_size": len(matching),
        "median_views": median_views,
        "baseline_median": baseline_median,
        "ratio": (median_views / baseline_median) if baseline_median else None,
    }


def promotable_patterns(clips: list[dict], *, min_sample_views: int = DEFAULT_MIN_SAMPLE_VIEWS,
                         min_samples: int = DEFAULT_MIN_SAMPLES,
                         min_ratio: float = DEFAULT_MIN_RATIO) -> list[dict]:
    """
    Varre todos os pattern_refs distintos citados nos clipes e retorna os
    que tem amostra e efeito suficientes pra virar candidato de promocao
    (ver cutgen_agent.promote).
    """
    all_patterns = {p for c in clips for p in (c.get("pattern_refs") or [])}
    results = []
    for pattern_id in sorted(all_patterns):
        perf = pattern_performance(clips, pattern_id, min_sample_views)
        if perf and perf["sample_size"] >= min_samples and perf["ratio"] is not None and perf["ratio"] >= min_ratio:
            results.append(perf)
    return results
