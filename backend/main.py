from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
# ROTA RAIZ
# =========================================

@app.get("/")
def home():

    return {
        "status": "online",
        "sistema": "RA Corretor de Imóveis"
    }


# =========================================
# IMPORT CHATBOT
# =========================================

try:

    from chatbot_engine import processar_chatbot

except Exception as erro:

    print(
        "ERRO CHATBOT:",
        erro
    )

    processar_chatbot = None


# =========================================
# REQUEST MODEL
# =========================================

class ChatRequest(BaseModel):

    mensagem: str

    session_id: str


# =========================================
# CHATBOT
# =========================================

@app.post("/chat")
async def chat(dados: ChatRequest):

    # =====================================
    # CHATBOT NÃO CARREGOU
    # =====================================

    if processar_chatbot is None:

        return {

            "resposta":

                "⚠️ O sistema inteligente "

                "não conseguiu iniciar.",

            "classificacao":
                "erro",

            "score":
                0

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


    except Exception as erro:

        print(
            "ERRO CHAT:",
            erro
        )

        return {

            "resposta":

                "⚠️ Ocorreu um erro "

                "ao processar sua solicitação.",

            "classificacao":
                "erro",

            "score":
                0

        }