import logging
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from backend.chatbot_engine import processar_chatbot

# =====================================
# APP
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("backend.main")

app = FastAPI()


@app.on_event("startup")
def on_startup():
    logger.info("Starting FastAPI application")


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start_time = time.perf_counter()
    logger.info("Recebendo %s %s", request.method, request.url.path)
    logger.info("Headers: %s", dict(request.headers))
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        "Finalizando %s %s -> %s (%d ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"mensagem": "Erro interno no servidor"},
    )


# =====================================
# CORS
# =====================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://buscador-inteligente-imobiliario.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# =====================================
# MODELO
# =====================================


class ChatRequest(BaseModel):
    mensagem: str
    session_id: str


# =====================================
# HOME
# =====================================


@app.get("/")
async def home():
    return {"status": "online", "sistema": "RA Inteligência Imobiliária"}


# =====================================
# TESTE
# =====================================


@app.get("/teste")
async def teste():
    logger.info("GET /teste executado")
    return {"status": "ok", "versao": "deploy atual", "backend": True}


# =====================================
# CHAT
# =====================================


@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info("Recebendo POST /chat")
    resposta = await processar_chatbot(request.mensagem, request.session_id)
    logger.info("Finalizando POST /chat")
    return resposta


@app.options("/chat", include_in_schema=False)
async def chat_options(request: Request):
    logger.info("Recebendo OPTIONS /chat")
    return Response(status_code=200)
