# Contribuindo com o cutgen

Obrigado pelo interesse. Antes de abrir um PR, leia isto.

## Setup

```bash
git clone https://github.com/IsaacRop/cutgen.git
cd cutgen
uv sync --all-packages --all-extras --dev
```

Requer [uv](https://docs.astral.sh/uv/) e Python 3.11+. `ffmpeg` e `yt-dlp`
precisam estar no PATH pra rodar o pipeline de ponta a ponta (os testes não
dependem deles — veja abaixo).

## Rodando testes e lint antes de commitar

```bash
uv run pytest packages/shared/tests packages/knowledge/tests packages/core/tests packages/agent/tests
uv run ruff check packages/
```

O CI roda exatamente esses dois comandos. Um PR com testes falhando ou lint
sujo não passa.

## Estrutura do repo

Veja o [README](README.md#como-está-organizado) pra a divisão entre os
quatro pacotes (`shared`, `knowledge`, `core`, `agent`) e os dados de
runtime (`niches/`, `knowledge/niches/`).

## O que NUNCA vai num commit

Este projeto é a generalização open source de um pipeline de produção real.
Antes de abrir um PR, confira:

- **Nenhum dado real de canal**: números de performance, padrões
  descobertos, exemplos ingeridos ou hashtags específicas de um canal de
  verdade. `niches/example-niche/` é fictício de propósito — não substitua
  os valores por dados reais, nem seus nem de terceiros.
- **Nenhuma credencial**: chave de API, token OAuth, `client_secret.json`.
  O `.gitignore` já cobre os padrões óbvios (`credentials/`, `*token.json`,
  `*client_secret*.json`, `.env*`) — mas revise `git status` antes de
  commitar, o gitignore não é uma garantia.
- Veja [SECURITY.md](SECURITY.md) pra mais detalhes e pra como reportar se
  algo escapou.

## Estilo de commit

Conventional Commits (`feat(core): ...`, `fix(agent): ...`, `docs: ...`,
`chore: ...`). Prefira commits pequenos e coerentes — um módulo ou uma
correção por commit, não um PR gigante misturando tudo.

## Escopo de PRs

Prefira PRs pequenos e focados. Se sua mudança adiciona um layout de render
novo, uma integração de plataforma nova, ou um formato de conteúdo novo,
considere abrir uma issue primeiro pra alinhar o design — esses são
exatamente os pontos de extensão que o projeto foi desenhado pra receber
(ver "O que não está aqui (ainda)" no README), mas o design de cada um
merece discussão antes do código.

## Código de conduta

Este projeto segue o [Contributor Covenant](CODE_OF_CONDUCT.md).
