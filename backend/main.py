from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import traceback

# =========================================
# FASTAPI
# =========================================

app = FastAPI()

# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# IMPORT CHATBOT
# =========================================

CHATBOT_ERRO = None

try:

    from chatbot_engine import processar_chatbot

except Exception as erro:

    CHATBOT_ERRO = str(erro)

    print("\n===================================")
    print("ERRO AO IMPORTAR CHATBOT_ENGINE")
    print("===================================")

    traceback.print_exc()

    print("===================================\n")

    processar_chatbot = None


# =========================================
# REQUEST MODEL
# =========================================

class ChatRequest(BaseModel):

    mensagem: str

    session_id: str


# =========================================
# HOME
# =========================================

@app.get("/")
def home():

    return {

        "status": "online",

        "sistema": "RA Corretor de Imóveis",

        "chatbot_carregado":

            processar_chatbot is not None,

        "erro_chatbot":

            CHATBOT_ERRO

    }


# =========================================
# CHAT
# =========================================

@app.post("/chat")
async def chat(dados: ChatRequest):

    # =====================================
    # CHATBOT NÃO CARREGOU
    # =====================================

    if processar_chatbot is None:

        return {

            "resposta":

                "⚠️ O chatbot não conseguiu "

                "ser iniciado.",

            "erro":

                CHATBOT_ERRO,

            "score":
                0,

            "classificacao":
                "erro"

        }

    # =====================================
    # PROCESSAR
    # =====================================

    try:

        resposta = await processar_chatbot(

            dados.mensagem,

            dados.session_id

        )

        return resposta

    except Exception:

        traceback.print_exc()

        return {

            "resposta":

                "⚠️ Erro interno no chatbot.",

            "score":
                0,

            "classificacao":
                "erro"

        }