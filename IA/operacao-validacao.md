# Operação e validação da IA

## Objetivo

Reunir caminhos e comandos para desenvolver, executar e verificar a IA. Os comandos abaixo são para a raiz do repositório **`delta-artificial-intelligence`**.

## Desenvolvimento local

Use Python 3.12, conforme Dockerfile e CI. Instale dependências de desenvolvimento:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip check
```

Copie `.env.example` para `.env` local e configure os componentes utilizados conforme [settings](settings.md). Não versione credenciais. A cópia do exemplo aplica `JEV_PROBABILITY_THRESHOLD=0.50`, diferente do default 0,70 do código.

Bancos locais de desenvolvimento:

```powershell
docker compose -p delta-artificial-intelligence-dev -f docker-compose.dev.yml config --quiet
docker compose -p delta-artificial-intelligence-dev -f docker-compose.dev.yml up -d --wait
docker compose -p delta-artificial-intelligence-dev -f docker-compose.dev.yml ps
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

SQL usa porta local 5432 e Mongo 27018, salvo override de portas do Compose. PostgreSQL carrega cópias de bootstrap em volume vazio; o Mongo inicia sem a carga do produto. Esse Compose não sobe Qdrant nem provedores. Verifique funções/views recentes exigidas pelas tools, especialmente cadastro de hábito e consultas organizacionais.

Para encerrar preservando volumes:

```powershell
docker compose -p delta-artificial-intelligence-dev -f docker-compose.dev.yml down
```

## Console e runners

`/playground/` serve `frontend/`: chat, agentes, roteador, Juiz e Monitor. Usa usuário fixo **123456789**, sem Bearer. Por padrão fica ligado em development/test e desligado em staging/production; `DELTA_PLAYGROUND_ENABLED` sobrescreve isso.

O console usa ferramentas e provedores reais quando configurados. A aba de especialista isolado não corresponde ao percurso completo da API. Chat/Juiz chamam o grafo com `persist_session=False`, mas **a rota do console salva pergunta original e resposta por seu próprio caminho** em `chat_sessions`, criando ObjectId se necessário. Logo, não é modo sem persistência nem garante anonimização da pergunta armazenada. Hábitos também pode gravar cadastro por ferramenta.

Runners existentes:

```powershell
python manual_chat.py consumption "Quanto consumi ontem?"
python manual_chat_judge.py --user-id 1 --no-history
```

O primeiro usa configuração/ID de demonstração do script. No segundo, use um usuário de teste autorizado; `--no-history` desliga gravação do histórico pelo runner, não as escritas de ferramentas como cadastro de hábito. Não imprime candidatas bloqueadas como resposta liberada.

Diagnósticos presentes: `python -m scripts.check_mcp --all` (fonte pública/MCP), `python -m scripts.bench_pool` (SELECTs/benchmark SQL), `python -m scripts.cost_projection` (métricas) e `python -m scripts.langsmith_reconcile` (comparação com LangSmith quando configurado). Os antigos `scripts.check_postgres` e `scripts.check_mongo` não estão nessa árvore.

## Testes e relatórios

Com dependências instaladas:

```powershell
$env:APP_ENV = "test"
python -m compileall -q app
python -m pytest tests -q
python tests/run_ci.py
node --test frontend/markdown.test.mjs
```

O runner `tests/run_ci.py` produz `reports/junit.xml`, `coverage.xml`, HTML e resumo com cobertura de branches. Ele executa a suíte; não é somente conversão de relatórios. O teste JavaScript é um comando adicional, não um passo do `test.yml` atual.

A suíte contém casos isolados com substitutos e casos de histórico com MongoDB real. A fixture de histórico usa `DELTA_TEST_MONGO_URI` (default `localhost:27018`) e **apaga o database `delta_test_historico`** no ciclo de teste. Use serviço descartável e não execute em paralelo com outra atividade que dependa desse database. Sem Mongo, esses testes são pulados. Resultado sem falhas com skips não confirma integração.

Uma validação real precisa exercitar autenticação com token do backend, ownership, fontes de consumo, tarifas/funções/views, escrita e conflito de hábitos, histórico, fechamento/resumo, RAG atual e falhas dos provedores. Isso requer dados e ambiente próprios.

## CI e entrega existentes

- `.github/workflows/test.yml`: PR/manual; instala dependências, `pip check`, compila e executa pytest com `APP_ENV=test`; reporta resultado pela automação compartilhada.
- `.github/workflows/sonar.yml`: PR/push main; executa `tests/run_ci.py`, publica artefato e chama scan compartilhado.
- `sonar-policy.yml` e `sonar-review-notify.yml`: integração com política/revisões compartilhadas.
- `trigger_actions.yml`: governança de PR independente dos testes.
- `cd.yml`: push na main chama `RENDER_DEPLOY_HOOK`. Não declara dependência explícita do CI nesse workflow.

O Dockerfile usa Python 3.12 slim, certificados/fusos, usuário sem root, `APP_ENV=production` e Uvicorn com um worker em `${PORT:-10000}`. Copia `app/` e `frontend/`; scripts diagnósticos não entram na imagem. O servidor MCP em `app/` entra.

A presença dos workflows não comprova configuração dos secrets, settings do Render, proteção de branch ou sucesso de deploy.

## Como manter estes documentos

Mantenha os contratos alinhados ao funcionamento da aplicação, preservando explicações, exemplos e decisões válidos. Substitua somente informações incorretas ou desatualizadas e acrescente os detalhes que faltarem. Diferencie funcionalidades disponíveis, propostas, testes executados e medições históricas. O [índice](leia-me.md) concentra divergências conhecidas sem transformar propostas em funcionalidades.

## Código relacionado

- [Dockerfile](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/Dockerfile)
- [.github/workflows/test.yml](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/.github/workflows/test.yml)
- [.github/workflows/cd.yml](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/.github/workflows/cd.yml)
- [app/routes/playground.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/routes/playground.py)
- [tests/run_ci.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/tests/run_ci.py)
