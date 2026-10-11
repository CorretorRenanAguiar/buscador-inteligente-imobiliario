# Limitações e Evolução Futura

Este documento registra as limitações verificadas na auditoria técnica de 11/10/2026 (branch `tcc-v2-final`), distingue funcionalidades parciais ou ausentes e aponta possibilidades de desenvolvimento futuro. Nenhum item listado como "evolução futura" deve ser apresentado como entrega já realizada.

## 1. Limitações de segurança (prioridade alta)

### 1.1 Arquivos de credenciais versionados no histórico

Os arquivos `.env` (raiz) e `backend/.env` constam como **versionados** no repositório, embora listados no [.gitignore](../.gitignore). Seu conteúdo inclui nomes de variáveis de credenciais do Supabase e da Evolution API. **Nenhum valor foi reproduzido nesta documentação.**

- **Risco:** credenciais potencialmente expostas no histórico Git (inclusive em commits anteriores).
- **Ação recomendada (não executada nesta auditoria):**
  1. Tratar as credenciais como comprometidas e realizar **rotação** das chaves do Supabase e da Evolution API;
  2. Remover os arquivos do controle de versão (`git rm --cached .env backend/.env`) e confirmar que o `.gitignore` impede novo versionamento;
  3. Avaliar, com apoio da equipe, a necessidade de reescrita do histórico (por exemplo, `git filter-repo`), ciente de que se trata de operação destrutiva que exige coordenação e nova clonagem do repositório;
  4. Registrar o ocorrido e a data da rotação.

### 1.2 Número de telefone aparentemente real em artefato de teste

O arquivo [teste_whatsapp.json](../teste_whatsapp.json), versionado na raiz, contém um número de telefone com DDI/DDD aparentemente real.

- **Ação recomendada:** remover o arquivo do repositório ou substituir o número por um placeholder (por exemplo, `5500999990000`), após confirmar que não há dependências operacionais sobre ele.

### 1.3 CORS permissivo

O backend aceita requisições de qualquer origem (`allow_origins=["*"]` em [backend/main.py](../backend/main.py)).

- **Ação recomendada:** restringir às origens conhecidas do frontend antes de exposição pública.

### 1.4 Endpoints sem autenticação

`/chat`, `/webhook/evolution` e `/diagnostico/evolution` não possuem autenticação ou autorização. O webhook, em particular, aceita cargas de qualquer origem que conheça a URL.

- **Ação recomendada:** validar a origem dos webhooks (por exemplo, verificação de segredo/cabeçalho configurado na Evolution API) e proteger o endpoint de diagnóstico.

## 2. Limitações funcionais verificadas

| Item | Situação | Evidência |
|---|---|---|
| Buscador de imóveis | **Parcialmente implementado (protótipo de interface):** formulário existe, mas o botão não executa consulta; não há base de imóveis | [src/componentes/Busca.jsx](../src/componentes/Busca.jsx) |
| Carrossel de imóveis da página inicial | Dados estáticos codificados no componente (ilustrativo) | [src/App.jsx](../src/App.jsx) |
| Cadastro/gestão de imóveis | **Não implementado** | Ausência de endpoints, telas ou tabelas correspondentes |
| CRM completo (funil, usuários, permissões, relacionamento) | **Não implementado**; há apenas registro de leads e interações | [backend/chatbot_engine.py](../backend/chatbot_engine.py) |
| Autenticação e gestão de usuários | **Não implementado** | [backend/main.py](../backend/main.py) |
| Machine Learning (K-Means) | **Código preparado, sem modelo treinado nem validado**; qualificação em operação é baseada em regras | [backend/enhanced_filters_kmeans.py](../backend/enhanced_filters_kmeans.py); diretório `backend/models/` inexistente; nenhum chamador do treinamento |
| IA generativa no diálogo | **Não implementada**: diálogo é máquina de estados; [backend/prompts/chatbot_prompt.txt](../backend/prompts/chatbot_prompt.txt) não é utilizado; dependência `openai` sem uso | [backend/chatbot_engine.py](../backend/chatbot_engine.py) |
| Camada de dados `database_supabase.py` | Implementada, porém **não utilizada** pelo fluxo atual | ausência de importações no backend |
| Webhook WhatsApp de entrada | Implementado no backend, **não validado**; `WEBHOOK_GLOBAL_ENABLED: "false"` no compose local | [backend/main.py](../backend/main.py), [evolution/docker-compose.yml](../evolution/docker-compose.yml) |
| Hospedagem do frontend | **Não configurada** no repositório | ausência de pipeline/configuração |
| Multi-inquilino | Parametrizado no código, mas configurado apenas para `RA_IMOBILIARIA` | [backend/evolution_api.py](../backend/evolution_api.py) |
| Consulta de lead por telefone | Implementada com varredura completa da tabela em memória (não escala) | `buscar_lead_por_telefone` em [backend/chatbot_engine.py](../backend/chatbot_engine.py) |
| Script `verify:chatbot-engine` | Referenciado em [package.json](../package.json), mas o arquivo alvo não existe em `backend/` | [arquivo_rascunho/testes/verify_chatbot_engine.py](../arquivo_rascunho/testes/verify_chatbot_engine.py) |

## 3. Limitações metodológicas (relação com o TCC)

- O protótipo **não foi submetido a avaliação por profissionais** do mercado imobiliário; a pesquisa de campo é etapa posterior à aprovação ética prevista no protocolo da pesquisa.
- Não houve validação com leads reais nem mensuração de resultados comerciais (conversão, retorno sobre investimento, custo de aquisição). Nenhum dado dessa natureza consta do repositório.
- Não foram utilizados como dados de treinamento bases de clientes de imobiliárias, conversas reais de WhatsApp ou documentos pessoais, em conformidade com o protocolo metodológico.
- A qualificação de leads é automação **baseada em regras** e não deve ser denominada modelo de ML; afirmações sobre aprendizado contínuo ou melhoria automática com o uso não possuem suporte no código.
- A documentação técnica do repositório, isoladamente, não comprova conformidade integral com normas ABNT (aplicáveis ao documento do TCC) nem com a LGPD, cuja avaliação demanda análise de fluxos de dados, finalidades, controles e responsabilidades.

## 4. Evolução futura (não implementada)

Curto/médio prazo:

1. Correção das questões de segurança da seção 1 (rotação de credenciais, remoção de arquivos sensíveis, restrição de CORS, proteção do webhook).
2. Implementação efetiva do buscador: modelo de dados de imóveis, cadastro e consulta com filtros no backend, substituindo os dados estáticos do frontend.
3. Ativação e validação do webhook da Evolution API para atendimento integral pelo WhatsApp.
4. Ampliação da cobertura de testes (trilhas completas do chatbot, qualificação, endpoints HTTP) e correção do script `verify:chatbot-engine`.
5. Consolidação da camada de dados (unificar `database_supabase.py` e as funções de persistência do motor) e consulta de lead por telefone com filtro no banco.

Médio/longo prazo:

6. Módulo de CRM: gestão de usuários e permissões, funil de atendimento e histórico estruturado de relacionamento, integrando chatbot e buscador.
7. Aplicação de técnicas de ML à segmentação de leads (por exemplo, o K-Means já preparado no código), **condicionada** à existência de volume adequado de dados, com treinamento, validação e avaliação documentados, e observância das salvaguardas éticas e legais aplicáveis.
8. Métricas e avaliação empírica com profissionais, após a aprovação ética, para verificar utilidade, aplicabilidade, limitações, transparência e adequação ao fluxo de trabalho — sem que a demonstração do protótipo, por si só, seja tratada como comprovação de eficácia comercial.
