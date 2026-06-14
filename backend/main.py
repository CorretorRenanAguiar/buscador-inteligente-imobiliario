import logging
import traceback

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from chatbot_engine import processar_chatbot

# =====================================
# APP
# =====================================

app = FastAPI()

# configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")


@app.on_event("startup")
def on_startup():
    logger.info("Starting FastAPI application")

# =====================================
# CORS
# =====================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

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

def home():

    return {

        "status": "online",

        "sistema":
            "RA Inteligência Imobiliária"

    }

# =====================================
# CHAT
# =====================================

@app.post("/chat")

async def chat(request: ChatRequest):
    try:
        resposta = await processar_chatbot(request.mensagem, request.session_id)
        return resposta
    except Exception:
        logger.exception("Erro ao processar /chat")
        return JSONResponse(
            status_code=500, content={"mensagem": "Erro interno no servidor"}
        )