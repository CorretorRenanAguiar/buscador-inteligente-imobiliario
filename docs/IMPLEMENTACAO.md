# Implementação

Este documento descreve o que está efetivamente implementado no código, com referências aos arquivos e funções correspondentes. Data de referência da auditoria: 11/10/2026 (branch `tcc-v2-final`).

## 1. Endpoints do backend

Definidos em [backend/main.py](../backend/main.py):

| Endpoint | Método | Função |
|---|---|---|
| `/` | GET | Verificação de disponibilidade (`status: online`) |
| `/chat` | POST | Recebe `mensagem`, `session_id` e `tenant_id`; aciona `processar_chatbot` |
| `/diagnostico/evolution` | GET | Informa estado da configuração da Evolution (sem expor valores) e consulta o estado de conexão da instância |
| `/webhook/evolution` | POST | Recebe eventos `MESSAGES.UPSERT` da Evolution API e aciona o chatbot com o telefone do remetente como sessão |

O tratamento de exceções retorna `500` com mensagem genérica ("Erro interno no servidor"), registrando o detalhe apenas no log do servidor.

## 2. Motor do chatbot

Implementado em [backend/chatbot_engine.py](../backend/chatbot_engine.py), função `processar_chatbot`, como **máquina de estados** persistida por sessão:

- **Sessões:** chave `chatbot:sessao:<tenant>:<session_id>` no Redis (TTL 3600 s); quando o Redis está indisponível, usa o dicionário em memória `MEMORY_SESSIONS` (não persistente entre processos).
- **Trilhas de diálogo:**
  - **Venda residencial:** objetivo → tipo de imóvel → uso → primeiro imóvel → quartos → banheiros → vagas → pet → localização → faixa de valor → momento da compra → financiamento → FGTS → renda familiar → WhatsApp.
  - **Imóvel rural** (fazenda, granja, sítio, chácara): objetivo rural → hectares → localização → faixa de valor → momento → financiamento → renda familiar (etapa FGTS é omitida) → WhatsApp.
  - **Terreno:** finalidade do terreno → localização → demais etapas da trilha de venda.
  - **Locação:** finalidade (residencial/comercial) → tipo de imóvel → (comercial: características essenciais; residencial: quartos/banheiros/vagas/pet/mobiliado) → localização → faixa de aluguel → prazo de ocupação → garantia locatícia (caução, seguro-fiança, cartão de crédito, fiador) → WhatsApp.
- **Desvios especiais:**
  - Detecção de **permuta** por palavras-chave (`detectar_permuta`): encaminha diretamente à coleta de WhatsApp para análise personalizada.
  - Identificação de **corretor parceiro** ("Sou corretor"): encerra a sessão e informa atendimento humano, sem qualificação nem persistência.
- **Validações:** `validar_localizacao` rejeita entradas curtas ou termos de teste; o telefone é normalizado (dígitos, remoção de prefixo 55) e validado por tamanho mínimo.
- **Prompt de IA:** o arquivo [backend/prompts/chatbot_prompt.txt](../backend/prompts/chatbot_prompt.txt) descreve um comportamento de assistente com linguagem natural, porém **não é lido nem utilizado** pelo código auditado — o diálogo é integralmente dirigido pelo roteiro de estados. Da mesma forma, a dependência `openai` consta em [backend/requirements.txt](../backend/requirements.txt), mas não há importação da OpenAI no código do backend.

## 3. Qualificação de leads — baseada em regras

Implementada em [backend/enhanced_filters_kmeans.py](../backend/enhanced_filters_kmeans.py), função `qualificar_sessao_chatbot`, que consolida:

- **Pontuação heurística** (`heuristic_lead_score`): inicia em 40 pontos e soma critérios como objetivo (investidor +15; comprar +10; alugar +5), prazo (imediato +15; 3 meses +10; 6 meses +5), valor de entrada declarado, faixa de valor, composição de renda, permuta e informação de WhatsApp; limitado ao intervalo 0–100.
- **Intenção** (`_determinar_intencao`): INVESTIDOR, LOCAÇÃO, RURAL/LAZER, COMPRA RESIDENCIAL ou POTENCIAL COMPRADOR.
- **Maturidade** (`_determinar_maturidade`): derivada do prazo informado (decisão imediata, curto, médio ou longo prazo).
- **Prioridade comercial** (`_determinar_prioridade`): ALTA, MÉDIA ou NORMAL, a partir de pontuação e maturidade.
- **Justificativas e recomendação** (`_gerar_justificativas`, `_gerar_recomendacao`): textos descritivos que explicitam os critérios utilizados, incluindo a ressalva de que a classificação "representa apoio à decisão comercial e não aprovação de crédito".

No motor do chatbot, complementam o relatório (funções em [backend/chatbot_engine.py](../backend/chatbot_engine.py)):

- **Completude** (`_calcular_completude_qualificacao`): percentual de campos relevantes preenchidos (ALTA ≥ 80%, MÉDIA ≥ 50%, BAIXA < 50%), com lista de campos específica por trilha (locação, rural ou venda residencial).
- **Sinais positivos** (`_gerar_sinais_positivos`) e **pontos de atenção** (`_gerar_pontos_atencao`): listas descritivas derivadas da presença ou ausência de informações, sem inferências além dos dados declarados.

O sistema também mantém, para compatibilidade, um **score legado** (`calcular_score`) e uma **classificação legada** frio/morno/quente (`_classificacao_legada`), gravados nas colunas `score_lead` e `classificacao_lead` da tabela `leads`.

### 3.1 Sobre o K-Means

O módulo inclui implementação de extração de atributos (`extract_features_for_kmeans`), treinamento (`train_kmeans`/`treinar_kmeans`) e inferência opcional do algoritmo K-Means (scikit-learn). Contudo:

