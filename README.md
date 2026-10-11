# Buscador Inteligente Imobiliário

Protótipo de plataforma web para o mercado imobiliário, composto por página institucional, formulário de busca, chatbot de atendimento com qualificação de leads e persistência em banco de dados. O projeto integra o Trabalho de Conclusão de Curso (TCC) da Pós-Graduação em Desenvolvimento de Projetos Baseados em Tecnologia 4.0 do IF Sudeste MG.

## Contexto e finalidade

O sistema foi desenvolvido como protótipo experimental para demonstrar a viabilidade técnica de um fluxo automatizado de atendimento inicial a potenciais clientes ("leads") do mercado imobiliário, com:

- coleta estruturada de preferências por meio de um chatbot com roteiro fixo de perguntas;
- qualificação do lead por **regras e critérios definidos no sistema** (não se trata de modelo de Machine Learning em operação);
- registro dos leads e das interações em banco de dados Supabase (PostgreSQL);
- envio de relatório descritivo de qualificação ao corretor por WhatsApp, via Evolution API;
- página web com formulário de busca de imóveis (protótipo de interface, sem consulta a base de imóveis).

## Arquitetura geral

A solução é composta por:

- **Frontend:** aplicação React + Vite ([src/](src/)), com a página principal, o formulário de busca, o componente de chat e o banner de cookies.
- **Backend:** API FastAPI ([backend/](backend/)), que expõe os endpoints `/chat` (interface web) e `/webhook/evolution` (integração WhatsApp), executa a máquina de estados do chatbot e a lógica de qualificação.
- **Banco de dados:** Supabase (PostgreSQL), com as tabelas `leads` e `interacoes_lead`.
- **Sessões do chatbot:** Redis, com fallback em memória local quando o Redis não está disponível.
- **Integração WhatsApp:** Evolution API v2.3.7, executada localmente em contêineres ([evolution/docker-compose.yml](evolution/docker-compose.yml)) ou como serviço externo em produção.

O detalhamento dos componentes e do fluxo de informações está em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Funcionalidades implementadas

- Chatbot funcional com fluxo de perguntas e respostas, separado por trilhas de venda (residencial, rural, terreno, comercial) e locação (residencial e comercial), incluindo detecção de permuta e encaminhamento direto para atendimento humano quando o interlocutor se identifica como corretor.
- Qualificação de leads baseada em regras: cálculo de pontuação heurística (0–100), classificação de intenção, maturidade, prioridade comercial, completude das informações, sinais positivos, pontos de atenção e ação recomendada, apresentados em relatório textual ao corretor.
- Persistência de leads e de histórico de interações no Supabase, com identificação de contato recorrente por telefone.
- Envio do relatório de qualificação ao WhatsApp do corretor via Evolution API.
- Endpoint de diagnóstico da configuração da integração (`/diagnostico/evolution`).
- Interface web com página institucional, carrossel de imóveis ilustrativo (dados estáticos), formulário de busca e chat integrado ao endpoint `/chat`.

## Limitações conhecidas

- **Buscador de imóveis:** o formulário de busca é um protótipo de interface; o botão "Buscar imóveis" não executa consulta nem se conecta a uma base de imóveis. Não há módulo de cadastro de imóveis.
- **Machine Learning:** existe código para treinamento opcional do algoritmo K-Means ([backend/enhanced_filters_kmeans.py](backend/enhanced_filters_kmeans.py)), porém **não há modelo treinado nem validado em operação**. A qualificação em funcionamento é integralmente baseada em regras; o K-Means é uma possibilidade de evolução futura, condicionada à existência de dados adequados, treinamento e validação.
- **CRM:** não há CRM completo; o sistema registra leads e interações e envia relatórios ao corretor, sem gestão de usuários, permissões, funil ou relacionamento estruturado.
- **Autenticação:** os endpoints do backend não implementam autenticação ou autorização.
- **CORS:** o middleware está configurado com `allow_origins=["*"]`, adequado apenas para ambiente de desenvolvimento do protótipo.
- **Webhook WhatsApp:** o webhook `/webhook/evolution` está implementado no backend, mas o `docker-compose` local da Evolution API está com `WEBHOOK_GLOBAL_ENABLED: "false"`; a configuração do webhook é etapa manual e não foi validada nesta auditoria.

