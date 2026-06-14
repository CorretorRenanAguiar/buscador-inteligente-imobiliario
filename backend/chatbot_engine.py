# ============================================
# chatbot_engine.py
# ============================================

import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURAÇÕES
# ============================================

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE", "")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN", "")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN", "")
NUMERO_CORRETOR = os.getenv("NUMERO_CORRETOR", "")

PALAVRAS_PERMUTA = ["permuta", "troca", "permutar"]
LOCALIZACOES_INVALIDAS = ["aqui", "lá", "ali", "acolá"]

sessoes = {}

# ============================================


def criar_relatorio(perfil, sessao, whatsapp, score):
    relatorio = f"""
🚨 NOVO LEAD IMOBILIÁRIO

👤 Perfil:
{perfil}

🎯 Objetivo:
{sessao.get('objetivo', 'Não informado')}

🏡 Uso do imóvel:
{sessao.get('uso_imovel', 'Não informado')}

🔑 Primeiro imóvel:
{sessao.get('primeiro_imovel', 'Não informado')}

🏠 Tipo imóvel:
{sessao.get('tipo_imovel')}

🛏️ Quartos:
{sessao.get('quartos', 'Não informado')}
🚿 Banheiros:
{sessao.get('banheiros', 'Não informado')}

🚗 Vagas:
{sessao.get('vagas', 'Não informado')}
🐶 Possui pet:
{sessao.get('pet', 'Não informado')}

🛋️ Mobiliado:
{sessao.get('mobiliado', 'Não informado')}

🌱 Objetivo rural:
{sessao.get('objetivo_rural', 'Não informado')}

📏 Área/Hectares:
{sessao.get('hectares', 'Não informado')}

📍 Localização:
{sessao.get('localizacao')}

💰 Faixa valor:
{sessao.get('faixa_valor')}
🏦 Financiamento:
{sessao.get('financiamento', 'Não informado')}

💵 FGTS:
{sessao.get('fgts', 'Não informado')}
👨‍👩‍👧‍👦 Renda familiar:
{sessao.get('renda_familiar', 'Não informado')}

⏳ Prazo compra:
{sessao.get('prazo_compra', 'Não informado')}

🔁 Permuta:
{'Sim' if sessao.get('permuta') else 'Não'}

📱 WhatsApp cliente:
{whatsapp}

🔥 Score Lead:
{score}
"""
    return relatorio


# ENVIAR WHATSAPP
# ============================================


def enviar_whatsapp(relatorio, phone=None):
    """Envia o relatório por Z-API para `phone` ou `NUMERO_CORRETOR`.

    Retorna True se a tentativa de envio foi iniciada, False caso contrário.
    """
    destino = phone or NUMERO_CORRETOR

    if not destino:
        print("Aviso: NUMERO_CORRETOR não configurado; envio Z-API pulado.")
        return False

    try:
        url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
        headers = {"Client-Token": ZAPI_CLIENT_TOKEN}
        payload = {"phone": destino, "message": relatorio}
        requests.post(url, json=payload, headers=headers)
        return True
    except Exception as erro:
        print("Erro Z-API:", erro)
        return False


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
# CALCULAR SCORE
# ============================================


