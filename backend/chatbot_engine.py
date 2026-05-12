import requests

# =========================================
# SESSÕES
# =========================================

sessoes = {}

# =========================================
# CONFIG Z-API
# =========================================

ZAPI_URL = "https://api.z-api.io/instances/3F2EFD4EDB9BB294D6392E60CA768835/token/6F1EA3F8D36CC67014A3B84B/send-text"

CLIENT_TOKEN = "F5de8d99a8ed846b6a50576a80f6240acS"

SEU_NUMERO = "5532998148333"

# =========================================
# ENVIO AUTOMÁTICO WHATSAPP
# =========================================

def enviar_whatsapp(relatorio):

    headers = {
        "Client-Token": CLIENT_TOKEN
    }

    payload = {
        "phone": SEU_NUMERO,
        "message": relatorio
    }

    try:

        response = requests.post(
            ZAPI_URL,
            json=payload,
            headers=headers
        )

        print(response.text)

    except Exception as erro:

        print(str(erro))

# =========================================
# CHATBOT
# =========================================

async def processar_chatbot(mensagem, session_id):

    if session_id not in sessoes:

        sessoes[session_id] = {
            "etapa": 0,
            "dados": {}
        }

    sessao = sessoes[session_id]

    etapa = sessao["etapa"]

    # =====================================
    # ETAPA 0
    # =====================================

    if etapa == 0:

        sessao["etapa"] = 1

        return {

            "mensagem": (
                "Olá 👋\n\n"
                "Sou a assistente virtual imobiliária de Renan Aguiar.\n\n"
                "Vou fazer algumas perguntas rápidas para entender o imóvel ideal para você 😊\n\n"
                "Qual é o seu objetivo?"
            ),

            "opcoes": [

                "Comprar imóvel",

                "Alugar imóvel",

                "Investir",

                "Sou corretor"

            ]

        }

    # =====================================
    # ETAPA 1
    # =====================================

    elif etapa == 1:

        sessao["dados"]["objetivo"] = mensagem

        sessao["etapa"] = 2

        return {

            "mensagem":
                (
                    "Perfeito 👍\n\n"
                    "Qual tipo de imóvel você procura?"
                ),

            "opcoes": [

                "Casa",

                "Apartamento",

                "Kitnet",

                "Cobertura",

                "Granja",

                "Chácara",

                "Fazenda",

                "Terreno",

                "Lançamento",

                "Imóvel comercial"

            ]

        }

    # =====================================
    # ETAPA 2
    # =====================================

    elif etapa == 2:

        sessao["dados"]["tipo_imovel"] = mensagem

        # =================================
        # TERRENO
        # =================================

        if mensagem == "Terreno":

            sessao["etapa"] = 20

            return {

                "mensagem":
                    (
                        "Excelente escolha 👍\n\n"
                        "Qual metragem aproximada você procura?"
                    ),

                "opcoes": [

                    "Até 250 m²",

                    "250 m² a 500 m²",

                    "500 m² a 1000 m²",

                    "Acima de 1000 m²"

                ]

            }

        # =================================
        # GRANJA / CHÁCARA / FAZENDA
        # =================================

        elif mensagem in [

            "Granja",

            "Chácara",

            "Fazenda"

        ]:

            sessao["etapa"] = 21

            return {

                "mensagem":
                    (
                        "Excelente 😊\n\n"
                        "Qual será o principal objetivo do imóvel?"
                    ),

                "opcoes": [

                    "Lazer",

                    "Moradia",

                    "Investimento",

                    "Produção rural"

                ]

            }

        # =================================
        # DEMAIS IMÓVEIS
        # =================================

        else:

            sessao["etapa"] = 3

            return {

                "mensagem":
                    (
                        "Entendi 👍\n\n"
                        "Quantos quartos você deseja?"
                    ),

                "opcoes": [

                    "1 quarto",

                    "2 quartos",

                    "3 quartos",

                    "4 quartos ou mais"

                ]

            }

    # =====================================
    # ETAPA TERRENO
    # =====================================

    elif etapa == 20:

        sessao["dados"]["metragem"] = mensagem

        sessao["etapa"] = 4

        return {

            "mensagem":
                (
                    "Perfeito 👍\n\n"
                    "Em qual bairro ou região você gostaria de encontrar o imóvel?"
                )

        }

    # =====================================
    # ETAPA GRANJA / CHÁCARA / FAZENDA
    # =====================================

    elif etapa == 21:

        sessao["dados"]["finalidade"] = mensagem

        sessao["etapa"] = 3

        return {

            "mensagem":
                (
                    "Ótimo 😊\n\n"
                    "Quantos quartos você deseja?"
                ),

            "opcoes": [

                "1 quarto",

                "2 quartos",

                "3 quartos",

                "4 quartos ou mais"

            ]

        }

    # =====================================
    # ETAPA 3
    # =====================================

    elif etapa == 3:

        sessao["dados"]["quartos"] = mensagem

        sessao["etapa"] = 4

        return {

            "mensagem":
                (
                    "Perfeito 👍\n\n"
                    "Em qual bairro ou região você gostaria de encontrar o imóvel?"
                )

        }

    # =====================================
    # ETAPA 4
    # =====================================

    elif etapa == 4:

        sessao["dados"]["bairro"] = mensagem

        sessao["etapa"] = 5

        return {

            "mensagem":
                (
                    "Excelente 😊\n\n"
                    "Qual faixa de valor você procura?"
                ),

            "opcoes": [

                "Até R$ 150 mil",

                "R$ 150 mil a R$ 300 mil",

                "R$ 300 mil a R$ 500 mil",

                "R$ 500 mil a R$ 1 milhão",

                "Acima de R$ 1 milhão"

            ]

        }

    # =====================================
    # ETAPA 5
    # =====================================

    elif etapa == 5:

        sessao["dados"]["faixa_valor"] = mensagem

        sessao["etapa"] = 6

        return {

            "mensagem":
                (
                    "Ótimo 😊\n\n"
                    "Para que um corretor entre em contato com você, informe seu WhatsApp com DDD."
                )

        }

    # =====================================
    # ETAPA FINAL
    # =====================================

    elif etapa == 6:

        sessao["dados"]["telefone"] = mensagem

        dados = sessao["dados"]

        # =================================
        # SCORE
        # =================================

        score = 0

        if "Comprar" in dados["objetivo"]:
            score += 50

        if dados["tipo_imovel"] in [
            "Casa",
            "Apartamento",
            "Cobertura",
            "Lançamento"
        ]:
            score += 40

        if "Acima" in dados["faixa_valor"]:
            score += 30

        score += 20

        # =================================
        # CLASSIFICAÇÃO
        # =================================

        if score >= 100:

            classificacao = "🔥 Lead Quente"

        elif score >= 70:

            classificacao = "🟡 Lead Morno"

        else:

            classificacao = "🔵 Lead Frio"

        # =================================
        # RELATÓRIO
        # =================================

        relatorio = f"""
🚨 NOVO LEAD IMOBILIÁRIO

👤 Objetivo: {dados.get('objetivo', '')}

🏡 Tipo de imóvel: {dados.get('tipo_imovel', '')}

🛏 Quartos: {dados.get('quartos', '')}

📐 Metragem: {dados.get('metragem', '')}

🌱 Finalidade rural: {dados.get('finalidade', '')}

📍 Bairro/Região: {dados.get('bairro', '')}

💰 Faixa de valor: {dados.get('faixa_valor', '')}

📱 WhatsApp Cliente: {dados.get('telefone', '')}

📊 Score: {score}

{classificacao}
"""

        # =================================
        # ENVIO AUTOMÁTICO
        # =================================

        enviar_whatsapp(relatorio)

        del sessoes[session_id]

        return {

            "mensagem": (
                "✅ Atendimento concluído com sucesso!\n\n"
                "Nossa equipe já recebeu suas informações.\n\n"
                "Em breve um corretor entrará em contato 😊"
            ),

            "link_whatsapp":
                "https://wa.me/5532998148333"

        }

    # =====================================
    # FALLBACK
    # =====================================

    return {

        "mensagem":
            "Desculpe, não consegui entender sua resposta."

    }