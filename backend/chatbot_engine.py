# ============================================
# chatbot_engine.py
# ============================================

import os
import re
import requests

from dotenv import load_dotenv

# ============================================
# CARREGAR VARIÁVEIS .ENV
# ============================================

load_dotenv()

# ============================================
# VARIÁVEIS AMBIENTE
# ============================================

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
NUMERO_CORRETOR = os.getenv("NUMERO_CORRETOR")

# ============================================
# SESSÕES
# ============================================

sessoes = {}

# ============================================
# PALAVRAS RELACIONADAS A PERMUTA
# ============================================

PALAVRAS_PERMUTA = [

    "permuta",
    "troca",
    "aceita carro",
    "aceita veículo",
    "aceita veiculo",
    "aceita imóvel",
    "aceita imovel",
    "aceita terreno",
    "aceita lote",
    "aceita casa",
    "aceita apartamento",
    "aceitar carro",
    "aceitar veículo",
    "aceitar veiculo",
    "aceitar imóvel",
    "aceitar imovel"

]

# ============================================
# ENTRADAS INVÁLIDAS
# ============================================

LOCALIZACOES_INVALIDAS = [

    "aaa",
    "bbb",
    "ccc",
    "abc",
    "123",
    "teste",
    "asdf",
    "qwerty",
    "isso",
    "esse",
    "xxx",
    "nada"

]

# ============================================
# VALIDAR LOCALIZAÇÃO
# ============================================

def validar_localizacao(texto):

    texto = texto.strip().lower()

    if len(texto) < 3:

        return False

    if texto in LOCALIZACOES_INVALIDAS:

        return False

    return True

# ============================================
# DETECTAR PERMUTA
# ============================================

def detectar_permuta(texto):

    texto = texto.lower()

    for palavra in PALAVRAS_PERMUTA:

        if palavra in texto:

            return True

    return False

# ============================================
# CALCULAR SCORE
# ============================================

def calcular_score(dados):

    score = 0

    objetivo = dados.get("objetivo", "").lower()
    faixa = dados.get("faixa_valor", "").lower()
    tipo = dados.get("tipo_imovel", "").lower()
    whatsapp = dados.get("whatsapp", "")

    # ========================================
    # INVESTIMENTO
    # ========================================

    if "invest" in objetivo:

        score += 5

    # ========================================
    # VALOR ALTO
    # ========================================

    if "1 milhão" in faixa:

        score += 5

    elif "500 mil" in faixa:

        score += 3

    # ========================================
    # LOCAÇÃO
    # ========================================

    if "alugar" in objetivo:

        score += 2

    # ========================================
    # MOBILIADO
    # ========================================

    if dados.get("mobiliado") == "Mobiliado":

        score += 2

    # ========================================
    # WHATSAPP VÁLIDO
    # ========================================

    if len(whatsapp) >= 11:

        score += 2

    # ========================================
    # COMERCIAL
    # ========================================

    if tipo == "imóvel comercial":

        score += 3

    # ========================================
    # RURAL
    # ========================================

    if tipo in [

        "fazenda",
        "granja",
        "sítio",
        "sitio",
        "chácara",
        "chacara"

    ]:

        score += 3

    # ========================================
    # PERMUTA
    # ========================================

    if dados.get("permuta"):

        score += 5

    return score

# ============================================
# CLASSIFICAR PERFIL
# ============================================

def classificar_perfil(dados):

    tipo = dados.get("tipo_imovel", "").lower()
    objetivo = dados.get("objetivo", "").lower()

    if "alugar" in objetivo:

        return "Locação"

    if "invest" in objetivo:

        return "Investidor"

    if tipo in [

        "fazenda",
        "granja",
        "sítio",
        "sitio",
        "chácara",
        "chacara"

    ]:

        return "Rural"

    if tipo == "lançamento":

        return "Lançamento"

    return "Residencial"

# ============================================
# ENVIAR WHATSAPP
# ============================================

def enviar_whatsapp(relatorio):

    try:

        url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"

        payload = {

            "phone": str(NUMERO_CORRETOR),
            "message": str(relatorio)

        }

        headers = {

            "Content-Type": "application/json"

        }

        response = requests.post(

            url,
            json=payload,
            headers=headers,
            timeout=30

        )

        print("====================================")
        print("ENVIO WHATSAPP")
        print("STATUS:", response.status_code)
        print("RESPOSTA:", response.text)
        print("====================================")

        return response.status_code == 200

    except Exception as erro:

        print("====================================")
        print("ERRO AO ENVIAR WHATSAPP")
        print(erro)
        print("====================================")

        return False

# ============================================
# PROCESSAMENTO CHATBOT
# ============================================

