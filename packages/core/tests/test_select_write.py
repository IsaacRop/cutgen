import json

from cutgen_core.select import load_selector_inputs, parse_selector_output
from cutgen_core.write import parse_writer_output

SELECTOR_RAW = """TRECHO (RECOMENDADO): start=12.5 end=48.0 (dur ~35.5s)
GANCHO (0-3s): "gancho forte"
POR QUÊ: causo concreto, escalada ate o final.
PADRÕES: [causo-concreto-titulo-resultado (alta), fecho-sem-cta (alta)]
RISCOS: nenhum

TRECHO: start=90.0 end=115.0 (dur ~25s)
GANCHO (0-3s): "opcao mais fraca"
POR QUÊ: hook ok mas corpo fraco.
PADRÕES: [hook-tese-polemica-porem (moderada)]
RISCOS: corte de b-roll no meio
"""

WRITER_RAW = """TÍTULO
Um titulo bem forte aqui

DESCRIÇÃO
Linha 1 da descricao.
Linha 2 da descricao.

HASHTAGS
#nicho #shorts #viral

---
Titulos alternativos:
- Outro titulo
Padroes usados: causo-concreto (alta)
"""


def test_parse_selector_output_two_candidates():
    candidates = parse_selector_output(SELECTOR_RAW)
    assert len(candidates) == 2

    c0 = candidates[0]
    assert (c0["start"], c0["end"]) == (12.5, 48.0)
    assert c0["gancho"] == "gancho forte"
    assert c0["recommended"] is True
    assert c0["patterns"] == ["causo-concreto-titulo-resultado (alta)", "fecho-sem-cta (alta)"]

    c1 = candidates[1]
    assert (c1["start"], c1["end"]) == (90.0, 115.0)
    assert c1["recommended"] is False


def test_load_selector_inputs_reads_real_files(tmp_path):
    processing_dir = tmp_path / "processing"
    processing_dir.mkdir()
    (processing_dir / "corte01.txt").write_text("[00:00 - 00:05] oi tudo bem", encoding="utf-8")
    (processing_dir / "corte01.words.json").write_text(
        json.dumps([{"word": "oi", "start": 0.0, "end": 0.3}]), encoding="utf-8"
    )
    knowledge_dir = tmp_path / "knowledge"
    patterns_dir = knowledge_dir / "niches" / "example-niche"
    patterns_dir.mkdir(parents=True)
    (patterns_dir / "PATTERNS.md").write_text("# padroes de teste", encoding="utf-8")

    transcript, words, patterns_md = load_selector_inputs("corte01", "example-niche", processing_dir, knowledge_dir)
    assert transcript == "[00:00 - 00:05] oi tudo bem"
    assert words == [{"word": "oi", "start": 0.0, "end": 0.3}]
    assert patterns_md == "# padroes de teste"


def test_load_selector_inputs_tolerates_missing_patterns_md(tmp_path):
    processing_dir = tmp_path / "processing"
    processing_dir.mkdir()
    (processing_dir / "corte01.txt").write_text("x", encoding="utf-8")
    (processing_dir / "corte01.words.json").write_text("[]", encoding="utf-8")

    _, _, patterns_md = load_selector_inputs("corte01", "example-niche", processing_dir, tmp_path / "knowledge")
    assert patterns_md is None


def test_parse_writer_output():
    parsed = parse_writer_output(WRITER_RAW)
    assert parsed["title"] == "Um titulo bem forte aqui"
    assert "Linha 1" in parsed["description"] and "Linha 2" in parsed["description"]
    assert "Outro titulo" not in parsed["description"]
    assert parsed["hashtags"] == "#nicho #shorts #viral"
    assert parsed["tags"] == ["nicho", "shorts", "viral"]
