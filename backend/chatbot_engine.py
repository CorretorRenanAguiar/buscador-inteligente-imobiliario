from database import supabase

sessoes = {}



# =========================================
# SCORE
# =========================================

def calcular_score(sessao):

    score = 0



    if sessao.get("objetivo"):
        score += 20



    if sessao.get("tipo_imovel"):
        score += 20



    if sessao.get("quartos"):
        score += 10



    if sessao.get("bairro"):
        score += 20



    if sessao.get("valor"):
        score += 30



    if sessao.get("telefone"):
        score += 40



    return score



# =========================================
# CLASSIFICAÇÃO
# =========================================

def classificar_lead(score):

    if score >= 90:
        return "lead_quente"



    elif score >= 60:
        return "lead_morno"



    return "lead_frio"



# =========================================
# PROCESSAR CHATBOT
# =========================================

async def processar_chatbot(

    mensagem,

    session_id

):

    texto = mensagem.lower()



    # =====================================
    # FALAR COM CORRETOR
    # =====================================

    if any(

        termo in texto

        for termo in [

            "corretor",

            "atendente",

            "humano",

            "whatsapp"

        ]

    ):

        return {

            "resposta":

                "Perfeito 👍\n\n"

                "Você será direcionado "

                "para um corretor.",

            "abrir_whatsapp": True,

            "whatsapp_texto":

                "Olá Renan, gostaria de falar com um corretor.",

            "opcoes": [],

            "classificacao":
                "lead_quente",

            "score": 100

        }



    # =====================================
    # CRIAR SESSÃO
    # =====================================

    if session_id not in sessoes:

        sessoes[session_id] = {

            "etapa": "objetivo",

            "objetivo": None,

            "tipo_imovel": None,

            "quartos": None,

            "bairro": None,

            "valor": None,

            "telefone": None

        }



    sessao = sessoes[session_id]



    # =====================================
    # OBJETIVO
    # =====================================

    if sessao["etapa"] == "objetivo":

        if texto not in [

            "comprar",

            "alugar",

            "investir",

            "anunciar imóvel"

        ]:

            return {

                "resposta":

                    "Olá 👋\n\n"

                    "Sou a assistente virtual "

                    "da RA Corretor de Imóveis.\n\n"

                    "Como posso ajudar?",

                "opcoes": [

                    "Comprar",

                    "Alugar",

                    "Investir",

                    "Anunciar Imóvel"

                ],

                "classificacao":
                    "lead_frio",

                "score": 10

            }



        sessao["objetivo"] = texto

        sessao["etapa"] = "tipo"



        return {

            "resposta":

                "Perfeito 👍\n\n"

                "Qual tipo de imóvel possui interesse?",

            "opcoes": [

                "Casa",

                "Apartamento",

                "Cobertura",

                "Kitnet",

                "Studio",

                "Granja",

                "Sítio",

                "Lote",

                "Sala Comercial",

                "Loja",

                "Galpão"

            ],

            "classificacao":
                "lead_morno",

            "score": 20

        }



    # =====================================
    # TIPO IMÓVEL
    # =====================================

    elif sessao["etapa"] == "tipo":

        sessao["tipo_imovel"] = mensagem



        # =================================
        # ANUNCIAR IMÓVEL
        # =================================

        if sessao["objetivo"] == "anunciar imóvel":

            sessao["etapa"] = "bairro"



            return {

                "resposta":

                    "Perfeito 👍\n\n"

                    "Qual a localização do imóvel?",

                "opcoes": [],

                "classificacao":
                    "lead_morno",

                "score": 40

            }



        # =================================
        # IMÓVEIS SEM QUARTOS
        # =================================

        if mensagem.lower() in [

            "lote",

            "loja",

            "galpão",

            "sala comercial"

        ]:

            sessao["etapa"] = "bairro"



            return {

                "resposta":

                    "Qual bairro ou região possui interesse?",

                "opcoes": [],

                "classificacao":
                    "lead_morno",

                "score": 40

            }



        # =================================
        # IMÓVEIS COM QUARTOS
        # =================================

        sessao["etapa"] = "quartos"



        return {

            "resposta":

                "Quantos quartos deseja?",

            "opcoes": [

                "1",

                "2",

                "3",

                "4+"

            ],

            "classificacao":
                "lead_morno",

            "score": 40

        }



    # =====================================
    # QUARTOS
    # =====================================

    elif sessao["etapa"] == "quartos":

        sessao["quartos"] = mensagem

        sessao["etapa"] = "bairro"



        return {

            "resposta":

                "Qual bairro ou região possui interesse?\n\n"

                "Você pode digitar bairros "

                "ou regiões desejadas.",

            "opcoes": [],

            "classificacao":
                "lead_morno",

            "score": 50

        }



    # =====================================
    # BAIRRO
    # =====================================

    elif sessao["etapa"] == "bairro":

        sessao["bairro"] = mensagem

        sessao["etapa"] = "valor"



        # =================================
        # ALUGUEL
        # =================================

        if sessao["objetivo"] == "alugar":

            return {

                "resposta":

                    "Qual faixa de aluguel deseja?",

                "opcoes": [

                    "Até R$800",

                    "R$800 - R$1.500",

                    "R$1.500 - R$3.000",

                    "Acima de R$3.000"

                ],

                "classificacao":
                    "lead_morno",

                "score": 70

            }



        # =================================
        # ANUNCIAR IMÓVEL
        # =================================

        elif sessao["objetivo"] == "anunciar imóvel":

            return {

                "resposta":

                    "Você já possui uma "

                    "faixa de valor para anúncio?",

                "opcoes": [

                    "Até R$200 mil",

                    "R$200 mil - R$400 mil",

                    "R$400 mil - R$700 mil",

                    "Acima de R$700 mil"

                ],

                "classificacao":
                    "lead_morno",

                "score": 70

            }



        # =================================
        # COMPRA / INVESTIMENTO
        # =================================

        return {

            "resposta":

                "Qual faixa de valor deseja?",

            "opcoes": [

                "R$100 mil - R$200 mil",

                "R$200 mil - R$300 mil",

                "R$300 mil - R$400 mil",

                "Acima de R$400 mil"

            ],

            "classificacao":
                "lead_quente",

            "score": 70

        }



    # =====================================
    # VALOR
    # =====================================

    elif sessao["etapa"] == "valor":

        sessao["valor"] = mensagem

        sessao["etapa"] = "telefone"



        return {

            "resposta":

                "Perfeito 🚀\n\n"

                "Informe seu WhatsApp com DDD "

                "para receber atendimento "

                "e imóveis compatíveis.",

            "opcoes": [],

            "classificacao":
                "lead_quente",

            "score": 80

        }



    # =====================================
    # TELEFONE
    # =====================================

    elif sessao["etapa"] == "telefone":

        sessao["telefone"] = mensagem



        score = calcular_score(
            sessao
        )



        classificacao = classificar_lead(
            score
        )



        relatorio = f"""
🏠 NOVO LEAD IMOBILIÁRIO

🎯 Objetivo: {sessao['objetivo']}
🏡 Tipo: {sessao['tipo_imovel']}
🛏 Quartos: {sessao['quartos']}
📍 Região: {sessao['bairro']}
💰 Faixa: {sessao['valor']}
📞 WhatsApp: {sessao['telefone']}

🔥 Classificação: {classificacao}
⭐ Score: {score}
"""



        try:

            supabase.table(
                "chatbot_logs"
            ).insert({

                "session_id":
                    session_id,

                "mensagem_usuario":
                    mensagem,

                "resposta_chatbot":
                    relatorio,

                "intencao_detectada":
                    sessao["objetivo"],

                "score_interesse":
                    score

            }).execute()

        except Exception as erro:

            print(erro)



        return {

            "resposta":

                "Perfil registrado com sucesso ✅\n\n"

                "Você será direcionado "

                "para um corretor.",

            "abrir_whatsapp": True,

            "whatsapp_texto":
                relatorio,

            "opcoes": [],

            "classificacao":
                classificacao,

            "score":
                score

        }



    # =====================================
    # FINAL
    # =====================================

    return {

        "resposta":

            "Posso continuar ajudando "

            "você 👍",

        "opcoes": [],

        "classificacao":
            "lead_quente",

        "score": 100

    }