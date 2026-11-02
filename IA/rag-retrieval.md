# Segmentação e recuperação da base Delta

## Objetivo e escopo

O serviço de recuperação prepara a base Markdown e busca os trechos mais próximos da pergunta. A recuperação não gera a resposta final por si só: o `RagAgent` usa seus resultados, está registrado no roteador e fornece evidências ao Juiz. A memória de conversas usa coleção separada.

A fonte padrão é `app/knowledge/delta-main-source.md`, configurada por `RAG_DOCUMENT_PATH` e incluída na imagem Docker. Caminhos relativos partem da raiz do serviço; não há dependência automática da estrutura de outros repositórios.

## Como funciona

1. `#` identifica o documento, `##` identifica capítulos e `###` identifica
   subtópicos. Cada corpo de seção vira um trecho, acompanhado da hierarquia
   completa de títulos. Texto antes dos capítulos, incluindo versão e ressalvas,
   também é preservado. Títulos sem corpo não geram vetores vazios.
2. O texto enviado ao embedding contém títulos e conteúdo. Assim, por exemplo,
   um subtópico de chuva mantém sua ligação ao capítulo de clima. Uma pergunta
   busca todos os trechos e devolve os mais próximos, com seus respectivos
   capítulos; não há classificação prévia que restrinja a busca a um só capítulo.
3. `GEMINI_EMBEDDING_MODEL` (padrão `gemini-embedding-2-preview`) produz vetores de 3072 dimensões. Documentos usam
   `RETRIEVAL_DOCUMENT`; a pergunta usa `RETRIEVAL_QUERY`. É um modelo textual,
   adequado a esta etapa com Markdown. A integração usa a dependência existente
   `langchain-google-genai`, com timeout HTTP de 30 segundos.
4. Qdrant armazena os vetores com distância Cosine na coleção fixa
   `rag_documents`, separada de `session_summaries`. Os metadados incluem fonte,
   hash da revisão, modelo, hierarquia, texto e linhas inicial/final (inclusivas).
5. A busca devolve até três trechos por padrão, com IDs, scores e metadados.
   Similaridade não é probabilidade nem garantia de relevância. O limiar opcional
   precisa ser calibrado com perguntas reais; nenhum limiar arbitrário é imposto.

A separação reconhece títulos no início das linhas sem tratamento especial para títulos dentro de blocos de código. Não separa pelo caractere `#`
encontrado no meio de frases. Para evitar truncamento silencioso pelo provedor,
seções acima de 6000 caracteres (corpo e títulos) são rejeitadas: subdivida-as
com `###` na fonte. Esse limite conservador em caracteres não é um tokenizador.
Títulos `####` e posteriores permanecem no corpo.

## Uso e configuração

A ferramenta `search_knowledge_base(question, top_k=3)` prepara automaticamente a revisão configurada antes da busca; `top_k` aceita 1 a 20. Não há CLI `scripts.rag` de inspeção/indexação/consulta no serviço.

Configure `GEMINI_API_KEY`, `QDRANT_URL`, `RAG_DOCUMENT_PATH` e, se exigida pelo servidor, `QDRANT_API_KEY`, conforme os [settings](settings.md). O destino Qdrant do RAG é explícito e aplica timeout de 30 segundos. A coleção `rag_documents` precisa existir previamente, com vetor sem nome, 3072 dimensões e distância Cosine. As permissões devem permitir criar índices de payload e gravar/ler pontos; o serviço não cria ou recria a coleção.

Na API Python, `load_document`, `index_document`, `ensure_document_indexed` e `search_document` estão em `app/services/rag.py`; os clientes são injetáveis para testes. `search_document` aceita `score_threshold` opcional. Embeddings de documentos e perguntas usam chamadas ao provedor, que podem ser cobradas. Clientes são reutilizados e encerrados por `close_rag_clients` no ciclo da API.

## Revisões e falhas

