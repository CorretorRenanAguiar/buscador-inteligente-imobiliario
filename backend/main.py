from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from chatbot_engine import processar_chatbot

# =====================================
# APP
# =====================================

app = FastAPI()

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

    resposta = await processar_chatbot(

        request.mensagem,

        request.session_id

    )

    return resposta