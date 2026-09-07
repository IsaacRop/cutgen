"""
Baixa video-fonte (pra make-cut) ou referencia viral (pra ingest-ref) via
yt-dlp. Generalizado a partir do download.py/ingest_ref.py do GTclips: os
flags de formato/cookies/idioma preferido vem da secao `download` de
niches/<niche>/config.yaml, nao sao fixos no codigo.

A transcricao em si NAO mora aqui (ver cutgen_core.transcribe) — este modulo
so baixa e, no caso de uma referencia, escreve o esqueleto do arquivo em
knowledge/niches/<niche>/examples/ a partir de metadados + uma transcricao
ja pronta.
"""

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_DOWNLOAD_CONFIG = {
    "format": "bv*+ba/b",
    "merge_output_format": "mp4",
    "sort": "vcodec:h264,acodec:aac,res:1080",
    "cookies_from_browser": None,
    "js_runtimes": None,
}

REFERENCE_TEMPLATE = """---
link: {link}
platform: {platform}
author: {author}
date_added: {date_added}
idioma: {language}
views: {views}
likes: {likes}
comentarios: {comments}
duracao_s: {duration}
status: viral
---

## Transcrição
{transcript}

## Estrutura
- hook (0-3s):
- corpo:
- cta:
- ritmo/legendas:

## Por que viralizou
(análise — preencher)

## Padrões identificados
-
"""


def platform_of(url: str) -> str:
    if "instagram.com" in url:
        return "instagram"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "other"


def slugify(text: str, max_words: int = 6) -> str:
    text = re.sub(r"[^\w\s-]", "", (text or "").lower())
    words = text.split()[:max_words]
    return "-".join(words) or "ref"


def build_download_command(url: str, output_template: str, download_config: dict | None = None,
                            *, write_info_json: bool = False) -> list[str]:
    """Monta o argv do yt-dlp a partir da secao `download` de niches/<niche>/config.yaml."""
    cfg = {**DEFAULT_DOWNLOAD_CONFIG, **(download_config or {})}
    cmd = ["yt-dlp"]
    if cfg.get("cookies_from_browser"):
        cmd += ["--cookies-from-browser", cfg["cookies_from_browser"]]
    if cfg.get("js_runtimes"):
        cmd += ["--js-runtimes", cfg["js_runtimes"]]
    cmd += ["-f", cfg["format"]]
    if cfg.get("sort"):
        cmd += ["-S", cfg["sort"]]
    cmd += ["--merge-output-format", cfg.get("merge_output_format", "mp4")]
    if write_info_json:
        cmd += ["--write-info-json"]
    cmd += ["--restrict-filenames", "-o", output_template, url]
    return cmd


def _latest_media_file(dest_dir: Path) -> Path:
    media = [p for p in dest_dir.glob("*") if p.suffix.lower() in (".mp4", ".mkv", ".webm")]
    if not media:
        raise FileNotFoundError(f"nenhum arquivo de video em {dest_dir}")
    return max(media, key=lambda p: p.stat().st_mtime)


def read_info_json(dest_dir: Path) -> dict:
    """Le o .info.json mais recente escrito pelo --write-info-json."""
    info_files = list(dest_dir.glob("*.info.json"))
    if not info_files:
        raise FileNotFoundError(f"nenhum .info.json em {dest_dir}")
    latest = max(info_files, key=lambda p: p.stat().st_mtime)
    return json.loads(latest.read_text(encoding="utf-8"))


def download(url: str, dest_dir: Path, download_config: dict | None = None, *,
             output_template: str | None = None, write_info_json: bool = False) -> Path:
    """Roda o yt-dlp de verdade e retorna o arquivo de video baixado."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    template = output_template or str(dest_dir / "%(id)s.%(ext)s")
    cmd = build_download_command(url, template, download_config, write_info_json=write_info_json)
    subprocess.run(cmd, check=True)
    return _latest_media_file(dest_dir)


def fetch_source(url: str, input_dir: Path, download_config: dict | None = None) -> Path:
    """Baixa um video-fonte pra input/ (usado pelo passo 1 do make-cut)."""
    return download(url, input_dir, download_config)


def write_reference_example(*, examples_dir: Path, info: dict, transcript: str, language: str,
                             video_id: str, url: str) -> Path:
    """
    Escreve knowledge/niches/<niche>/examples/<data>-<slug>-<id>.md a partir
    dos metadados do yt-dlp + de uma transcricao ja pronta (cutgen_core.transcribe).
    Sem parsing de volta — o analyst preenche Estrutura/Por que/Padroes por
    cima deste esqueleto.
    """
    def val(x):
        return "" if x is None else x

    examples_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC).date().isoformat()
    title = info.get("title") or (info.get("description") or "")[:80]
    slug = slugify(title)
    out = examples_dir / f"{date}-{slug}-{video_id}.md"
    out.write_text(
        REFERENCE_TEMPLATE.format(
            link=info.get("webpage_url", url),
            platform=platform_of(url),
            author=val(info.get("uploader") or info.get("channel")),
            date_added=date,
            language=language,
            views=val(info.get("view_count")),
            likes=val(info.get("like_count")),
            comments=val(info.get("comment_count")),
            duration=val(info.get("duration")),
            transcript=transcript,
        ),
        encoding="utf-8",
    )
    return out


def main():
    import argparse

    from cutgen_core.config import load_niche_config
    from cutgen_core.transcribe import TranscribeConfig, transcribe_plain

    parser = argparse.ArgumentParser(
        description="Baixa uma referencia viral, transcreve e escreve o esqueleto em "
                     "knowledge/niches/<niche>/examples/ (ou so baixa pra input/ com --no-analyze)."
    )
    parser.add_argument("url")
    parser.add_argument("--niche", required=True)
    parser.add_argument("--no-analyze", action="store_true",
                         help="So baixa pra input/ (passo 1 do make-cut); nao transcreve nem escreve exemplo")
    parser.add_argument("--input-dir", default="input")
    parser.add_argument("--refs-dir", default="refs")
    parser.add_argument("--examples-dir")
    args = parser.parse_args()

    niche_config = load_niche_config(args.niche)
    download_config = (niche_config or {}).get("download", {})

    if args.no_analyze:
        path = fetch_source(args.url, Path(args.input_dir), download_config)
        print(f"OK -> {path}")
        return

    refs_dir = Path(args.refs_dir)
    download(args.url, refs_dir, download_config, write_info_json=True)
    info = read_info_json(refs_dir)
    video_path = _latest_media_file(refs_dir)

    transcribe_config = TranscribeConfig.from_niche_config(niche_config)
    transcript, language = transcribe_plain(video_path, transcribe_config)

    examples_dir = (
        Path(args.examples_dir) if args.examples_dir
        else Path("knowledge") / "niches" / args.niche / "examples"
    )
    out = write_reference_example(
        examples_dir=examples_dir,
        info=info,
        transcript=transcript,
        language=language,
        video_id=info["id"],
        url=args.url,
    )
    print(f"OK -> {out}")
    print(f"  {platform_of(args.url)} | @{info.get('uploader')} | views={info.get('view_count')} "
          f"| likes={info.get('like_count')} | {info.get('duration')}s")


if __name__ == "__main__":
    main()