def calcular_score(dados):

    score = 0

    objetivo = dados.get("objetivo", "").lower()

    faixa = dados.get("faixa_valor", "").lower()

    tipo = dados.get("tipo_imovel", "").lower()

    whatsapp = dados.get("whatsapp", "")

    # ========================================
    # IMÓVEL COMERCIAL
    # ========================================

    if tipo == "imóvel comercial":

        score += 3

    # ========================================
    # RURAL
    # ========================================

    if tipo in ["fazenda", "granja", "chácara", "chacara", "sítio", "sitio"]:

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

    if tipo in ["fazenda", "granja", "chácara", "chacara", "sítio", "sitio"]:

        return "Rural"

    if "alugar" in objetivo:

        return "Locação"

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

        sessoes[session_id] = {"etapa": "objetivo"}

        return {
            "mensagem": (
                "Olá 👋\n\n"
                "Sou a assistente virtual imobiliária de Renan Aguiar.\n\n"
                "Vou entender rapidamente o perfil do imóvel que você procura 😊\n\n"
                "Qual é o seu objetivo?"
            ),
            "opcoes": ["Comprar imóvel", "Alugar imóvel", "Investir", "Sou corretor"],
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
            "mensagem": "Entendi 😊\n\n"
            "Casos de permuta exigem análise personalizada.\n\n"
            "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato.",
            "opcoes": [],
        }

    # ========================================
    # OBJETIVO
    # ========================================

    if etapa == "objetivo":

        sessao["objetivo"] = mensagem

        sessao["etapa"] = "tipo_imovel"

        # ====================================
        # ALUGUEL
        # ====================================

        if "alugar" in mensagem.lower():

            return {
                "mensagem": "Perfeito 👍\n\n" "Qual tipo de imóvel você procura?",
                "opcoes": [
                    "Casa",
                    "Apartamento",
                    "Kitnet",
                    "Cobertura",
                    "Terreno",
                    "Imóvel comercial",
                ],
            }

        # ====================================
        # COMPRA
        # ====================================

        return {
            "mensagem": "Perfeito 👍\n\n" "Qual tipo de imóvel você procura?",
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

    # # ========================================

    # TIPO IMÓVEL

    # ========================================

    if etapa == "tipo_imovel":

        sessao["tipo_imovel"] = mensagem

        tipo = mensagem.lower()

        # ====================================
        # RURAL
        # ====================================

        if tipo in ["granja", "chácara", "chacara", "fazenda", "sítio", "sitio"]:

            sessao["etapa"] = "objetivo_rural"

            return {
                "mensagem": "Excelente 😊\n\n" "Qual o objetivo principal do imóvel?",
                "opcoes": ["Lazer", "Moradia", "Produção rural", "Investimento"],
            }

        # ====================================
        # TERRENO
        # ====================================

        if tipo == "terreno":

            sessao["etapa"] = "objetivo_terreno"

            return {
                "mensagem": "Perfeito 👍\n\n" "Qual a finalidade do terreno?",
                "opcoes": [
                    "Construir para morar",
                    "Investimento",
                    "Construção comercial",
                ],
            }

        # ====================================
        # USO DO IMÓVEL
        # ====================================

        sessao["etapa"] = "uso_imovel"

        return {
            "mensagem": "Qual será o principal uso do imóvel?",
            "opcoes": ["Moradia", "Investimento", "Moradia e investimento"],
        }

    # ========================================

    # USO IMÓVEL

    # ========================================

    if etapa == "uso_imovel":

        sessao["uso_imovel"] = mensagem

        sessao["etapa"] = "primeiro_imovel"

        return {"mensagem": "Será seu primeiro imóvel?", "opcoes": ["Sim", "Não"]}

    # ========================================

    # PRIMEIRO IMÓVEL

    # ========================================

    if etapa == "primeiro_imovel":

        sessao["primeiro_imovel"] = mensagem

        sessao["etapa"] = "quartos"

        return {
            "mensagem": "Quantos quartos você deseja?",
            "opcoes": ["1 quarto", "2 quartos", "3 quartos", "4 quartos ou mais"],
        }

    # ========================================
    # OBJETIVO RURAL
    # ========================================

    if etapa == "objetivo_rural":

        sessao["objetivo_rural"] = mensagem

        sessao["etapa"] = "hectares"

        return {
            "mensagem": "Ótimo 👍\n\n" "Qual tamanho aproximado procura?",
            "opcoes": [
                "Até 1 hectare",
                "1 a 5 hectares",
                "5 a 20 hectares",
                "Acima de 20 hectares",
            ],
        }

    # ========================================
    # HECTARES
    # ========================================

    if etapa == "hectares":

        sessao["hectares"] = mensagem

        sessao["etapa"] = "localizacao"

        return {
            "mensagem": "Perfeito 😊\n\n" "Qual localização deseja para o imóvel?",
            "opcoes": [],
        }

    # ========================================
    # OBJETIVO TERRENO
    # ========================================

    if etapa == "objetivo_terreno":

        sessao["objetivo_terreno"] = mensagem

        sessao["etapa"] = "localizacao"

        return {
            "mensagem": "Excelente 👍\n\n" "Qual localização deseja para o terreno?",
            "opcoes": [],
        }

    # ========================================
    # QUARTOS
    # ========================================

    if etapa == "quartos":

        sessao["quartos"] = mensagem

        sessao["etapa"] = "banheiros"

        return {
            "mensagem": "Perfeito 👍\n\n" "Quantos banheiros você deseja?",
            "opcoes": ["1 banheiro", "2 banheiros", "3 banheiros", "4 ou mais"],
        }

    # ========================================

    # BANHEIROS

    # ========================================

    if etapa == "banheiros":

        sessao["banheiros"] = mensagem

        sessao["etapa"] = "vagas"

        return {
            "mensagem": "Ótimo 😊\n\n" "Quantas vagas de garagem você precisa?",
            "opcoes": ["Sem garagem", "1 vaga", "2 vagas", "3 ou mais"],
        }

    # ========================================

    # VAGAS

    # ========================================

    if etapa == "vagas":

        sessao["vagas"] = mensagem

        if "alugar" in sessao["objetivo"].lower():

            sessao["etapa"] = "mobiliado"

            return {
                "mensagem": "Perfeito 👍\n\n" "Você procura imóvel:",
                "opcoes": ["Mobiliado", "Semimobiliado", "Não importa"],
            }

        sessao["etapa"] = "localizacao"

        return {
            "mensagem": "Perfeito 👍\n\n" "Qual localização deseja para o imóvel?",
            "opcoes": [],
        }

    # ========================================

    # MOBILIADO

    # ========================================

    if etapa == "mobiliado":

        sessao["mobiliado"] = mensagem

        sessao["etapa"] = "pet"

        return {
            "mensagem": "Você possui animais de estimação?",
            "opcoes": ["Sim", "Não"],
        }

    # ========================================

    # PET

    # ========================================

    if etapa == "pet":

        sessao["pet"] = mensagem

        sessao["etapa"] = "localizacao"

        return {
            "mensagem": "Excelente 😊\n\n" "Qual localização deseja para o imóvel?",
            "opcoes": [],
        }

    # ========================================

    # LOCALIZAÇÃO

    # ========================================

    if etapa == "localizacao":

        if not validar_localizacao(mensagem):

            return {
                "mensagem": "Não consegui identificar a localização 😊\n\n"
                "Pode informar a cidade, bairro, região ou referência desejada?",
                "opcoes": [],
            }

        sessao["localizacao"] = mensagem

        sessao["etapa"] = "faixa_valor"

        if "alugar" in sessao["objetivo"].lower():

            return {
                "mensagem": "Ótimo 😊\n\n" "Qual faixa de aluguel você procura?",
                "opcoes": [
                    "Até R$ 800",
                    "R$ 800 a R$ 1.500",
                    "R$ 1.500 a R$ 3.000",
                    "R$ 3.000 a R$ 5.000",
                    "Acima de R$ 5.000",
                ],
            }

        return {
            "mensagem": "Excelente 😊\n\n" "Qual faixa de valor você procura?",
            "opcoes": [
                "Até R$ 150 mil",
                "R$ 150 mil a R$ 300 mil",
                "R$ 300 mil a R$ 500 mil",
                "R$ 500 mil a R$ 1 milhão",
                "Acima de R$ 1 milhão",
            ],
        }

    # ========================================

    # FAIXA VALOR

    # ========================================

    if etapa == "faixa_valor":
        sessao["faixa_valor"] = mensagem

        sessao["etapa"] = "financiamento"

        return {
            "mensagem": "Você pretende utilizar financiamento?",
            "opcoes": ["Sim", "Não", "Ainda vou verificar"],
        }

    # ========================================

    # FINANCIAMENTO

    # ========================================

    if etapa == "financiamento":
        sessao["financiamento"] = mensagem

        sessao["etapa"] = "fgts"

        return {
            "mensagem": "Pretende utilizar FGTS?",
            "opcoes": ["Sim", "Não", "Não sei"],
        }

    # ========================================

    # FGTS

    # ========================================

    if etapa == "fgts":

        sessao["fgts"] = mensagem

        sessao["etapa"] = "renda_familiar"

        return {
            "mensagem": "Qual sua renda familiar aproximada?",
            "opcoes": [
                "Até R$ 3.000",
                "R$ 3.000 a R$ 5.000",
                "R$ 5.000 a R$ 8.000",
                "Acima de R$ 8.000",
            ],
        }

    # ========================================

    # RENDA FAMILIAR

    # ========================================

    if etapa == "renda_familiar":
        sessao["renda_familiar"] = mensagem
        sessao["etapa"] = "prazo_compra"
        return {
            "mensagem": "Quando pretende comprar o imóvel?",
            "opcoes": [
                "Imediatamente",
                "Até 3 meses",
                "Até 6 meses",
                "Mais de 6 meses",
            ],
        }

    # ========================================

    # PRAZO COMPRA

    # ========================================

    if etapa == "prazo_compra":
        sessao["prazo_compra"] = mensagem
        sessao["etapa"] = "whatsapp"
        return {
            "mensagem": "Perfeito 😊\n\n"
            "Informe seu WhatsApp com DDD para continuar.",
            "opcoes": [],
        }

    # ========================================
    # WHATSAPP
    # ========================================

    if etapa in ["whatsapp", "whatsapp_permuta"]:
        whatsapp = re.sub(r"\D", "", mensagem)

        sessao["whatsapp"] = whatsapp

        perfil = classificar_perfil(sessao)

        score = calcular_score(sessao)

        relatorio = criar_relatorio(perfil, sessao, whatsapp, score)

        enviado = enviar_whatsapp(relatorio)

        del sessoes[session_id]

        resposta = {
            "mensagem": "✅ Atendimento concluído com sucesso!\n\n"
            "Nossa equipe já recebeu suas informações.\n\n"
            "Em breve um corretor entrará em contato 😊",
        }

        if NUMERO_CORRETOR:
            resposta["link_whatsapp"] = f"https://wa.me/{NUMERO_CORRETOR}"
        else:
            # Quando o número do corretor não estiver configurado, incluímos
            # o relatório no retorno para permitir encaminhamento manual.
            resposta["aviso"] = (
                "NUMERO_CORRETOR não configurado. Configure a variável de ambiente "
                "NUMERO_CORRETOR para habilitar o link direto ao corretor."
            )
            resposta["relatorio"] = relatorio

        return resposta

    # ========================================
    # FALLBACK
    # ========================================

    return {"mensagem": "Desculpe, não consegui entender.\n\n" "Tente novamente 😊"}
