import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from chatbot_engine import processar_chatbot

app = FastAPI(
    title="RA Inteligência Imobiliária",
    version="1.0.0",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")


@app.on_event("startup")
def on_startup():
    logger.info("Starting FastAPI application")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    mensagem: str
    session_id: str
    tenant_id: str = "RA_IMOBILIARIA"


@app.get("/")
def home():
    return {
        "status": "online",
        "sistema": "RA Inteligência Imobiliária",
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        resposta = await processar_chatbot(
            request.mensagem,
            request.session_id,
            request.tenant_id,
        )
        return resposta
    except Exception:
        logger.exception("Erro ao processar /chat")
        return JSONResponse(
            status_code=500,
            content={"mensagem": "Erro interno no servidor"},
            media_type="application/json; charset=utf-8",
        )


@app.post("/webhook/evolution")
async def webhook_evolution(payload: Dict[str, Any]):
    try:
        event_name = str(payload.get("event") or payload.get("type") or "").strip()
        if event_name.upper() not in {"MESSAGES.UPSERT", "MESSAGES_UPSERT"}:
            return {"status": "ignorado", "evento": event_name}

        data = payload.get("data") or payload
        messages = data.get("messages") or []
        if not messages:
            return {"status": "ignorado", "motivo": "sem mensagens"}

        mensagem = messages[0]
        texto = ""
        if isinstance(mensagem, dict):
            texto = mensagem.get("conversation") or mensagem.get("text") or ""
            if isinstance(texto, dict):
                texto = texto.get("body") or ""
            if not texto:
                for item in (
                    mensagem.get("extendedTextMessage"),
                    mensagem.get("message"),
                ):
                    if isinstance(item, dict):
                        texto = item.get("text") or item.get("conversation") or ""
                        break

        remetente = ""
        if isinstance(mensagem, dict):
            key = mensagem.get("key") or {}
            remetente = str(key.get("remoteJid") or key.get("from") or "")
            if not remetente:
                remetente = str(mensagem.get("from") or mensagem.get("remoteJid") or "")

        if not texto or not remetente:
            return {"status": "ignorado", "motivo": "mensagem incompleta"}

        session_id = remetente.replace("@s.whatsapp.net", "").replace("@g.us", "")
        resposta = await processar_chatbot(str(texto), session_id, "RA_IMOBILIARIA")
        return {"status": "ok", "resposta": resposta}
    except Exception:
        logger.exception("Erro ao processar webhook Evolution")
        return JSONResponse(
            status_code=500,
            content={"status": "erro", "mensagem": "Falha ao processar webhook"},
            media_type="application/json; charset=utf-8",
        )
