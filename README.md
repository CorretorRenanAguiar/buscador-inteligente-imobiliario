# buscador-inteligente-imobiliario

Plataforma web de recomendação e segmentação de leads imobiliários com chatbot, IA e Supabase.

## Evolution API 2.3.7

O backend envia os relatórios do chatbot pela Evolution API 2.3.7, usando uma única instância: `RA_IMOBILIARIA`. A camada de integração está em `backend/evolution_api.py` e usa `/message/sendText/{instance}`.

### Configuração local

1. Copie `backend/.env.example` para `backend/.env` e preencha as variáveis do Supabase e da Evolution. Não versionar esse arquivo.
2. Copie `evolution/.env.example` para `evolution/.env` e defina uma senha de PostgreSQL e uma chave de API fortes.
3. Inicie a máquina Podman:

```powershell
podman machine start
podman machine list
```

4. Inicie PostgreSQL, Redis e Evolution API:

```powershell
cd evolution
podman compose up -d
podman ps
```

A API local fica disponível em `http://localhost:8080`. A chave usada no header `apikey` é `AUTHENTICATION_API_KEY`, e deve ser igual a `EVOLUTION_API_KEY` no backend.

### Criar e conectar a instância

Com a Evolution API em execução, crie a instância usando a chave configurada:

```powershell
curl.exe -X POST http://localhost:8080/instance/create `
	-H "apikey: SUA_AUTHENTICATION_API_KEY" `
	-H "Content-Type: application/json" `
	-d "{\"instanceName\":\"RA_IMOBILIARIA\",\"integration\":\"WHATSAPP-BAILEYS\"}"
```

Consulte o QR Code pelos endpoints da Evolution e conecte o único número do corretor. O projeto não cria múltiplos tenants.

### Backend e testes

Execute o backend a partir da pasta `backend`:

```powershell
python -m uvicorn main:app --reload
```

Os testes da integração não usam WhatsApp real:

```powershell
python -m unittest backend.test_evolution -v
```

### Produção no Railway

No Railway, configure `EVOLUTION_API_URL` com uma URL pública da Evolution API. Não use `localhost` em produção. Configure também `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_RA_IMOBILIARIA` e `NUMERO_CORRETOR_RA_IMOBILIARIA` como variáveis privadas do serviço. A Evolution API, PostgreSQL e Redis continuam sendo serviços separados do backend Railway.
