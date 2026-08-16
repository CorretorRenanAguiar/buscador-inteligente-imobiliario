# backup of chatbot_engine.py
# original content preserved

import requests
import re

ZAPI_INSTANCE = "3F2EFD4EDB9BB294D6392E60CA768835"
ZAPI_TOKEN = "6F1EA3F8D36CC67014A3B84B"
ZAPI_CLIENT_TOKEN = "F5de8d99a8ed846b6a50576a80f6240acS"
NUMERO_CORRETOR = "5532998148333"

sessoes = {}

PALAVRAS_PERMUTA = [
    "permuta",
    "troca",
    "aceita carro",
    "aceita veículo",
    "aceita veiculo",
    "aceita imóvel",
    "aceita imovel",
    "aceita terreno",
    "aceitar carro",
    "aceitar veículo",
    "aceitar veiculo",
    "aceitar imóvel",
    "aceitar imovel",
    "aceitar terreno",
]

LOCALIZACOES_INVALIDAS = [
    "aaa",
    "bbb",
    "ccc",
    "abc",
    "teste",
    "123",
    "piru",
    "asdf",
    "qwerty",
    "esse",
    "isso",
]


def enviar_whatsapp(relatorio):
    try:
        url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
        headers = {"Client-Token": ZAPI_CLIENT_TOKEN}
        payload = {"phone": NUMERO_CORRETOR, "message": relatorio}

        requests.post(
            url,
            json=payload,
            headers=headers,
        )
    except Exception as erro:
        print("Erro Z-API:", erro)


def detectar_permuta(texto):
    texto = texto.lower()

    for palavra in PALAVRAS_PERMUTA:
        if palavra in texto:
            return True

    return False


def validar_localizacao(texto):
    texto = texto.strip().lower()

    if len(texto) < 3:
        return False

    if texto in LOCALIZACOES_INVALIDAS:
        return False

    return True


def calcular_score(dados):
    score = 0

    objetivo = dados.get("objetivo", "").lower()
    faixa = dados.get("faixa_valor", "").lower()
    tipo = dados.get("tipo_imovel", "").lower()
    whatsapp = dados.get("whatsapp", "")

    if "invest" in objetivo:
        score += 5

    if "1 milhão" in faixa:
        score += 5
    elif "500 mil" in faixa:
        score += 3

    if "alugar" in objetivo:
        score += 2

    if dados.get("mobiliado") == "Mobiliado":
        score += 2

    if len(whatsapp) >= 10:
        score += 2

    if tipo == "imóvel comercial":
        score += 3

    if tipo in [
        "fazenda",
        "granja",
        "chácara",
        "chacara",
        "sítio",
        "sitio",
    ]:
        score += 3

    if dados.get("permuta"):
        score += 5

    return score


def classificar_perfil(dados):
    tipo = dados.get("tipo_imovel", "").lower()
    objetivo = dados.get("objetivo", "").lower()

    if tipo in [
        "fazenda",
        "granja",
        "chácara",
        "chacara",
        "sítio",
        "sitio",
    ]:
        return "Rural"

    if "alugar" in objetivo:
        return "Locação"

    if "invest" in objetivo:
        return "Investidor"

    if tipo == "lançamento":
        return "Lançamento"

    return "Residencial"


async def processar_chatbot(mensagem, session_id):
    mensagem = mensagem.strip()

    if session_id not in sessoes:
        sessoes[session_id] = {"etapa": "objetivo"}
        return {
            "mensagem": (
                "Olá 👋\n\n"
                "Sou a assistente virtual imobiliária de Renan Aguiar.\n\n"
                "Vou entender rapidamente o perfil do imóvel que você procura 😊\n\n"
                "Qual é o seu objetivo?"
            ),
            "opcoes": [
                "Comprar imóvel",
                "Alugar imóvel",
                "Investir",
                "Sou corretor",
            ],
        }

    sessao = sessoes[session_id]
    etapa = sessao["etapa"]

    if detectar_permuta(mensagem):
        sessao["permuta"] = True
        sessao["etapa"] = "whatsapp_permuta"
        return {
            "mensagem": (
                "Entendi 😊\n\n"
                "Casos de permuta exigem análise personalizada.\n\n"
                "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato."
            ),
            "opcoes": [],
        }

    if etapa == "objetivo":
        sessao["objetivo"] = mensagem
        sessao["etapa"] = "tipo_imovel"

        if "alugar" in mensagem.lower():
            return {
                "mensagem": "Perfeito 👍\n\nQual tipo de imóvel você procura?",
                "opcoes": [
                    "Casa",
                    "Apartamento",
                    "Kitnet",
                    "Cobertura",
                    "Terreno",
                    "Imóvel comercial",
                ],
            }

        return {
            "mensagem": "Perfeito 👍\n\nQual tipo de imóvel você procura?",
            "opcoes": [
                "Casa",
                "Apartamento",
                "Kitnet",
                "Cobertura",
                "Granja",
                "Chácara",
                "Sítio",
                "Fazenda",
                "Terreno",
                "Lançamento",
                "Imóvel comercial",
            ],
        }

    return {"mensagem": "Desculpe, não consegui entender.\n\nTente novamente 😊"}
