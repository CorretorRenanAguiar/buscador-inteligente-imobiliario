from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chatbot_engine import processar_chatbot

app = FastAPI()



# =========================================
# CORS
# =========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)



# =========================================
# MODELO REQUEST
# =========================================

class ChatRequest(BaseModel):

    mensagem: str

    session_id: str



# =========================================
# ROTA PRINCIPAL
# =========================================

@app.get("/")

def home():

    return {

        "status": "online",

        "sistema":
            "RA Corretor de Imóveis"

    }



# =========================================
# CHAT IA
# =========================================

@app.post("/chat")

async def chat(data: ChatRequest):

    resposta = await processar_chatbot(

        data.mensagem,

        data.session_id

    )

    return resposta