A lista completa de limitações e o plano de evolução estão em [docs/LIMITACOES_E_EVOLUCAO.md](docs/LIMITACOES_E_EVOLUCAO.md).

## Pré-requisitos

- Python 3.11 (ver [backend/runtime.txt](backend/runtime.txt)) e pip;
- Node.js e npm (para o frontend Vite);
- Podman ou Docker (para executar localmente PostgreSQL, Redis e Evolution API);
- Projeto Supabase com as tabelas `leads` e `interacoes_lead` criadas.

## Configuração de variáveis de ambiente

As credenciais são configuradas por variáveis de ambiente. **Nunca versione arquivos `.env` nem inclua valores reais em documentação.** Utilize os arquivos de exemplo como referência.

### Frontend (raiz do projeto)

Copie e adapte com placeholders:

```
VITE_SUPABASE_URL=SUA_URL_DO_SUPABASE
VITE_SUPABASE_ANON_KEY=SUA_CHAVE_ANON_DO_SUPABASE
VITE_API_URL=SUA_URL_DO_BACKEND   # opcional; se ausente, o frontend usa a URL de produção definida no código
```

### Backend ([backend/.env.example](backend/.env.example))

```
SUPABASE_URL=SUA_URL_DO_SUPABASE
SUPABASE_KEY=SUA_CHAVE_DE_SERVICO_DO_SUPABASE
DEFAULT_TENANT_ID=RA_IMOBILIARIA
EVOLUTION_API_URL=SUA_URL_DA_EVOLUTION_API
EVOLUTION_API_KEY=SUA_CHAVE_DA_EVOLUTION_API
EVOLUTION_TIMEOUT=15
EVOLUTION_INSTANCE_RA_IMOBILIARIA=SUA_INSTANCIA_EVOLUTION
NUMERO_CORRETOR_RA_IMOBILIARIA=SEU_NUMERO_COM_DDD_SOMENTE_DIGITOS
REDIS_URL=SUA_URL_DO_REDIS
```

Variáveis opcionais do módulo de segmentação (sem efeito enquanto não houver modelo treinado): `KMEANS_MODEL_PATH`, `KMEANS_SCALER_PATH`, `KMEANS_N_CLUSTERS`, `KMEANS_MIN_TRAINING_SAMPLES`.

### Evolution API local ([evolution/.env.example](evolution/.env.example))

```
POSTGRES_USER=evolution
POSTGRES_PASSWORD=SUA_SENHA_FORTE_DO_POSTGRES
POSTGRES_DB=evolution
AUTHENTICATION_API_KEY=SUA_CHAVE_DE_API_FORTE
SERVER_URL=http://localhost:8080
REDIS_URI=redis://redis:6379/6
```

O valor de `AUTHENTICATION_API_KEY` (Evolution) deve ser igual ao de `EVOLUTION_API_KEY` (backend).

Instruções detalhadas em [docs/CONFIGURACAO.md](docs/CONFIGURACAO.md).

## Execução local

### Backend

```powershell
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

(Observação: em alguns cenários de implantação, como com Root Directory apontado para `backend`, o comando utilizado é `python -m uvicorn main:app`; ver [docs/CONFIGURACAO.md](docs/CONFIGURACAO.md).)

### Frontend

```powershell
npm install
npm run dev
```

### Evolution API (ambiente local, com Podman ou Docker)

```powershell
cd evolution
podman compose up -d   # ou: docker compose up -d
podman ps
```

A Evolution API local responde em `http://localhost:8080`. A criação da instância e a conexão do número (QR Code) são etapas manuais realizadas pelos endpoints da Evolution. Exemplo de criação de instância (substituindo os placeholders):

```powershell
curl.exe -X POST http://localhost:8080/instance/create `
	-H "apikey: SUA_AUTHENTICATION_API_KEY" `
	-H "Content-Type: application/json" `
	-d "{\"instanceName\":\"SUA_INSTANCIA\",\"integration\":\"WHATSAPP-BAILEYS\"}"
