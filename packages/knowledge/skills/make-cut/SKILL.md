---
name: make-cut
description: Produz um corte vertical 9:16 a partir de um vídeo-fonte (link do YouTube ou arquivo em input/), com a seleção do trecho guiada pelos padrões virais aprendidos. Use quando o usuário quiser gerar um Short/corte de um vídeo.
---

# Skill: make-cut

Uso: `/make-cut <url-do-youtube | arquivo-em-input/> --niche <niche>`

## Fluxo
1. Se for URL: `python -m cutgen_core.ingest <url> --niche <niche> --no-analyze`. Se já for arquivo em `input/`, use direto.
2. `python -m cutgen_core.transcribe input/<arquivo>` → gera `processing/<stem>.txt` e `processing/<stem>.words.json`.
3. Acione o subagente `selector` (`cutgen_knowledge.agents.selector`) passando o `<stem>` e o `<niche>` → ele retorna o(s) trecho(s) recomendado(s) com `start`/`end` + padrões citados, guiado por `knowledge/niches/<niche>/PATTERNS.md`.
4. **APRESENTE o trecho ao usuário e ESPERE aprovação** (ou ajuste de start/end) antes de renderizar.
5. Após aprovação: `python -m cutgen_core.render --video input/<arquivo> --words processing/<stem>.words.json --start <S> --end <E> --name <nome> --niche <niche>`.
6. Acione o subagente `writer` (`cutgen_knowledge.agents.writer`) pra gerar `output/<nome>.txt` (título/descrição/hashtags), lendo `niches/<niche>/config.yaml` pra idioma/hashtags-base/marca.
7. Mostre o resultado: `output/<nome>.mp4` + `output/<nome>.txt`.

## Notas
- Fundo/música/sfx/estilo de legenda/logotipo/paleta de cores: tudo definido em `niches/<niche>/config.yaml`, lido pelo `cutgen_core.render` — não hardcoded no core.
- NÃO pule a etapa de aprovação do trecho (passo 4).
- O layout de renderização (split-screen, foco, estático, etc.) e as transições disponíveis são opções de `cutgen_core.render`; os valores padrão de cada uma vêm do `config.yaml` do nicho, não de constantes fixas no código.