- **não existe modelo treinado** no repositório (o diretório `backend/models/` não existe);
- **nenhum endpoint, tarefa ou script do projeto chama o treinamento** — as funções existem, mas não são acionadas pelo sistema em operação;
- quando não há artefato de modelo, a função de qualificação registra nas justificativas que "Modelo K-Means ainda não treinado ou incompatível" e segue **exclusivamente com as regras**;
- em caso de erro na qualificação avançada, o motor utiliza _fallback_ com o score legado e classificação por regras (`_qualificar_para_relatorio`).

Portanto, a qualificação em funcionamento é **integralmente baseada em regras e critérios definidos no sistema**. O K-Means é código preparado para evolução futura, sem evidência de treinamento, validação ou uso operacional.

## 4. Persistência (Supabase)

Implementada em [backend/chatbot_engine.py](../backend/chatbot_engine.py):

- `_construir_payload_lead`: mapeia os dados da sessão para as colunas da tabela `leads`, convertendo textos como "2 quartos" para inteiro (`_extrair_numero`) e consolidando campos adicionais em `observacoes`.
- `persistir_lead_e_interacao`: normaliza e valida o telefone; consulta lead existente pelo número (`buscar_lead_por_telefone`); cria novo registro (contato "novo") ou atualiza o existente (contato "recorrente", `_atualizar_lead_recorrente`); registra a interação na tabela `interacoes_lead` com os dados da sessão e o resultado da qualificação (`salvar_interacao_lead`).
- Sem telefone válido, o fluxo preserva o comportamento anterior (`salvar_lead_supabase`), inserindo o lead sem vínculo de interação.

Observação: [backend/database_supabase.py](../backend/database_supabase.py) contém uma implementação mais rica de persistência (composição de renda, participantes, campos de qualificação), mas **não é utilizada** pelo fluxo atual; seu uso pressuporia campos que o chatbot não coleta na trilha atual (por exemplo, `participantes_renda`, `valor_entrada`).

## 5. Integração WhatsApp (Evolution API)

Implementada em [backend/evolution_api.py](../backend/evolution_api.py):

- `enviar_mensagem_whatsapp`: valida configuração, monta a requisição (`construir_requisicao_evolution`) e envia o texto ao endpoint `/message/sendText/{instance}` com a chave no cabeçalho `apikey`;
- instância e número do corretor são resolvidos por tenant (`_configuracao_tenant`);
- números são mascarados nos logs (`_mascarar_numero`);
- falhas de rede, tempo limite e recusas HTTP são tratadas com retorno estruturado de erro, sem interromper o atendimento ao usuário (o chatbot informa falha no envio e oferece link direto `wa.me` para o corretor).

O webhook de entrada (`/webhook/evolution`) está implementado no backend; no ambiente local, o `docker-compose` da Evolution está com `WEBHOOK_GLOBAL_ENABLED: "false"`, de modo que a ativação do webhook é etapa de configuração manual não validada nesta auditoria.

## 6. Frontend

- [src/App.jsx](../src/App.jsx): página única com cabeçalho, seção principal (hero), carrossel de imóveis com **dados estáticos** (quatro imóveis ilustrativos codificados no componente), formulário de busca, chat e banner de cookies.
- [src/componentes/Busca.jsx](../src/componentes/Busca.jsx): formulário com abas "Comprar/Alugar" e campos de tipo de imóvel, quartos, cidade/bairro e faixa de preço. O botão "Buscar imóveis" **não possui ação associada**: não há consulta ao Supabase, ao backend ou a qualquer base de imóveis.
- [src/componentes/Chatbot.jsx](../src/componentes/Chatbot.jsx): janela de chat que envia as mensagens ao `POST /chat` e exibe respostas, opções de botões e link do WhatsApp do corretor ao final.
- [src/componentes/CookieBanner.jsx](../src/componentes/CookieBanner.jsx): banner de consentimento de cookies.
- [src/componentes/TesteSupabase.jsx](../src/componentes/TesteSupabase.jsx): componente de diagnóstico que insere um lead de teste (dados fictícios) diretamente do navegador; **não é renderizado** pela aplicação principal.

## 7. Materiais de apoio na raiz do repositório

Arquivos como [requisicao_chat.json](../requisicao_chat.json), [resposta_chat.json](../resposta_chat.json), [resposta_headers.txt](../resposta_headers.txt) e [teste_whatsapp.json](../teste_whatsapp.json) são artefatos de testes manuais realizados durante o desenvolvimento (a resposta registrada é um erro HTTP 422 de validação de JSON). O arquivo [teste_whatsapp.json](../teste_whatsapp.json) contém um número de telefone aparentemente real; recomenda-se sua remoção do repositório (ver [LIMITACOES_E_EVOLUCAO.md](LIMITACOES_E_EVOLUCAO.md)).

## 8. Divergências observadas

| Afirmação anterior (README/material) | Evidência no código |
|---|---|
| "Segmentação de leads com IA" | A segmentação operacional é por regras; K-Means sem modelo treinado |
| Prompt de chatbot com IA generativa | Arquivo de prompt não é utilizado; diálogo é máquina de estados |
| Dependência `openai` | Instalada, porém sem qualquer importação no backend |
| `database_supabase.py` como camada de dados | Implementada, mas não referenciada pelo fluxo atual |
| Script `verify:chatbot-engine` | Arquivo ausente em `backend/` (existe apenas em `arquivo_rascunho/testes/`) |
| Textos da landing page ("recomendação inteligente de imóveis", "análise comportamental") | Não há recomendação automatizada de imóveis nem análise comportamental implementada |
