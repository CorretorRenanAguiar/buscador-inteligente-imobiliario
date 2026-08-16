import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from chatbot_engine import processar_chatbot

app = FastAPI()

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


@app.get("/")
def home():
    return {
        "status": "online",
        "sistema": "RA Inteligência Imobiliária",
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        resposta = await processar_chatbot(request.mensagem, request.session_id)
        return resposta
    except Exception:
        logger.exception("Erro ao processar /chat")
        return JSONResponse(
            status_code=500,
            content={"mensagem": "Erro interno no servidor"},
        )
