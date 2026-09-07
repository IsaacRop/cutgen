---
name: consolidate
description: Consolida as referências ingeridas em padrões virais destilados (camada 2). Use ao fim de uma rodada de ingestão, ou quando o usuário pedir pra "atualizar/consolidar os padrões".
---

# Skill: consolidate

Uso: `/consolidate <niche>`

## Fluxo
1. Acione o subagente `curator` (`cutgen_knowledge.agents.curator`).
2. Ele lê `knowledge/niches/<niche>/examples/` + `knowledge/niches/<niche>/patterns/`, reforça/cria padrões, trata contradições (exceção vs. pendente) e atualiza `knowledge/niches/<niche>/PATTERNS.md`.
3. Mostre ao usuário o resumo: o que reforçou, o que criou de novo, o que ficou pendente/ambíguo.

## Notas
- Rode DEPOIS de acumular novas referências via `/ingest-ref` — não faz sentido rodar sem exemplos novos.
- É o único ponto que mexe na camada 2 (padrões). A ingestão sozinha não altera padrões.