```

As instruções de execução acima descrevem a configuração prevista; nesta auditoria foram verificados o código e a configuração, não a execução completa do ambiente integrado.

## Implantação (Railway)

- O backend é implantado a partir do [Dockerfile](Dockerfile) na raiz do repositório (`python -m uvicorn backend.main:app`), conforme [railway.toml](railway.toml).
- **Não** utilizar `EVOLUTION_API_URL` apontando para `localhost` em produção: a Evolution API, o PostgreSQL e o Redis são serviços separados do backend.
- Configurar as variáveis de ambiente do backend como variáveis privadas do serviço no provedor de hospedagem.

## Testes

Os testes automatizados existentes são unitários, executados com mocks (sem envio real de mensagens nem acesso a serviços externos):

```powershell
python -m unittest backend.test_evolution backend.test_chatbot_corretor backend.test_chatbot_historico -v
```

Resultado da execução nesta auditoria (11/10/2026, Python 3.14.7, ambiente local): **8 testes executados, todos aprovados**. Detalhes em [docs/TESTES.md](docs/TESTES.md).

Observação: o script `verify:chatbot-engine` definido em [package.json](package.json) referencia [backend/verify_chatbot_engine.py](backend/verify_chatbot_engine.py), que **não existe** no backend atual (encontra-se apenas na pasta de rascunho [arquivo_rascunho/testes/verify_chatbot_engine.py](arquivo_rascunho/testes/verify_chatbot_engine.py)).

## Privacidade, proteção de dados e credenciais

- O chatbot coleta dados pessoais informados voluntariamente pelo usuário (nome de contato via WhatsApp, telefone, preferências e faixa de renda), que são armazenados no Supabase e encaminhados ao corretor. O tratamento desses dados no contexto da pesquisa observa o protocolo metodológico do TCC; não houve uso de bases de clientes de imobiliárias, conversas reais de WhatsApp ou documentos pessoais como dados de treinamento.
- Nos testes e exemplos deste repositório não são utilizados dados pessoais reais.
- Credenciais não devem ser versionadas. **Atenção:** nesta auditoria foi identificado que os arquivos `.env` e `backend/.env` constam como versionados no histórico do repositório, apesar de constarem do `.gitignore`. Recomenda-se tratar as credenciais neles contidas como potencialmente expostas: realizar rotação das chaves e remover os arquivos do controle de versão (plano de correção proposto na documentação de limitações), sem que qualquer valor tenha sido reproduzido nesta documentação.

## Documentação complementar

- [docs/ARQUITETURA.md](docs/ARQUITETURA.md) — componentes, responsabilidades e fluxo de informações;
- [docs/IMPLEMENTACAO.md](docs/IMPLEMENTACAO.md) — detalhes da implementação, com referências a arquivos e funções;
- [docs/CONFIGURACAO.md](docs/CONFIGURACAO.md) — pré-requisitos e configuração segura de ambiente;
- [docs/TESTES.md](docs/TESTES.md) — testes existentes, objetivos e resultados observados;
- [docs/LIMITACOES_E_EVOLUCAO.md](docs/LIMITACOES_E_EVOLUCAO.md) — limitações verificadas e evolução futura.

## Relação com o TCC

Este repositório corresponde ao artefato tecnológico experimental descrito no TCC da Pós-Graduação em Desenvolvimento de Projetos Baseados em Tecnologia 4.0 do IF Sudeste MG. A pesquisa de campo com profissionais do mercado imobiliário constitui etapa posterior à aprovação ética prevista no protocolo da pesquisa; o protótipo aqui documentado poderá subsidiar a coleta de percepções sobre utilidade, aplicabilidade e limitações, sem que tal demonstração, por si só, comprove eficácia comercial. No texto do TCC, adotam-se as siglas AI (Artificial Intelligence) e ML (Machine Learning), com distinção expressa entre a automação baseada em regras aqui implementada e a possível aplicação futura de técnicas de ML.
