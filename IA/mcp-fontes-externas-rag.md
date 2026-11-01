# MCP de fontes externas para o RAG

## Objetivo e decisão de escopo

Disponibilizar conhecimento público sobre uso consciente, conservação e eficiência
hídrica ao Agente RAG. A entrega está na branch `feat/mcp-fontes-externas-rag` do
repositório `delta-artificial-intelligence`; esta documentação acompanha a branch
`docs/mcp-fontes-externas-rag`. A presença nas branches não significa merge ou deploy.

A [demanda de configuração MCP](https://app.clickup.com/t/86e32aqra) ainda menciona
clima. Por orientação da pessoa responsável, nesta entrega MCP alimenta o RAG com
conhecimento externo. O histórico meteorológico de `weather_daily` e a ferramenta
de hábitos permanecem no fluxo já existente.

O MCP padroniza a comunicação entre cliente e servidor. Aqui ele transporta o
artigo e seus metadados; a recuperação vetorial continua no serviço RAG existente.
Não há um novo agente gerativo para pesquisar ou resumir páginas.

## Componentes e fluxo

1. O roteador encaminha perguntas gerais sobre conservação ao `RagAgent`.
2. Para regras do Delta, o agente usa `search_knowledge_base`; para conhecimento
   público, usa `search_external_knowledge`. Pedidos mistos podem usar ambas.
3. O cliente inicia `python -m app.integrations.mcp.server` no mesmo ambiente
   Python, por stdio. O processo recebe somente `source_id`, nunca a pergunta,
   o histórico, o usuário autenticado ou as chaves do backend.
4. O servidor busca a URL HTTPS cadastrada, extrai apenas o artigo e devolve
   texto, proveniência e hash SHA-256. Não segue redirecionamentos e não recebe
   URLs livres, comandos, caminhos de arquivo ou instruções de navegação.
5. O serviço segmenta o texto, verifica o esquema e a completude da revisão no
   Qdrant e gera os embeddings faltantes. A busca retorna até `top_k` trechos.
6. O agente recebe o resultado estruturado, preserva as evidências e constrói a
   lista final de referências a partir das ferramentas. O grafo continua passando
   candidata e trechos ao Juiz antes da publicação e do guardrail de saída.

Código na [branch de implementação](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/feat/mcp-fontes-externas-rag):

| Arquivo | Responsabilidade |
| --- | --- |
| `app/integrations/mcp/sources.py` | Catálogo, extração HTML e contrato de proveniência |
| `app/integrations/mcp/server.py` | Servidor MCP com ferramentas de leitura |
| `app/integrations/mcp/client.py` | Subprocesso fixo, prazo total e cache dos textos |
| `app/tools/external_knowledge.py` | Filtros, indexação e recuperação externa |
| `app/services/rag.py` | Segmentação e indexação compartilhadas com a base local |
| `app/agents/rag.py` | Contexto das ferramentas e referências da resposta |
| `scripts/check_mcp.py` | Diagnóstico real sem banco nem LLM |

## Fontes especificadas no handbook e recorte por perfil

As fontes educativas já constavam na seção **Agente 6 — RAG → Fonte propostas**
do [documento de arquitetura anterior à implementação](https://github.com/delta-app-ofc/delta-handbook/blob/91ec3e5/IA/arquitetura-inteligencia-artificial.md#agente-6--rag).
A primeira implementação deixou passar essa seção e escolheu um artigo do
Senado. Essa escolha foi corrigida: o catálogo ativo agora contém as três
fontes propostas originalmente, e o Senado não participa de novas consultas.

| ID | Fonte | Perfil e tema |
| --- | --- | --- |
| `midr-water-conservation` | [Uso consciente da água — MIDR](https://www.gov.br/mdr/pt-br/assuntos/seguranca-hidrica/projeto-sao-francisco/meio-ambiente-preservado/uso-consciente-da-agua) | Geral, residencial e comercial; `water_conservation` |
| `epa-residential-saving` | [Start Saving — US EPA](https://www.epa.gov/watersense/start-saving) | Residencial; `water_conservation` |
| `epa-commercial-facilities` | [Types of Facilities — US EPA](https://www.epa.gov/watersense/types-facilities) | Comercial/organizacional; `commercial_efficiency` |

O perfil do backend `residential` representa RESIDENCIAL; `organizational`
representa COMERCIAL/organizacional. `RagAgent` constrói a ferramenta com esse
perfil confiável, que não é argumento disponível ao LLM. Cada consulta considera
a fonte geral e a EPA aplicável ao perfil. Um filtro de fonte incompatível
não consulta a outra categoria. Chamadas diretas sem perfil usam somente a
fonte geral; perfis desconhecidos não recebem fontes específicas.

A aba RAG do playground também consulta o perfil do usuário fixo de teste no
backend antes de construir o especialista. O processo precisa executar a branch
de implementação com `MCP_EXTERNAL_ENABLED=true`. A aba isolada testa RAG e
guardrails; Chat completo e Juiz exercitam também a avaliação antes da publicação.
Os exemplos da aba e o painel de ferramentas permitem conferir a seleção de
fontes e os trechos retornados. Não há seletor para substituir o perfil da conta.

O prompt exige orientações adequadas à instalação e à atividade, sem presumir
moradores ou hábitos domésticos para uma conta comercial. As páginas da EPA
são referência educativa estrangeira, não regras brasileiras nem comprovação
da situação da conta. **Não recomendar ou promover WaterSense**, incluindo
programas, selos, certificações, produtos, calculadoras ou campanhas. A URL
original da EPA continua na citação para garantir a rastreabilidade.
Essa é uma instrução ao modelo; testes controlados não comprovam cumprimento
semântico em toda resposta gerada por um provedor real.

As três páginas não fornecem uma tabela de tarifas públicas vigente. Sem
fonte tarifária específica, o agente deve reconhecer a falta de dados e não
inventar preços. A base documental do projeto continua sendo consultada pela
ferramenta local. Não há pesquisa aberta na internet ou navegação automática
pelos links dessas páginas.

Novas fontes exigem revisão de URL, título, tema, audiência, idioma e seletor do
artigo no catálogo, além de testes da extração. Páginas que exigem JavaScript,
apresentam desafios de acesso ou mudam a estrutura podem ficar indisponíveis;
não se indexa o menu como substituto.

## Contratos das ferramentas

### Servidor MCP

| Ferramenta | Entrada | Saída |
| --- | --- | --- |
| `list_knowledge_sources` | `{}` | `sources`: IDs, títulos, URLs, temas, audiências, idiomas e datas de publicação |
| `read_knowledge_source` | `source_id` cadastrado | `status=ok` e `document`, ou `status=unavailable` com mensagem segura |

`document` possui `source_id`, `title`, `url`, `topic`, `audiences`, `language`,
`published_at`, `collected_at` com fuso, `revision` SHA-256 e `text`. A publicação
é `null` quando a data não está confirmada, caso da página MIDR nesta entrega;
a citação informa “não informada”. Para as duas páginas EPA, a data de criação
confirmada nos metadados é 16/01/2017. O cliente verifica os
metadados contra o catálogo e recalcula o hash antes de indexar. O texto deve
ter entre 200 e 60.000 caracteres; o HTTP limita a resposta a 512.000 bytes.

### Ferramentas do Agente RAG

```python
search_knowledge_base(question="Como funciona o vínculo do hidrômetro?", top_k=3)

search_external_knowledge(
    question="Como usar menos água no banho?",
    top_k=3,
    topic="water_conservation",             # opcional, igualdade exata
    source_id="midr-water-conservation",   # opcional, igualdade exata
)
```

`top_k` aceita de 1 a 20, com padrão 3. A pergunta é obrigatória e limitada a
2.000 caracteres. Filtros sem correspondência retornam `insufficient_data`, sem
consultar outra fonte implicitamente. Falha de acesso/configuração retorna
`unavailable`, não ausência de conhecimento. Se houver outras fontes futuramente,
a ferramenta ordena os resultados por score e informa `unavailable_sources`
quando somente parte delas estiver acessível.

Cada trecho externo contém texto, títulos, score, `origin=external`, fonte,
modelo, revisão, URL, tema, publicação, coleta e `citation`. O campo de citação
inclui título com link, revisão e linhas do **texto extraído normalizado**;
essas linhas não são posições do HTML remoto. A revisão de indexação também
inclui a versão do segmentador. Repetir uma revisão não duplica seus pontos.

## Configuração, acesso e ciclo de vida

| Variável | Padrão | Validação |
| --- | --- | --- |
| `MCP_EXTERNAL_ENABLED` | `false` | `true` ou `false` |
| `MCP_TIMEOUT_SECONDS` | `45` | Prazo total de 1 a 120 segundos por consulta MCP |
| `MCP_CACHE_TTL_SECONDS` | `3600` | De 0 a 86.400 segundos; zero desativa o reaproveitamento |

Não há chave de API para a página pública. O servidor MCP é um subprocesso local
com canais privados do sistema operacional, sem porta HTTP ou endpoint público;
seu acesso depende do usuário que executa o backend. Não foi implementado um
servidor remoto com autenticação Bearer/OAuth. As chaves do backend não são
repassadas no ambiente do subprocesso pelo cliente.

O HTTP mantém validação TLS ativa, usa as autoridades confiáveis do sistema e
timeout de 10 segundos por operação. O cliente aplica também o prazo total MCP,
incluindo inicialização e fechamento. Não há retries automáticos nessa camada.

O cache guarda somente textos públicos em RAM por processo e por fonte. Falhas
não entram no cache; uma cópia vencida não é servida quando a fonte falha.
`clear_source_cache()` descarta o cache; reiniciar também aplica novas configurações.
Cada leitura de fonte sem cache abre e fecha seu subprocesso; uma consulta
residencial/comercial pode ler duas fontes, cada qual com seu prazo MCP. Os clientes Gemini/Qdrant
continuam seguindo o ciclo de vida já implementado na API.

A busca vetorial requer `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL`, `QDRANT_URL`
e `QDRANT_API_KEY` quando exigida. `rag_documents` deve existir com vetor sem nome,
3072 dimensões e distância Cosine. O serviço verifica o esquema antes de gerar
embeddings e nunca apaga ou recria uma coleção incompatível.

O vetor padrão pode aparecer na resposta do Qdrant tanto como `VectorParams`
quanto como um mapa cuja única chave é `""`. As duas representações são aceitas;
a chave vazia não indica, por si só, uma mudança para um vetor nomeado distinto.
Mapas com nomes não vazios ou múltiplos vetores continuam sendo recusados.
O ajuste de compatibilidade passou por 71 testes direcionados e por validação
somente de leitura na coleção real, que permaneceu com os mesmos 58 pontos.

Fontes locais e externas são separadas pelo identificador, revisão e modelo;
a fonte externa usa `mcp:<source_id>`. Revisões antigas permanecem
armazenadas, mas não entram na busca atual. A coleção de memória
`session_summaries` não recebe documentos externos. A data de coleta no payload
corresponde à cópia indexada, que pode ser anterior à última consulta HTTP se o
conteúdo não mudou.

## Validação e critérios de aceite

Na raiz do repositório de IA:

```powershell
python -m pip install -r requirements-dev.txt

# Acessa MCP e a página pública; não usa Qdrant ou provedor de linguagem.
# O diagnóstico explícito funciona mesmo com MCP_EXTERNAL_ENABLED=false.
python -m scripts.check_mcp --all

# Suíte controlada: não precisa de credenciais nem de serviços remotos.
$env:APP_ENV = 'test'
python -m pytest tests/test_mcp_sources.py tests/test_external_rag.py tests/test_rag_workflow_integration.py -q
```

Em **01/11/2026**, `python -m scripts.check_mcp --all` executou com sucesso
cliente → subprocesso MCP → HTTPS para as **três fontes propostas**:

| Fonte | Caracteres extraídos | Hash do texto |
| --- | ---: | --- |
| MIDR | 4.854 | `45063d295fa69e947cc4dc8efb668db2a29e77693667b48d9ce9909f3f8ce2e5` |
| EPA residencial | 8.554 | `c832a32b403bc2c845d36c713013ee347185953b72412facae3dbbf668b9ae26` |
| EPA comercial | 12.349 | `386daaac3cace5b64157d657331057a102c7f9574a27b4d6da6c0be1ee0f5bcc` |

Esses são hashes dos textos extraídos, não os hashes do segmentador no índice.
Os **62 testes direcionados** passaram, incluindo extração dos três seletores,
contrato MCP, vínculo de perfil, tentativa de troca do perfil pelo modelo,
falha parcial de fontes, rastreabilidade, contexto e Juiz no grafo.

A regressão completa terminou com **261 testes aprovados e 53 pulados**, sem
falhas. A execução usou `APP_ENV=test` e
`DELTA_TEST_MONGO_URI=mongodb://127.0.0.1:1`, para pular os testes dependentes
de MongoDB sem tocar bancos existentes. O JUnit local está em
`reports/regression.xml` no checkout de implementação. `git diff --check` e
a validação dos links relativos dos guias passaram.


| Demanda | Evidência e limite |
| --- | --- |
| [Recuperação e citação no RAG](https://app.clickup.com/t/86e32aqn9) | Top-k, filtros exatos externos, fontes vinculadas ao perfil confiável, contexto estruturado e lista de fontes; testes temáticos de ranking com embeddings controlados e Qdrant em memória. Qualidade semântica com Gemini real continua pendente. |
| [Configuração MCP](https://app.clickup.com/t/86e32aqra) | Cliente/servidor stdio, contrato, variáveis, modelo de acesso local e chamadas reais às três fontes públicas executados. O escopo foi alterado de clima para conhecimento externo conforme orientação. |
| [Integração de memória, RAG, guardrails, MCP e A2A](https://app.clickup.com/t/86e32arfe) | Testes do grafo preservam contexto e evidências, verificam memória de outro usuário, bloqueio de entrada maliciosa, anonimização, falha MCP e bloqueio por Juiz. MCP também passa pelo protocolo real com HTTP controlado. A2A foi excluído por decisão de negócio em 01/11/2026 e não compõe o aceite. A validação com todos os serviços reais continua pendente. |

Os testes do grafo usam modelos e acesso Mongo/PostgreSQL substituídos e memória
vetorial real em RAM. Eles comprovam o encadeamento dos componentes, não a
persistência remota entre sessões, qualidade dos modelos ou resistência semântica
completa a prompt injection. Documentos e ferramentas continuam sendo dados não
confiáveis: o prompt orienta a ignorar instruções nesses conteúdos, e o Juiz
continua obrigatório. Nenhuma tarefa do ClickUp foi encerrada automaticamente.

## Referências técnicas

- [SDK Python MCP v2](https://py.sdk.modelcontextprotocol.io/).
- [Transporte stdio](https://py.sdk.modelcontextprotocol.io/client/transports/).
- [Saída estruturada das ferramentas](https://py.sdk.modelcontextprotocol.io/servers/structured-output/).
- [Recuperação documental do Delta](rag-retrieval.md).
- [Arquitetura e decisão de escopo das integrações](arquitetura-inteligencia-artificial.md).