Reindexar o mesmo conteúdo atualiza os mesmos IDs, sem duplicar pontos. O hash
inclui conteúdo e versão do segmentador. Após alterar o Markdown, a ferramenta chama `ensure_document_indexed` e prepara a nova revisão automaticamente antes de `search_document`. A busca filtra fonte, revisão e modelo;
revisões antigas continuam armazenadas, mas não participam da consulta atual.
O arquivo precisa estar acessível também na consulta para identificar a revisão.

Uma revisão ausente ou incompleta precisa ser preparada antes de `search_document`; a ferramenta faz essa preparação e confere a contagem esperada. Erros de provedor/banco propagam na API Python e são convertidos pela ferramenta para `status=unavailable`, sem se confundirem com busca sem resultados.
Erros de configuração indicam o nome da variável ausente, sem mostrar seu valor.
Lista vazia significa que a busca executada não encontrou pontos aceitos pelo
limiar. Coleções incompatíveis são recusadas, nunca apagadas ou recriadas.

Revisões antigas não são removidas automaticamente. Trocar modelo ou dimensões
exige uma migração explícita, não comparação entre espaços vetoriais diferentes.

## Validação e limites

Testes como `test_ci_rag.py`, `test_external_rag.py` e `test_rag_workflow_integration.py` verificam segmentação, rastreabilidade,
idempotência, isolamento de fontes/revisões, erros e consulta vetorial usando
Qdrant real em memória e embeddings controlados. Não acessa Gemini nem Qdrant
remoto e não comprova qualidade semântica ou disponibilidade dos serviços.

Na validação original da recuperação documental, a suíte completa passou com 214 testes. O
diretório temporário padrão do Windows sandbox negou escrita nos testes com
arquivos; a execução usou `--basetemp` em um diretório novo e isolado dentro do
workspace. Isso não exige mudar os testes ou a configuração da aplicação.

Naquela validação, a inspeção local da base de referência encontrou 12 capítulos e 58 trechos,
incluindo a apresentação. Credenciais Gemini e URL Qdrant estavam ausentes:
geração dos embeddings reais, persistência remota e avaliação temática com
perguntas reais ficaram pendentes naquela execução. O documento original não foi alterado.

Referências técnicas: [embeddings Gemini](https://ai.google.dev/gemini-api/docs/embeddings)
e [documentação Qdrant](https://qdrant.tech/documentation/).

## Preparação automática

1. `load_document` lê a fonte atual e divide Markdown por títulos `#`, `##`, `###`, preservando hierarquia e linhas. Uma seção acima de 6000 caracteres, contando corpo e hierarquia, é recusada; subdivida a fonte com `###`. Não há divisão automática de seção interna longa.
2. A revisão SHA-256 incorpora texto e versão do parser (`markdown-headings-v2`). O identificador estável da fonte interna é `delta-product-reference`.
3. `ensure_document_indexed` valida a coleção, garante índices de payload e compara a contagem da revisão/modelo com os trechos esperados.
4. Se faltar conteúdo, gera embeddings e faz upsert com IDs determinísticos por fonte, revisão, modelo e posição, conferindo completude ao final.
5. Só então gera o embedding da pergunta e consulta a revisão/modelo atuais.

O lock de indexação é **por processo**; não é trava distribuída entre workers. Revisões antigas continuam armazenadas e são excluídas da busca por filtros, sem limpeza automática.

## Busca e proveniência

`search_knowledge_base(question, top_k=3)` aceita top-k de 1 a 20. Retorna `status`, `chunks` e referências com fonte, revisão, modelo, títulos, linhas e score. Resultado vazio é `insufficient_data`; falha é `unavailable`. O modelo não deve completar regras do produto sem apoio quando a busca falha.

O score vetorial ordena resultados e não comprova verdade ou relevância suficiente. Os outputs reais e fontes acompanham a execução e chegam ao Juiz. Fontes externas têm `origin=external`, IDs próprios e URL; veja [MCP](mcp-conhecimento-externo.md).

## Código relacionado

- [app/services/rag.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/services/rag.py)
- [app/tools/rag.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/tools/rag.py)
- [app/agents/rag.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/agents/rag.py)
