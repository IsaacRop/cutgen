---
name: ingest-ref
description: Ingesta uma referência viral (Short/Reel do YouTube ou Instagram) e a analisa, enriquecendo a base de padrões. Use quando o usuário mandar um link de vídeo viral do nicho ("adiciona essa referência", "/ingest-ref <url>").
---

# Skill: ingest-ref

Uso: `/ingest-ref <url> --niche <niche>` (YouTube ou Instagram)

## Fluxo
1. Rode `python -m cutgen_core.ingest <url> --niche <niche>` — baixa, transcreve e puxa métricas (views/likes/autor/duração), criando `knowledge/niches/<niche>/examples/<data>-<slug>.md` com os blocos de análise vazios.
2. Abra o arquivo gerado e acione o subagente `analyst` (`cutgen_knowledge.agents.analyst`) pra preencher Estrutura, "Por que (não) viralizou" e Padrões identificados.
3. Mostre ao usuário um resumo: métricas + gancho + padrões marcados.
4. Lembre que os padrões só entram na camada 2 quando rodar `/consolidate <niche>` (curator).

## Notas
- NÃO roda o curator aqui. Ingestão só empilha exemplos em `knowledge/niches/<niche>/examples/`.
- Aceita vários links numa tacada — repita o fluxo por link.
- A receita de autenticação/download (cookies, PO token, etc.) fica embutida em `cutgen_core.ingest`, configurável por `niches/<niche>/config.yaml`.
