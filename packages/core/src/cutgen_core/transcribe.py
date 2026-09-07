"""
Transcreve um arquivo de video/audio em blocos, com timestamps por palavra.
Generalizado a partir do transcribe.py do GTclips: tamanho do modelo, sample
rate e duracao do bloco vem da secao `transcribe` de niches/<niche>/config.yaml,
com os mesmos defaults do original (small / 16kHz / blocos de 3 min).

Roda em blocos (nao o audio inteiro de uma vez) por dois motivos: nao estourar
RAM em fontes longas e salvar progresso parcial cedo — uma falha tardia nao
apaga o que ja foi transcrito.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_SIZE = "small"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHUNK_SECONDS = 180


@dataclass
class TranscribeConfig:
    model_size: str = DEFAULT_MODEL_SIZE
    sample_rate: int = DEFAULT_SAMPLE_RATE
    chunk_seconds: int = DEFAULT_CHUNK_SECONDS

    @classmethod
    def from_niche_config(cls, niche_config: dict) -> "TranscribeConfig":
        section = (niche_config or {}).get("transcribe", {}) or {}
        return cls(
            model_size=section.get("model_size", DEFAULT_MODEL_SIZE),
            sample_rate=section.get("sample_rate", DEFAULT_SAMPLE_RATE),
            chunk_seconds=section.get("chunk_seconds", DEFAULT_CHUNK_SECONDS),
        )


def format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def format_line(start: float, end: float, text: str) -> str:
    return f"[{format_timestamp(start)} - {format_timestamp(end)}] {text.strip()}"


def transcribe(video_path: Path, processing_dir: Path, config: TranscribeConfig | None = None,
                *, on_progress=None) -> tuple[Path, Path]:
    """
    Transcreve video_path em blocos, salvando progresso parcial a cada bloco.
    Retorna (words_path, txt_path). Chamada real ao faster-whisper — precisa
    do modelo e de CPU disponiveis, nao e testavel sem um arquivo de audio real.
    """
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    config = config or TranscribeConfig()
    processing_dir.mkdir(parents=True, exist_ok=True)
    stem = video_path.stem
    words_path = processing_dir / f"{stem}.words.json"
    txt_path = processing_dir / f"{stem}.txt"

    model = WhisperModel(config.model_size, device="cpu", compute_type="int8")
    audio = decode_audio(str(video_path), sampling_rate=config.sample_rate)
    step = config.chunk_seconds * config.sample_rate

    words: list[dict] = []
    lines: list[str] = []

    def flush():
        words_path.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        txt_path.write_text("\n".join(lines), encoding="utf-8")

    for i in range(0, len(audio), step):
        offset = i / config.sample_rate
        segments, _info = model.transcribe(audio[i:i + step], word_timestamps=True, vad_filter=True)
        for seg in segments:
            lines.append(format_line(seg.start + offset, seg.end + offset, seg.text))
            for w in (seg.words or []):
                words.append({
                    "word": w.word,
                    "start": round(w.start + offset, 3),
                    "end": round(w.end + offset, 3),
                })
        flush()
        if on_progress:
            on_progress(block=i // step + 1, offset_minutes=offset / 60, word_count=len(words))

    return words_path, txt_path


def transcribe_plain(video_path: Path, config: TranscribeConfig | None = None) -> tuple[str, str]:
    """
    Transcricao de uma tacada so, sem chunking nem timestamps por palavra —
    usada pra referencias ingeridas (knowledge/niches/<niche>/examples/), que
    so precisam do texto corrido + idioma detectado, nao de cortes precisos.
    """
    from faster_whisper import WhisperModel

    config = config or TranscribeConfig()
    model = WhisperModel(config.model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(video_path), vad_filter=True)
    transcript = " ".join(s.text.strip() for s in segments).strip()
    return transcript, info.language


def main():
    import argparse

    from cutgen_core.config import load_niche_config

    parser = argparse.ArgumentParser(
        description="Transcreve um video/audio em blocos, com timestamps por palavra."
    )
    parser.add_argument("video", help="Caminho do arquivo de video/audio (ex.: input/corte.mp4)")
    parser.add_argument("--niche", help="Le niches/<niche>/config.yaml, secao 'transcribe'")
    parser.add_argument("--processing-dir", default="processing")
    args = parser.parse_args()

    config = (
        TranscribeConfig.from_niche_config(load_niche_config(args.niche))
        if args.niche
        else TranscribeConfig()
    )

    def report(block, offset_minutes, word_count):
        print(f"--- bloco {block} (~{offset_minutes:.0f} min) ok | {word_count} palavras ---")

    words_path, txt_path = transcribe(Path(args.video), Path(args.processing_dir), config, on_progress=report)
    print(f"\nOK: {txt_path.name} + {words_path.name} em {args.processing_dir}/")


if __name__ == "__main__":
    main()
