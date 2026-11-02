# RAG: segmentação, indexação e recuperação

## Objetivo e fonte

Documentar o caminho implementado por `RagAgent`, `app/tools/rag.py` e `app/services/rag.py` na `main` `f6f3d8c` (02/11/2026). O agente é registrado no roteador e gera resposta usando trechos; o serviço de recuperação isolado apenas indexa/busca.

A fonte interna é `app/knowledge/delta-main-source.md`, default de `RAG_DOCUMENT_PATH`, incluída na imagem Docker. Caminhos relativos partem da raiz da IA. O handbook explica a implementação, mas seus arquivos não são ingeridos automaticamente como fonte do produto.

## Preparação automática

1. `load_document` lê a fonte atual e divide Markdown por títulos `#`, `##`, `###`, preservando hierarquia e linhas. Uma seção acima de 6000 caracteres, contando corpo e hierarquia, é recusada; subdivida a fonte com `###`. Não há divisão automática de seção interna longa.
2. A revisão SHA-256 incorpora texto e versão do parser (`markdown-headings-v2`). O identificador estável da fonte interna é `delta-product-reference`.
3. `ensure_document_indexed` valida a coleção, garante índices de payload e compara a contagem da revisão/modelo com os trechos esperados.
4. Se faltar conteúdo, gera embeddings e faz upsert com IDs determinísticos por fonte, revisão, modelo e posição, conferindo completude ao final.
5. Só então gera o embedding da pergunta e consulta a revisão/modelo atuais.

O lock de indexação é **por processo**; não é trava distribuída entre workers. Revisões antigas continuam armazenadas e são excluídas da busca por filtros, sem limpeza automática.

## Contrato Qdrant e embeddings

`rag_documents` precisa existir previamente com um vetor sem nome de **3072 dimensões e distância Cosine**. Esquema incompatível ou coleção ausente são recusados; o serviço não apaga nem recria a coleção.

O modelo vem de `GEMINI_EMBEDDING_MODEL`, default `gemini-embedding-2-preview`, normalizado com prefixo `models/` no payload. Documentos usam `RETRIEVAL_DOCUMENT`; perguntas, `RETRIEVAL_QUERY`. RAG exige `GEMINI_API_KEY`, modelo, `QDRANT_URL` explícita e fonte acessível. `QDRANT_API_KEY` depende da autenticação do destino.

Coleção, modelo, dimensão e conteúdo precisam ser compatíveis. Troca de modelo com a mesma dimensão ainda exige nova indexação; o filtro evita misturar modelos. Os resumos em `session_summaries` têm outro contrato e exigem tratamento próprio.

## Busca e proveniência

`search_knowledge_base(question, top_k=3)` aceita top-k de 1 a 20. Retorna `status`, `chunks` e referências com fonte, revisão, modelo, títulos, linhas e score. Resultado vazio é `insufficient_data`; falha é `unavailable`. O modelo não deve completar regras do produto sem apoio quando a busca falha.

O score vetorial ordena resultados e não comprova verdade ou relevância suficiente. Os outputs reais e fontes acompanham a execução e chegam ao Juiz. Fontes externas têm `origin=external`, IDs próprios e URL; veja [MCP](mcp-conhecimento-externo.md).

## Clientes e diagnóstico

Clientes RAG de embeddings/Qdrant são lazy, reutilizados por configuração e encerrados por `close_rag_clients` no `lifespan`. Reutilizar clientes não armazena resposta final nem elimina a verificação de revisão ou o embedding da pergunta.

A revisão atual não contém os CLIs antigos de indexação/consulta documental. A tool prepara a revisão automaticamente; não é necessário inventar uma etapa manual de CLI. A primeira busca pode custar mais por indexar conteúdo.

Testes versionados: `test_ci_rag.py`, `test_external_rag.py`, `test_rag_workflow_integration.py` e `test_mcp_sources.py`. Eles incluem substitutos e Qdrant em memória conforme o caso; não provam qualidade temática, disponibilidade Gemini ou persistência Qdrant remota. Nesta revisão não houve reindexação de ambiente real.

## Fontes da implementação revisada

- [app/services/rag.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/services/rag.py)
- [app/tools/rag.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/tools/rag.py)
- [app/agents/rag.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/agents/rag.py)
