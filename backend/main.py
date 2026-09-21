import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.chatbot_engine import processar_chatbot

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
        return JSONResponse(
            content=resposta,
            media_type="application/json; charset=utf-8",
        )
    except Exception:
        logger.exception("Erro ao processar /chat")
        return JSONResponse(
            status_code=500,
            content={"mensagem": "Erro interno no servidor"},
            media_type="application/json; charset=utf-8",
        )


@app.get("/diagnostico/evolution")
def diagnostico_evolution():
    import os
    import requests

    url = (os.getenv("EVOLUTION_API_URL") or "").rstrip("/")
    key = os.getenv("EVOLUTION_API_KEY") or ""
    instance = os.getenv("EVOLUTION_INSTANCE_RA_IMOBILIARIA") or ""
    numero = os.getenv("NUMERO_CORRETOR_RA_IMOBILIARIA") or ""
    tenant = os.getenv("DEFAULT_TENANT_ID") or ""

    resultado = {
        "url_host": (url.split("//", 1)[-1].split("/", 1)[0] if url else None),
        "api_key_configurada": bool(key),
        "api_key_tamanho": len(key),
        "instance": instance,
        "numero_configurado": bool(numero),
        "tenant": tenant,
        "url_sendtext": (
            f"{url}/message/sendText/{instance}" if url and instance else None
        ),
    }

    if not url:
        resultado["erro"] = "EVOLUTION_API_URL não configurada."
        return resultado

    if not key:
        resultado["erro"] = "EVOLUTION_API_KEY não configurada."
        return resultado

    if not instance:
        resultado["erro"] = "EVOLUTION_INSTANCE_RA_IMOBILIARIA não configurada."
        return resultado

    try:
        response = requests.get(
            f"{url}/instance/connectionState/{instance}",
            headers={
                "apikey": key,
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        resultado["http_status"] = response.status_code

        try:
            dados = response.json()
            resultado["state"] = dados.get("instance", {}).get("state")
        except ValueError:
            resultado["resposta"] = response.text[:300]

    except requests.exceptions.Timeout:
        resultado["erro_tipo"] = "Timeout"

    except requests.exceptions.RequestException as erro:
        resultado["erro_tipo"] = type(erro).__name__
        resultado["erro"] = str(erro)[:300]

    except Exception as erro:
        resultado["erro_tipo"] = type(erro).__name__
        resultado["erro"] = str(erro)[:300]

    return resultado


@app.post("/webhook/evolution")
async def webhook_evolution(payload: Dict[str, Any]):
    try:
        event_name = str(payload.get("event") or payload.get("type") or "").strip()

        if event_name.upper() not in {
            "MESSAGES.UPSERT",
            "MESSAGES_UPSERT",
        }:
            return {
                "status": "ignorado",
                "evento": event_name,
            }

        data = payload.get("data") or payload
        messages = data.get("messages") or []

        if not messages:
            return {
                "status": "ignorado",
                "motivo": "sem mensagens",
            }

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
            return {
                "status": "ignorado",
                "motivo": "mensagem incompleta",
            }

        session_id = remetente.replace("@s.whatsapp.net", "").replace("@g.us", "")

        resposta = await processar_chatbot(
            str(texto),
            session_id,
            "RA_IMOBILIARIA",
        )

        return {
            "status": "ok",
            "resposta": resposta,
        }

    except Exception:
        logger.exception("Erro ao processar webhook Evolution")

        return JSONResponse(
            status_code=500,
            content={
                "status": "erro",
                "mensagem": "Falha ao processar webhook",
            },
            media_type="application/json; charset=utf-8",
        )
