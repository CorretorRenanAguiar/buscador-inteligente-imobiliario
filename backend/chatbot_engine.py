# ============================================
# chatbot_engine.py
# ============================================

import requests
import re

# ============================================
# CONFIGURAÇÕES Z-API
# ============================================

ZAPI_INSTANCE = "3F2EFD4EDB9BB294D6392E60CA768835"

ZAPI_TOKEN = "6F1EA3F8D36CC67014A3B84B"

ZAPI_CLIENT_TOKEN = "F5de8d99a8ed846b6a50576a80f6240acS"

NUMERO_CORRETOR = "5532998148333"

# ============================================
# SESSÕES
# ============================================

sessoes = {}

# ============================================
# PALAVRAS DE PERMUTA
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
    "aceitar carro",
    "aceitar veículo",
    "aceitar veiculo",
    "aceitar imóvel",
    "aceitar imovel",
    "aceitar terreno"

]

# ============================================
# ENVIAR WHATSAPP
# ============================================

def enviar_whatsapp(relatorio):

    try:

        url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"

        headers = {

            "Client-Token": ZAPI_CLIENT_TOKEN

        }

        payload = {

            "phone": NUMERO_CORRETOR,
            "message": relatorio

        }

        requests.post(

            url,
            json=payload,
            headers=headers

        )

    except Exception as erro:

        print("Erro Z-API:", erro)

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

    if "invest" in objetivo:

        score += 4

    if "1 milhão" in faixa:

        score += 5

    if "500 mil" in faixa:

        score += 3

    if dados.get("permuta"):

        score += 5

    if tipo in [

        "fazenda",
        "chácara",
        "chacara",
        "granja"

    ]:

        score += 3

    return score

# ============================================
# CLASSIFICAÇÃO DE PERFIL
# ============================================

def classificar_perfil(dados):

    tipo = dados.get("tipo_imovel", "").lower()

    objetivo = dados.get("objetivo", "").lower()

    if tipo in [

        "fazenda",
        "sítio",
        "sitio",
        "granja",
        "chácara",
        "chacara"

    ]:

        return "Rural"

    if "invest" in objetivo:

        return "Investidor"

    if tipo == "lançamento":

        return "Lançamento"

    return "Residencial"

# ============================================
# PROCESSAMENTO PRINCIPAL
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

                "Comprar",
                "Alugar",
                "Investir",
                "Sou corretor/parceiro"

            ]

        }

    sessao = sessoes[session_id]

    etapa = sessao["etapa"]

    # ========================================
    # DETECTAR PERMUTA
    # ========================================

    if detectar_permuta(mensagem):

        sessao["permuta"] = True

        sessao["etapa"] = "whatsapp_permuta"

        return {

            "mensagem":

                "Entendi 😊\n\n"
                "Casos de permuta exigem uma análise personalizada.\n\n"
                "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato.",

            "opcoes": []

        }

    # ========================================
    # OBJETIVO
    # ========================================

    if etapa == "objetivo":

        sessao["objetivo"] = mensagem

        sessao["etapa"] = "tipo_imovel"

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
        # RURAL
        # ====================================

        if tipo in [

            "granja",
            "chácara",
            "chacara",
            "fazenda",
            "sítio",
            "sitio"

        ]:

            sessao["etapa"] = "objetivo_rural"

            return {

                "mensagem":

                    "Excelente 😊\n\n"
                    "Qual o objetivo principal do imóvel?",

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
        # URBANO
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

        sessao["etapa"] = "regiao"

        return {

            "mensagem":

                "Perfeito 😊\n\n"
                "Em qual cidade, bairro ou região deseja o imóvel?",

            "opcoes": []

        }

    # ========================================
    # OBJETIVO TERRENO
    # ========================================

    if etapa == "objetivo_terreno":

        sessao["objetivo_terreno"] = mensagem

        sessao["etapa"] = "regiao"

        return {

            "mensagem":

                "Excelente 👍\n\n"
                "Em qual bairro ou região deseja o terreno?",

            "opcoes": []

        }

    # ========================================
    # QUARTOS
    # ========================================

    if etapa == "quartos":

        sessao["quartos"] = mensagem

        sessao["etapa"] = "regiao"

        return {

            "mensagem":

                "Perfeito 👍\n\n"
                "Em qual bairro ou região você gostaria de encontrar o imóvel?",

            "opcoes": []

        }

    # ========================================
    # REGIÃO
    # ========================================

    if etapa == "regiao":

        sessao["regiao"] = mensagem

        sessao["etapa"] = "faixa_valor"

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

                "Ótimo 😊\n\n"
                "Para que um corretor entre em contato com você, informe seu WhatsApp com DDD.",

            "opcoes": []

        }

    # ========================================
    # WHATSAPP
    # ========================================

    if etapa in [

        "whatsapp",
        "whatsapp_permuta"

    ]:

        whatsapp = re.sub(r"\D", "", mensagem)

        sessao["whatsapp"] = whatsapp

        perfil = classificar_perfil(sessao)

        score = calcular_score(sessao)

        relatorio = f"""

🚨 NOVO LEAD IMOBILIÁRIO

👤 Perfil:
{perfil}

🎯 Objetivo:
{sessao.get('objetivo')}

🏠 Tipo imóvel:
{sessao.get('tipo_imovel')}

🛏 Quartos:
{sessao.get('quartos', 'Não informado')}

🌱 Objetivo rural:
{sessao.get('objetivo_rural', 'Não informado')}

📏 Área/Hectares:
{sessao.get('hectares', 'Não informado')}

📍 Região:
{sessao.get('regiao')}

💰 Faixa valor:
{sessao.get('faixa_valor')}

🔁 Permuta:
{'Sim' if sessao.get('permuta') else 'Não'}

📱 WhatsApp cliente:
{whatsapp}

🔥 Score Lead:
{score}
"""

        enviar_whatsapp(relatorio)

        del sessoes[session_id]

        return {

            "mensagem":

                "✅ Atendimento concluído com sucesso!\n\n"
                "Nossa equipe já recebeu suas informações.\n\n"
                "Em breve um corretor entrará em contato 😊",

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