# Conhecimento externo por MCP

## Objetivo

Descrever `app/integrations/mcp/` e `app/tools/external_knowledge.py` na `main` de IA `f6f3d8c` (02/11/2026). O mecanismo recupera práticas gerais de uso consciente da água para o `RagAgent`, com origem rastreável.

## Catálogo fechado

| ID | Artigo configurado | Perfil |
| --- | --- | --- |
| `midr-water-conservation` | Uso consciente da água, MIDR | Residencial e organizacional. |
| `epa-residential-saving` | Start Saving, US EPA | Residencial. |
| `epa-commercial-facilities` | Types of Facilities, US EPA | Organizacional. |

URLs e metadados estão em `app/integrations/mcp/sources.py`. Essa tabela descreve o catálogo do código; não atesta disponibilidade das páginas nesta revisão. Sem perfil informado, a ferramenta expõe somente a fonte geral. O LLM não escolhe outro perfil nem fornece URL livre.

O prompt proíbe recomendar WaterSense, seus produtos, selos, programas e campanhas. Práticas gerais podem ser explicadas, preservando a URL original da EPA na citação. As páginas não são fonte para tarifas vigentes ou regras particulares do produto Delta.

## Transporte e contrato

O cliente inicia servidor MCP local via **stdio**, executado como módulo Python. Não abre serviço HTTP público. A solicitação ao subprocesso contém o identificador da fonte; não inclui pergunta, histórico ou dados da conta nesse payload.

A leitura pública usa TLS, timeout, limite de resposta e recusa redirecionamento. O parser extrai o artigo e ignora menus/scripts. `ExternalDocument` valida fonte, URL, metadados, revisão SHA-256 e coleta com timezone. Linhas citadas são do texto extraído normalizado, não do HTML original.

O cliente configura `env={"PYTHONUTF8": "1"}` e conta com as variáveis básicas herdadas pelo SDK, sem repassar as credenciais do backend. Isso é diferente do processamento completo: pergunta e trechos continuam passando pelos serviços de embedding e geração necessários ao RAG.

## Configuração e recuperação

`MCP_EXTERNAL_ENABLED=true` habilita a busca; default é `false`. `MCP_TIMEOUT_SECONDS=45` limita o caminho MCP e `MCP_CACHE_TTL_SECONDS=3600` controla cache dos textos. O cache é por processo e catálogo, sem servir conteúdo vencido quando a fonte falha.

`search_external_knowledge` aceita pergunta, top-k de 1 a 20 e filtros exatos opcionais `topic`/`source_id`. Seleciona fontes permitidas pelo perfil confiável, recupera snapshots, indexa revisões em `rag_documents` e busca trechos. Gera um embedding da pergunta e o reutiliza entre fontes dessa chamada.

O conteúdo externo usa fonte `mcp:<source_id>` e metadados próprios, separado da fonte interna por filtros de origem/revisão/modelo. Retorna citação Markdown com título/URL, data de coleta, revisão e localização. Uma fonte pode falhar enquanto outras retornam trechos; `unavailable_sources` identifica falhas. Sem resultados e com falha, retorna `unavailable`; filtro sem fontes ou busca sem resultado retorna `insufficient_data`.

## Diagnóstico e limites

Na raiz do repositório de IA, com dependências instaladas:

```powershell
python -m scripts.check_mcp --all
```

Esse comando testa protocolo e acesso público, sem embeddings/Qdrant/LLM. Não valida a resposta completa do agente. Os CLIs em `scripts/` não são copiados para a imagem atual; o servidor em `app/` é copiado.

Testes: `test_mcp_sources.py`, `test_external_rag.py`, `test_playground_rag_profile.py` e integração RAG no grafo. A revisão documental não fez leitura das páginas ou chamada remota.

Não há implementação A2A nessa `main`. O fluxo de clima consulta `weather_daily` no MongoDB, e não esse MCP nem uma API meteorológica ao vivo.

## Fontes da implementação revisada

- [app/integrations/mcp/client.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/integrations/mcp/client.py)
- [app/integrations/mcp/sources.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/integrations/mcp/sources.py)
- [app/tools/external_knowledge.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/tools/external_knowledge.py)
