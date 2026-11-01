# Segmentação e recuperação da base Delta

## Objetivo e escopo

O Agente RAG recupera documentação local do produto e conhecimento externo sobre
uso consciente da água, preservando os trechos e suas fontes até a avaliação do
Juiz. A integração externa está na branch `feat/mcp-fontes-externas-rag` do
repositório `delta-artificial-intelligence`, sujeita à revisão antes de merge.

A fonte local implementada é `app/knowledge/delta-main-source.md`, configurável
por `RAG_DOCUMENT_PATH` e incluída na imagem da aplicação. Caminhos relativos
partem da raiz do repositório de IA. O agente não recebe caminhos livres do LLM.
O antigo fluxo de CLI manual `scripts.rag` não está presente neste checkout:
a ferramenta prepara automaticamente a revisão antes da consulta.

Para fontes externas, consulte o [guia MCP/RAG](mcp-fontes-externas-rag.md), que
registra o catálogo, os contratos, os filtros e a validação da chamada pública.
O documento do produto e os artigos externos conservam identidades distintas.

## Segmentação e modelo vetorial

A base local é segmentada por títulos `#`, `##` e `###`, preservando hierarquia,
texto e linhas. Títulos sem corpo não viram vetores vazios; seções acima de
6.000 caracteres devem ser subdivididas. Esta versão do parser não implementa
tratamento especial de blocos de código cercados: não trate títulos dentro
nesses blocos como comportamento validado.

O texto externo é extraído do artigo HTML e dividido em trechos de até 1.800
caracteres. Títulos Markdown no conteúdo externo não são interpretados como
estrutura. As linhas da citação se referem ao texto extraído normalizado,
não ao HTML publicado. O texto enviado ao embedding inclui título e conteúdo.

O serviço compartilha `GEMINI_EMBEDDING_MODEL` entre documentos e perguntas:
`RETRIEVAL_DOCUMENT` para indexação, `RETRIEVAL_QUERY` para consulta e vetores
de 3072 dimensões. O padrão dos settings é `gemini-embedding-001`. O modelo,
a dimensão e os documentos indexados precisam permanecer compatíveis.

A coleção fixa `rag_documents` é separada da memória `session_summaries`.
Ela deve existir com vetor sem nome, 3072 dimensões e distância Cosine. O
serviço recusa esquema incompatível antes de gerar embeddings e nunca apaga
ou recria essa coleção.

A representação do vetor padrão como mapa `{"": VectorParams(...)}` também é
compatível; ela não deve ser confundida com um vetor de nome não vazio.

## Recuperação, revisão e referência

`search_knowledge_base(question, top_k=3)` consulta as regras do Delta.
`search_external_knowledge(question, top_k=3, topic=None, source_id=None)`
consulta as três fontes propostas (MIDR e EPA), quando o MCP está habilitado.
A ferramenta construída pelo agente recebe o perfil confiável do backend e
seleciona a fonte geral e a EPA residencial ou comercial, sem argumento livre
de perfil para o modelo. O prompt proíbe recomendações WaterSense e mantém a
URL original da EPA na referência. Top-k
aceita valores de 1 a 20; tema e fonte são filtros exatos na busca externa.

A preparação usa IDs estáveis por fonte, revisão, modelo e posição. Um lock
impede indexações simultâneas no mesmo processo. Quando uma revisão está
completa, não gera novamente os embeddings dos documentos; se está incompleta,
a próxima chamada tenta completá-la. Revisões antigas continuam armazenadas,
mas a consulta filtra somente a atual. Não há limpeza automática de revisões.

Os resultados incluem texto, hierarquia, linhas, fonte, revisão, modelo e
score. Trechos externos também incluem URL, título, tema, publicação, coleta
e natureza externa. Similaridade não é probabilidade nem garantia de que o
trecho responda à pergunta. O serviço Python oferece `score_threshold`
opcional; nenhum limiar sem calibração foi imposto às ferramentas.

O `RagAgent` recebe os resultados como mensagens de ferramenta, registra os
trechos em `tool_calls` e as referências em `sources`. A lista final de
fontes é montada em Python com os campos `citation` recuperados. O grafo leva
esse contexto real ao Juiz antes da publicação. A avaliação semântica e a
fidelidade de uma resposta gerada precisam de validação com os modelos reais.

## Configuração e falhas

Configure `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL`, `QDRANT_URL` e, se exigido,
`QDRANT_API_KEY`. A fonte local exige `RAG_DOCUMENT_PATH`; a externa exige
`MCP_EXTERNAL_ENABLED=true`. Não há fallback para outro Qdrant implícito na
base documental. Indexar gera chamadas ao provedor de embeddings e grava na
coleção configurada.

`unavailable` indica falha de configuração, preparação ou acesso;
`insufficient_data` indica que a busca ou o filtro não produziu trechos.
Nenhum desses estados permite completar a resposta com regras inventadas.
O conteúdo externo não comprova consumo, tarifa, clima, alertas ou outros
dados da conta, nem define funcionalidades do produto.

## Testes e limites

Na raiz do repositório de IA:

```powershell
$env:APP_ENV = 'test'
python -m pytest tests/test_ci_rag.py tests/test_external_rag.py tests/test_rag_workflow_integration.py -q
```

Os testes verificam rastreabilidade, top-k, filtros, ranking temático controlado,
idempotência, reparo de revisão incompleta, isolamento de fontes e revisões,
esquema incompatível e evidências no grafo. Usam Qdrant em memória e embeddings
artificiais; não comprovam a qualidade semântica do Gemini ou acesso ao Qdrant
remoto. Os provedores generativos, a avaliação e os bancos cadastrais do grafo
são substituídos nos cenários de integração.

As chamadas reais às três fontes propostas por MCP foram executadas e está registrada no
[guia de fontes externas](mcp-fontes-externas-rag.md). Ela não equivale à
validação completa de memória persistente, bancos, embeddings e Juiz.
A2A está fora do escopo por decisão de negócio em 01/11/2026.

Referências técnicas: [embeddings Gemini](https://ai.google.dev/gemini-api/docs/embeddings)
e [Qdrant](https://qdrant.tech/documentation/).
