# Testes

Este documento relaciona os testes automatizados existentes, seus objetivos, o procedimento de execução e os resultados efetivamente observados. Data de referência: 11/10/2026.

## Testes existentes

| Arquivo | Objetivo | Técnica |
|---|---|---|
| [backend/test_evolution.py](../backend/test_evolution.py) | Validar a montagem da requisição à Evolution API, o envio com resposta simulada e o tratamento de falha de conexão | `unittest` com `unittest.mock` (sem HTTP real) |
| [backend/test_chatbot_corretor.py](../backend/test_chatbot_corretor.py) | Validar que a mensagem "Sou corretor" encaminha a atendimento humano sem qualificar nem persistir lead | `unittest` assíncrono com mocks de persistência, envio e qualificação |
| [backend/test_chatbot_historico.py](../backend/test_chatbot_historico.py) | Validar a criação de lead e interação, a detecção de contato recorrente por telefone e o fluxo sem telefone | `unittest` com cliente Supabase falso em memória (`FakeSupabase`) |

## Procedimento de execução

Os testes não enviam mensagens reais, não acessam o Supabase nem a Evolution API e não utilizam credenciais:

```powershell
python -m unittest backend.test_evolution backend.test_chatbot_corretor backend.test_chatbot_historico -v
```

## Resultado observado

Execução realizada nesta auditoria (11/10/2026, Python 3.14.7, ambiente virtual local do desenvolvedor), a partir da raiz do repositório:

```
Ran 8 tests in 0.163s
OK
```

Detalhamento:

- `test_evolution.py` — 3 testes aprovados:
  - `test_constroi_requisicao_evolution`: URL, cabeçalho `apikey` e carga útil montados corretamente;
  - `test_envia_com_mock_http`: envio com resposta simulada retorna sucesso;
  - `test_trata_falha_de_conexao`: falha de conexão simulada retorna erro estruturado ("Não foi possível comunicar com a Evolution API.").
- `test_chatbot_corretor.py` — 1 teste aprovado: o fluxo de corretor parceiro não aciona qualificação, persistência ou envio.
- `test_chatbot_historico.py` — 4 testes aprovados:
  - criação de lead novo com interação;
  - contato recorrente atualiza o lead existente sem duplicá-lo;
  - dois atendimentos do mesmo telefone geram interações distintas;
  - ausência de telefone preserva o fluxo legado de inserção simples.

## Testes não executados

- **Testes de integração com serviços reais** (Supabase, Evolution API, Redis, Railway): não executados, pois demandariam credenciais e poderiam gerar envio de mensagens ou alteração de dados remotos, o que está fora do escopo da auditoria.
- **Teste do frontend:** não há testes automatizados do frontend no repositório; há apenas o componente manual de diagnóstico [src/componentes/TesteSupabase.jsx](../src/componentes/TesteSupabase.jsx), não executado nesta auditoria.
- **Script `verify:chatbot-engine` ([package.json](../package.json)):** não executável — o arquivo [backend/verify_chatbot_engine.py](../backend/verify_chatbot_engine.py) não existe; há apenas uma versão em [arquivo_rascunho/testes/verify_chatbot_engine.py](../arquivo_rascunho/testes/verify_chatbot_engine.py), que não foi executada por pertencer a material de rascunho.
- **[backend/teste.py](../backend/teste.py):** script auxiliar de desenvolvimento, não estruturado como suíte de testes; não executado nesta auditoria.

## Limitações da cobertura

- Não há testes do fluxo conversacional completo (trilhas de venda, locação, rural e permuta) nem das funções de qualificação de [backend/enhanced_filters_kmeans.py](../backend/enhanced_filters_kmeans.py).
- Não há testes do webhook `/webhook/evolution` nem do endpoint `/chat` na camada HTTP.
- Os resultados acima demonstram o comportamento das unidades testadas com dados simulados; não constituem validação do sistema integrado nem avaliação de desempenho com leads reais.