async def processar_chatbot(mensagem, session_id):

    mensagem = mensagem.strip()

    # ========================================
    # NOVA SESSÃO
    # ========================================

    if session_id not in sessoes:

        sessoes[session_id] = {

            "etapa": "objetivo"

        }

        return {

            "mensagem":

                "Olá 👋\n\n"
                "Sou a assistente virtual imobiliária de Renan Aguiar.\n\n"
                "Vou entender rapidamente o perfil do imóvel que você procura 😊\n\n"
                "Qual é o seu objetivo?",

            "opcoes": [

                "Comprar imóvel",
                "Alugar imóvel",
                "Investir",
                "Sou corretor"

            ]

        }

    sessao = sessoes[session_id]

    etapa = sessao["etapa"]

    # ========================================
    # DETECTAR PERMUTA
    # ========================================

    if detectar_permuta(mensagem):

        sessao["permuta"] = True

        sessao["etapa"] = "whatsapp"

        return {

            "mensagem":

                "Entendi 😊\n\n"
                "Casos de permuta exigem análise personalizada.\n\n"
                "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato.",

            "opcoes": []

        }

    # ========================================
    # OBJETIVO
    # ========================================

    if etapa == "objetivo":

        sessao["objetivo"] = mensagem

        sessao["etapa"] = "tipo_imovel"

        # ====================================
        # LOCAÇÃO
        # ====================================

        if "alugar" in mensagem.lower():

            return {

                "mensagem":

                    "Perfeito 👍\n\n"
                    "Qual tipo de imóvel você procura?",

                "opcoes": [

                    "Casa",
                    "Apartamento",
                    "Kitnet",
                    "Cobertura",
                    "Terreno",
                    "Imóvel comercial"

                ]

            }

        # ====================================
        # COMPRA / INVESTIMENTO
        # ====================================

        return {

            "mensagem":

                "Perfeito 👍\n\n"
                "Qual tipo de imóvel você procura?",

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
                "Imóvel comercial"

            ]

        }

    # ========================================
    # TIPO IMÓVEL
    # ========================================

    if etapa == "tipo_imovel":

        sessao["tipo_imovel"] = mensagem

        tipo = mensagem.lower()

        # ====================================
        # IMÓVEIS RURAIS
        # ====================================

        if tipo in [

            "granja",
            "fazenda",
            "sítio",
            "sitio",
            "chácara",
            "chacara"

        ]:

            sessao["etapa"] = "objetivo_rural"

            return {

                "mensagem":

                    "Excelente 😊\n\n"
                    "Qual o principal objetivo do imóvel rural?",

                "opcoes": [

                    "Lazer",
                    "Moradia",
                    "Produção rural",
                    "Investimento"

                ]

            }

        # ====================================
        # TERRENO
        # ====================================

        if tipo == "terreno":

            sessao["etapa"] = "objetivo_terreno"

            return {

                "mensagem":

                    "Perfeito 👍\n\n"
                    "Qual a finalidade do terreno?",

                "opcoes": [

                    "Construir para morar",
                    "Investimento",
                    "Construção comercial"

                ]

            }

        # ====================================
        # IMÓVEIS URBANOS
        # ====================================

        sessao["etapa"] = "quartos"

        return {

            "mensagem":

                "Entendi 👍\n\n"
                "Quantos quartos você deseja?",

            "opcoes": [

                "1 quarto",
                "2 quartos",
                "3 quartos",
                "4 quartos ou mais"

            ]

        }

    # ========================================
    # OBJETIVO RURAL
    # ========================================

    if etapa == "objetivo_rural":

        sessao["objetivo_rural"] = mensagem

        sessao["etapa"] = "hectares"

        return {

            "mensagem":

                "Ótimo 👍\n\n"
                "Qual tamanho aproximado procura?",

            "opcoes": [

                "Até 1 hectare",
                "1 a 5 hectares",
                "5 a 20 hectares",
                "Acima de 20 hectares"

            ]

        }

    # ========================================
    # HECTARES
    # ========================================

    if etapa == "hectares":

        sessao["hectares"] = mensagem

        sessao["etapa"] = "localizacao"

        return {

            "mensagem":

                "Perfeito 😊\n\n"
                "Qual localização deseja para o imóvel?",

            "opcoes": []

        }

    # ========================================
    # OBJETIVO TERRENO
    # ========================================

    if etapa == "objetivo_terreno":

        sessao["objetivo_terreno"] = mensagem

        sessao["etapa"] = "localizacao"

        return {

            "mensagem":

                "Excelente 👍\n\n"
                "Qual localização deseja para o terreno?",

            "opcoes": []

        }

    # ========================================
    # QUARTOS
    # ========================================

    if etapa == "quartos":

        sessao["quartos"] = mensagem

        # ====================================
        # LOCAÇÃO
        # ====================================

        if "alugar" in sessao["objetivo"].lower():

            sessao["etapa"] = "mobiliado"

            return {

                "mensagem":

                    "Perfeito 👍\n\n"
                    "Você procura imóvel:",

                "opcoes": [

                    "Mobiliado",
                    "Semimobiliado",
                    "Não importa"

                ]

            }

        sessao["etapa"] = "localizacao"

        return {

            "mensagem":

                "Perfeito 👍\n\n"
                "Qual localização deseja para o imóvel?",

            "opcoes": []

        }

    # ========================================
    # MOBILIADO
    # ========================================

    if etapa == "mobiliado":

        sessao["mobiliado"] = mensagem

        sessao["etapa"] = "localizacao"

        return {

            "mensagem":

                "Excelente 😊\n\n"
                "Qual localização deseja para o imóvel?",

            "opcoes": []

        }

    # ========================================
    # LOCALIZAÇÃO
    # ========================================

    if etapa == "localizacao":

        if not validar_localizacao(mensagem):

            return {

                "mensagem":

                    "Não consegui identificar a localização 😊\n\n"
                    "Pode informar cidade, bairro, região ou referência desejada?",

                "opcoes": []

            }

        sessao["localizacao"] = mensagem

        sessao["etapa"] = "faixa_valor"

        # ====================================
        # LOCAÇÃO
        # ====================================

        if "alugar" in sessao["objetivo"].lower():

            return {

                "mensagem":

                    "Ótimo 😊\n\n"
                    "Qual faixa de aluguel você procura?",

                "opcoes": [

                    "Até R$ 800",
                    "R$ 800 a R$ 1.500",
                    "R$ 1.500 a R$ 3.000",
                    "R$ 3.000 a R$ 5.000",
                    "Acima de R$ 5.000"

                ]

            }

        # ====================================
        # COMPRA
        # ====================================

        return {

            "mensagem":

                "Excelente 😊\n\n"
                "Qual faixa de valor você procura?",

            "opcoes": [

                "Até R$ 150 mil",
                "R$ 150 mil a R$ 300 mil",
                "R$ 300 mil a R$ 500 mil",
                "R$ 500 mil a R$ 1 milhão",
                "Acima de R$ 1 milhão"

            ]

        }

    # ========================================
    # FAIXA VALOR
    # ========================================

    if etapa == "faixa_valor":

        sessao["faixa_valor"] = mensagem

        sessao["etapa"] = "whatsapp"

        return {

            "mensagem":

                "Perfeito 😊\n\n"
                "Informe seu WhatsApp com DDD para que um corretor entre em contato.",

            "opcoes": []

        }

    # ========================================
    # WHATSAPP
    # ========================================

    if etapa == "whatsapp":

        whatsapp = re.sub(r"\D", "", mensagem)

        sessao["whatsapp"] = whatsapp

        perfil = classificar_perfil(sessao)

        score = calcular_score(sessao)

        relatorio = f"""

🚨 NOVO LEAD IMOBILIÁRIO

👤 Perfil:
{perfil}

🎯 Objetivo:
{sessao.get("objetivo")}

🏠 Tipo imóvel:
{sessao.get("tipo_imovel")}

🛏️ Quartos:
{sessao.get("quartos", "Não informado")}

🛋️ Mobiliado:
{sessao.get("mobiliado", "Não informado")}

🌱 Objetivo rural:
{sessao.get("objetivo_rural", "Não informado")}

📏 Área/Hectares:
{sessao.get("hectares", "Não informado")}

📍 Localização:
{sessao.get("localizacao")}

💰 Faixa valor:
{sessao.get("faixa_valor")}

🔁 Permuta:
{"Sim" if sessao.get("permuta") else "Não"}

📱 WhatsApp cliente:
{whatsapp}

🔥 Score Lead:
{score}
"""

        enviado = enviar_whatsapp(relatorio)

        del sessoes[session_id]

        if enviado:

            return {

                "mensagem":

                    "✅ Atendimento concluído com sucesso!\n\n"
                    "Nossa equipe já recebeu suas informações.\n\n"
                    "Em breve um corretor entrará em contato 😊",

                "link_whatsapp":

                    f"https://wa.me/{NUMERO_CORRETOR}"

            }

        return {

            "mensagem":

                "⚠️ O atendimento foi concluído, porém ocorreu uma falha no envio automático.\n\n"
                "Por favor, clique no botão abaixo para falar diretamente com o corretor.",

            "link_whatsapp":

                f"https://wa.me/{NUMERO_CORRETOR}"

        }

    # ========================================
    # FALLBACK
    # ========================================

    return {

        "mensagem":

            "Desculpe, não consegui entender.\n\n"
            "Tente novamente 😊"

    }