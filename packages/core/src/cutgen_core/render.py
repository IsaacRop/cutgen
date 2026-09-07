"""
Renderiza o corte final: gera a legenda .ass estilo karaoke a partir do
words.json (recorte + palavra atual em destaque, censura automatica de
palavrao) e monta/roda o comando ffmpeg que queima a legenda sobre o video,
com trilha opcional.

Generalizado a partir do render.py do GTclips: fonte, cores, palavras
censuradas e os alvos de loudness vem da secao `render` de
niches/<niche>/config.yaml, nao sao constantes fixas no codigo.

Escopo: este modulo cobre o mecanismo central (legenda karaoke + composicao
basica com trilha). Os layouts avancados do GTclips real (foco/post/reacao,
split-screen com gameplay, transicoes push/punch/shake/tilt/flash, tarja de
titulo animada) sao templates visuais especificos de marca/formato — ficam
fora deste MVP. Adicione-os como opcoes de layout por nicho quando fizer
sentido pro seu caso; nao foram recriados aqui por serem trabalho de design
proporcional a um produto inteiro, nao a uma generalizacao mecanica.
"""

import random
import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{base_style}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

DEFAULT_RENDER_CONFIG = {
    "font": "Arial",
    "font_size": 90,
    "primary_color": "&H00FFFFFF",   # branco opaco (AABBGGRR) — cor base do texto
    "secondary_color": "&H000000FF",
    "outline_color": "&H00000000",   # preto opaco — contorno
    "back_color": "&H96000000",      # preto semi-transparente — sombra
    "highlight_tag": "&H00FFFF&",    # amarelo (BBGGRR) — palavra atual em destaque
    "reset_tag": "&HFFFFFF&",        # branco (BBGGRR) — volta ao normal
    "max_words": 3,                  # palavras visiveis por vez
    "max_chars": 13,                 # cabe numa linha so
    "gap_seconds": 0.6,              # silencio que comeca um bloco novo
    "swears": [],                    # palavras mascaradas na legenda (audio intacto)
    "mask_from": "AI",
    "mask_to": "@1",
    "voice_lufs": -14.0,
    "music_lufs": -26.0,
}


@dataclass
class RenderConfig:
    font: str = DEFAULT_RENDER_CONFIG["font"]
    font_size: int = DEFAULT_RENDER_CONFIG["font_size"]
    primary_color: str = DEFAULT_RENDER_CONFIG["primary_color"]
    secondary_color: str = DEFAULT_RENDER_CONFIG["secondary_color"]
    outline_color: str = DEFAULT_RENDER_CONFIG["outline_color"]
    back_color: str = DEFAULT_RENDER_CONFIG["back_color"]
    highlight_tag: str = DEFAULT_RENDER_CONFIG["highlight_tag"]
    reset_tag: str = DEFAULT_RENDER_CONFIG["reset_tag"]
    max_words: int = DEFAULT_RENDER_CONFIG["max_words"]
    max_chars: int = DEFAULT_RENDER_CONFIG["max_chars"]
    gap_seconds: float = DEFAULT_RENDER_CONFIG["gap_seconds"]
    swears: frozenset = field(default_factory=frozenset)
    mask_table: dict = field(default_factory=dict)
    voice_lufs: float = DEFAULT_RENDER_CONFIG["voice_lufs"]
    music_lufs: float = DEFAULT_RENDER_CONFIG["music_lufs"]

    @classmethod
    def from_niche_config(cls, niche_config: dict) -> "RenderConfig":
        section = {**DEFAULT_RENDER_CONFIG, **((niche_config or {}).get("render") or {})}
        return cls(
            font=section["font"],
            font_size=section["font_size"],
            primary_color=section["primary_color"],
            secondary_color=section["secondary_color"],
            outline_color=section["outline_color"],
            back_color=section["back_color"],
            highlight_tag=section["highlight_tag"],
            reset_tag=section["reset_tag"],
            max_words=section["max_words"],
            max_chars=section["max_chars"],
            gap_seconds=section["gap_seconds"],
            swears=frozenset(w.upper() for w in section["swears"]),
            mask_table=str.maketrans(section["mask_from"], section["mask_to"]),
            voice_lufs=section["voice_lufs"],
            music_lufs=section["music_lufs"],
        )


def ass_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def censor(word: str, config: RenderConfig) -> str:
    """Mascara palavroes na legenda conforme swears/mask do nicho; o audio segue intacto."""
    core = re.sub(r"\W", "", word, flags=re.UNICODE)
    key = unicodedata.normalize("NFKD", core).encode("ascii", "ignore").decode().upper()
    return word.translate(config.mask_table) if key in config.swears else word


