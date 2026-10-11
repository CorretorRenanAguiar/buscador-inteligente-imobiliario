# Configuração do Ambiente

Este documento descreve pré-requisitos e configuração segura de variáveis de ambiente. **Nunca registre valores reais de credenciais neste arquivo, em outros documentos ou no controle de versão.** Utilize apenas os arquivos `.env` locais, que devem permanecer fora do Git.

## Pré-requisitos

- Python 3.11 (referência: [backend/runtime.txt](../backend/runtime.txt)) com pip;
- Node.js (versão compatível com Vite 8) e npm;
- Podman ou Docker, para os serviços locais (PostgreSQL, Redis, Evolution API);
- Projeto Supabase provisionado, com as tabelas `leads` e `interacoes_lead` (o script de criação das tabelas não consta do repositório; a estrutura é inferida pelos payloads de [backend/chatbot_engine.py](../backend/chatbot_engine.py));
- Instância da Evolution API (local via [evolution/docker-compose.yml](../evolution/docker-compose.yml) ou serviço externo) para o envio de WhatsApp.

## Variáveis de ambiente

### Frontend (arquivo `.env` na raiz do projeto)

| Variável | Finalidade |
|---|---|
| `VITE_SUPABASE_URL` | URL do projeto Supabase (uso do componente de diagnóstico) |
| `VITE_SUPABASE_ANON_KEY` | Chave pública ("anon") do Supabase |
| `VITE_API_URL` | URL do backend; se ausente, o frontend utiliza a URL de produção definida em [src/componentes/Chatbot.jsx](../src/componentes/Chatbot.jsx) |

### Backend (arquivo `backend/.env`, conforme [backend/.env.example](../backend/.env.example))

| Variável | Finalidade | Obrigatória |
|---|---|---|
| `SUPABASE_URL` | URL do projeto Supabase | Sim |
| `SUPABASE_KEY` | Chave de serviço do Supabase (acesso às tabelas) | Sim |
| `DEFAULT_TENANT_ID` | Identificador do inquilino padrão (padrão do código: `RA_IMOBILIARIA`) | Não |
| `EVOLUTION_API_URL` | URL base da Evolution API (sem `localhost` em produção) | Sim, para envio de WhatsApp |
| `EVOLUTION_API_KEY` | Chave de API da Evolution (igual a `AUTHENTICATION_API_KEY` da Evolution) | Sim, para envio de WhatsApp |
| `EVOLUTION_TIMEOUT` | Tempo limite das chamadas HTTP, em segundos (padrão: 15) | Não |
| `EVOLUTION_INSTANCE_RA_IMOBILIARIA` | Nome da instância da Evolution associada ao tenant | Sim, para envio de WhatsApp |
| `NUMERO_CORRETOR_RA_IMOBILIARIA` | Número do WhatsApp do corretor, somente dígitos, com DDI/DDD | Sim, para envio de WhatsApp |
| `REDIS_URL` | URL do Redis para sessões (padrão: `redis://localhost:6379/6`; sem Redis, o sistema usa memória local) | Não |
| `KMEANS_MODEL_PATH` / `KMEANS_SCALER_PATH` | Caminhos dos artefatos do modelo K-Means (sem efeito enquanto não houver modelo treinado) | Não |
| `KMEANS_N_CLUSTERS` / `KMEANS_MIN_TRAINING_SAMPLES` | Parâmetros do treinamento futuro do K-Means | Não |

Exemplo de estrutura (com placeholders — substituir apenas no arquivo local):

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

### Evolution API local (arquivo `evolution/.env`, conforme [evolution/.env.example](../evolution/.env.example))

| Variável | Finalidade |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciais do PostgreSQL da Evolution |
| `AUTHENTICATION_API_KEY` | Chave mestra da Evolution API (deve ser igual a `EVOLUTION_API_KEY` do backend) |
| `SERVER_URL` | URL pública local da Evolution (padrão: `http://localhost:8080`) |
| `REDIS_URI` | URI do Redis interno da Evolution (padrão: `redis://redis:6379/6`) |

## Execução local

### Backend

```powershell
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Observação sobre o comando de inicialização: o código importa módulos com o prefixo de pacote (`from backend.chatbot_engine import ...`), de modo que a execução a partir da **raiz do repositório** é `python -m uvicorn backend.main:app`. Em cenários de implantação com diretório raiz apontado para `backend/` (como em configurações anteriores do Railway), o comando documentado era `python -m uvicorn main:app`; o Procfile em [backend/Procfile](../backend/Procfile) reflete esse cenário. Verifique qual dos dois corresponde ao ambiente em uso antes de executar.

### Frontend

```powershell
npm install
npm run dev
```

### Serviços locais da Evolution API

```powershell
podman machine start        # apenas Podman
cd evolution
podman compose up -d        # ou: docker compose up -d
```

A criação da instância e a conexão do número via QR Code são etapas manuais, realizadas pelos endpoints da Evolution (exemplo no [README.md](../README.md)). A verificação da configuração pode ser feita pelo endpoint `GET /diagnostico/evolution` do backend, que informa apenas o estado das variáveis (configurada/ausente), sem expor valores.

## Diferenças entre ambiente local e produção

| Aspecto | Local | Produção (Railway, conforme arquivos de configuração) |
|---|---|---|
| Backend | `uvicorn` com `--reload` | Contêiner do [Dockerfile](../Dockerfile), iniciado por `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT` ([railway.toml](../railway.toml)) |
| Evolution API | Contêiner local (`localhost:8080`) | Serviço externo com URL pública (`EVOLUTION_API_URL` não pode ser `localhost`) |
| PostgreSQL/Redis | Contêineres locais do `docker-compose` | Serviços separados do backend |
| Frontend | `npm run dev` | Sem configuração de hospedagem no repositório; o chat usa `VITE_API_URL` ou URL de produção fixa no código |

## Cuidados de segurança na configuração

- Mantenha `.env`, `backend/.env` e `evolution/.env` fora do controle de versão (o [.gitignore](../.gitignore) já os contempla; ver a seção de limitações sobre arquivos sensíveis identificados no histórico).
- Não reuse a chave anônima do frontend como chave de serviço do backend, nem vice-versa.
- Em produção, configure as variáveis como segredos do provedor de hospedagem ("variáveis privadas"), nunca no código ou em arquivos versionados.
- Restrinja o CORS do backend a origens conhecidas antes de qualquer exposição pública (a configuração atual aceita qualquer origem).
