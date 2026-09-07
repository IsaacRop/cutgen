"""
Publica um video no YouTube via OAuth (google-api-python-client), usando um
token de credenciais salvo localmente. Generalizado a partir de
youtube/upload.py e youtube/authorize.py do GTclips: categoria/idioma/
privacidade padrao vem da secao `publish` de niches/<niche>/config.yaml, e o
caminho do token de credenciais e configuravel — nunca versionado (ver
.gitignore: credentials/, *token.json, *client_secret*.json).

authorize() roda uma vez manualmente pra gerar o token; upload_video() e o
que o pipeline chama depois, renovando o token quando expira.
"""

from pathlib import Path

DEFAULT_PUBLISH_CONFIG = {
    "category_id": "22",  # "People & Blogs" — categoria generica default do YouTube
    "default_language": "en",
    "privacy": "public",
    "made_for_kids": False,
}

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def authorize(client_secret_file: Path, token_file: Path) -> None:
    """Fluxo OAuth interativo — roda uma vez manualmente, salva o refresh token."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
    credentials = flow.run_local_server(port=0)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json())


def get_credentials(token_file: Path):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_file(str(token_file))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json())
    return creds


def build_video_body(*, title: str, description: str, tags: list[str], niche_config: dict,
                      privacy: str | None = None) -> dict:
    """Monta o body do videos().insert() a partir da metadata do writer + config do nicho."""
    cfg = {**DEFAULT_PUBLISH_CONFIG, **((niche_config or {}).get("publish") or {})}
    language = cfg["default_language"]
    return {
        "snippet": {
            "title": title[:100],  # limite da API
            "description": description,
            "tags": tags,
            "categoryId": cfg["category_id"],
            "defaultLanguage": language,
            "defaultAudioLanguage": language,
        },
        "status": {
            "privacyStatus": privacy or cfg["privacy"],
            "selfDeclaredMadeForKids": cfg["made_for_kids"],
        },
    }


def upload_video(video_path: Path, *, title: str, description: str, tags: list[str],
                  niche_config: dict, token_file: Path, privacy: str | None = None,
                  progress=None) -> str:
    """Sobe o video e retorna o video_id."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=get_credentials(token_file))
    body = build_video_body(title=title, description=description, tags=tags,
                             niche_config=niche_config, privacy=privacy)
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and progress:
            progress(int(status.progress() * 100))
    return response["id"]


def main():
    import argparse

    from cutgen_core.config import load_niche_config

    parser = argparse.ArgumentParser(description="Publica um corte no YouTube.")
    parser.add_argument("video")
    parser.add_argument("title")
    parser.add_argument("description")
    parser.add_argument("tags", help="Tags separadas por virgula")
    parser.add_argument("--niche", required=True)
    parser.add_argument("--token-file", default="credentials/token.json")
    parser.add_argument("--privacy", choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    video_id = upload_video(
        Path(args.video), title=args.title, description=args.description,
        tags=[t.strip() for t in args.tags.split(",") if t.strip()],
        niche_config=load_niche_config(args.niche),
        token_file=Path(args.token_file), privacy=args.privacy,
        progress=lambda p: print(f"Upload {p}%"),
    )
    print(f"Video publicado: https://youtu.be/{video_id}")


if __name__ == "__main__":
    main()