def build_caption_events(words: list[dict], start: float, end: float, dur: float,
                          config: RenderConfig) -> list[tuple[float, float, str]]:
    """
    Recorta words (words.json) pra janela [start,end], reancora no tempo 0 do
    corte, agrupa em blocos curtos (max_words/max_chars/gap_seconds) e gera um
    evento por palavra com ela em destaque (karaoke), as demais no tom base.
    """
    hl = "{\\c" + config.highlight_tag + "}"
    rs = "{\\c" + config.reset_tag + "}"

    win = []
    for w in words:
        if w["end"] > start and w["start"] < end:
            ws = max(0.0, w["start"] - start)
            we = min(dur, w["end"] - start)
            tok = censor(w["word"].strip().upper(), config)
            if tok:
                win.append((ws, we, tok))

    chunks: list[list[tuple[float, float, str]]] = []
    cur: list[tuple[float, float, str]] = []
    for ws, we, tok in win:
        joined = " ".join(t for _, _, t in cur + [(ws, we, tok)])
        if cur and (len(cur) >= config.max_words or ws - cur[-1][1] > config.gap_seconds
                    or len(joined) > config.max_chars):
            chunks.append(cur)
            cur = []
        cur.append((ws, we, tok))
    if cur:
        chunks.append(cur)

    events: list[tuple[float, float, str]] = []
    for ch in chunks:
        for i in range(len(ch)):
            ev_start = ch[i][0]
            ev_end = ch[i + 1][0] if i + 1 < len(ch) else ch[i][1]
            if ev_end <= ev_start:
                ev_end = ev_start + 0.05
            parts = [(hl + t + rs if j == i else t) for j, (_, _, t) in enumerate(ch)]
            events.append((ev_start, ev_end, " ".join(parts)))
    return events


def build_style_line(config: RenderConfig) -> str:
    """Monta a linha 'Style:' do .ass a partir da config do nicho (fonte/cores)."""
    return (f"Style: Base,{config.font},{config.font_size},{config.primary_color},"
            f"{config.secondary_color},{config.outline_color},{config.back_color},"
            "-1,0,0,0,100,100,0,0,1,7,3,5,15,15,60,1")


def write_ass(events: list[tuple[float, float, str]], path: Path, config: RenderConfig) -> Path:
    lines = [ASS_HEADER.format(base_style=build_style_line(config))]
    for st, en, text in events:
        lines.append(f"Dialogue: 0,{ass_time(st)},{ass_time(en)},Base,,0,0,0,,{text}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def pick_asset(folder: Path, *, random_pick: bool = False) -> Path | None:
    """Primeiro arquivo (ou aleatorio) de uma pasta de assets (musica/sfx/fundo).
    None se a pasta nao existir ou estiver vazia — assets sao opcionais."""
    if not folder.exists():
        return None
    files = sorted(p for p in folder.iterdir() if p.is_file())
    if not files:
        return None
    return random.choice(files) if random_pick else files[0]


def build_ffmpeg_command(*, video_path: Path, ass_path: Path, output_path: Path,
                          start: float, end: float, music_path: Path | None = None,
                          config: RenderConfig | None = None) -> list[str]:
    """
    Comando ffmpeg pra um corte 9:16: recorta [start,end], centra/escala pra
    1080x1920, queima a legenda .ass, normaliza a voz e mistura com a
    trilha (se houver). Layout simples — sem split-screen nem transicoes,
    ver o docstring do modulo pra escopo.
    """
    config = config or RenderConfig()
    duration = end - start
    video_filter = (
        "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',"
        "scale=1080:1920,"
        f"ass={ass_path.as_posix()}"
    )
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", str(video_path)]
    if music_path:
        cmd += ["-i", str(music_path)]
    cmd += ["-vf", video_filter]
    if music_path:
        cmd += [
            "-filter_complex",
            (
                f"[0:a]loudnorm=I={config.voice_lufs}[voice];"
                f"[1:a]loudnorm=I={config.music_lufs}[music];"
                "[voice][music]amix=inputs=2:duration=first[aout]"
            ),
            "-map", "0:v", "-map", "[aout]",
        ]
    else:
        cmd += ["-af", f"loudnorm=I={config.voice_lufs}"]
    cmd += ["-t", str(duration), str(output_path)]
    return cmd


def render(*, video_path: Path, words: list[dict], start: float, end: float, name: str,
           niche_config: dict, output_dir: Path = Path("output"),
           assets_dir: Path = Path("assets")) -> Path:
    """Gera a legenda + roda o ffmpeg de verdade. Retorna output/<name>.mp4."""
    config = RenderConfig.from_niche_config(niche_config)
    output_dir.mkdir(parents=True, exist_ok=True)
    dur = end - start
    events = build_caption_events(words, start, end, dur, config)
    ass_path = output_dir / f"{name}.ass"
    write_ass(events, ass_path, config)

    music_path = pick_asset(assets_dir / "music", random_pick=True)
    output_path = output_dir / f"{name}.mp4"
    cmd = build_ffmpeg_command(
        video_path=video_path, ass_path=ass_path, output_path=output_path,
        start=start, end=end, music_path=music_path, config=config,
    )
    subprocess.run(cmd, check=True)
    return output_path


def main():
    import argparse
    import json

    from cutgen_core.config import load_niche_config

    parser = argparse.ArgumentParser(description="Renderiza um corte vertical com legenda karaoke.")
    parser.add_argument("--video", required=True)
    parser.add_argument("--words", required=True, help="processing/<stem>.words.json")
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--niche", required=True)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--assets-dir", default="assets")
    args = parser.parse_args()

    words = json.loads(Path(args.words).read_text(encoding="utf-8"))
    out = render(
        video_path=Path(args.video), words=words, start=args.start, end=args.end,
        name=args.name, niche_config=load_niche_config(args.niche),
        output_dir=Path(args.output_dir), assets_dir=Path(args.assets_dir),
    )
    print(f"OK -> {out}")


if __name__ == "__main__":
    main()
