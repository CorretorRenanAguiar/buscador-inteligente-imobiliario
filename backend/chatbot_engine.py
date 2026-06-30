# ============================================
# chatbot_engine.py
# ============================================

import logging
import os
import re
import requests

logger = logging.getLogger(__name__)

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
        logger.warning("NUMERO_CORRETOR não configurado; envio Z-API pulado.")
        return False

    try:
        url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
        headers = {"Client-Token": ZAPI_CLIENT_TOKEN}
        payload = {"phone": destino, "message": relatorio}
        requests.post(url, json=payload, headers=headers, timeout=10)
        return True
    except Exception as erro:
        logger.exception("Erro ao enviar mensagem via Z-API")
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
    logger.info(
        "Entrando em processar_chatbot() | session_id=%s | mensagem=%s",
        session_id,
        mensagem[:120],
    )
    try:
        # ========================================
        # NOVA SESSÃO
        # ========================================

        if session_id not in sessoes:
            sessoes[session_id] = {"etapa": "objetivo"}
            resposta = {
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
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessoes[session_id]["etapa"],
                list(resposta.keys()),
            )
            return resposta

        sessao = sessoes[session_id]
        etapa = sessao["etapa"]
        logger.info(
            "processar_chatbot etapagem | session_id=%s | etapa=%s",
            session_id,
            etapa,
        )

        # ========================================
        # DETECTAR PERMUTA
        # ========================================

        if detectar_permuta(mensagem):
            sessao["permuta"] = True
            sessao["etapa"] = "whatsapp_permuta"
            resposta = {
                "mensagem": "Entendi 😊\n\n"
                "Casos de permuta exigem análise personalizada.\n\n"
                "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato.",
                "opcoes": [],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # OBJETIVO
        # ========================================

        if etapa == "objetivo":
            sessao["objetivo"] = mensagem
            sessao["etapa"] = "tipo_imovel"
            if "alugar" in mensagem.lower():
                resposta = {
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
            else:
                resposta = {
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
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # TIPO IMÓVEL
        # ========================================

        if etapa == "tipo_imovel":
            sessao["tipo_imovel"] = mensagem
            tipo = mensagem.lower()
            if tipo in ["granja", "chácara", "chacara", "fazenda", "sítio", "sitio"]:
                sessao["etapa"] = "objetivo_rural"
                resposta = {
                    "mensagem": "Excelente 😊\n\n"
                    "Qual o objetivo principal do imóvel?",
                    "opcoes": ["Lazer", "Moradia", "Produção rural", "Investimento"],
                }
                logger.info(
                    "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                    session_id,
                    sessao["etapa"],
                    list(resposta.keys()),
                )
                return resposta
            if tipo == "terreno":
                sessao["etapa"] = "objetivo_terreno"
                resposta = {
                    "mensagem": "Perfeito 👍\n\n" "Qual a finalidade do terreno?",
                    "opcoes": [
                        "Construir para morar",
                        "Investimento",
                        "Construção comercial",
                    ],
                }
                logger.info(
                    "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                    session_id,
                    sessao["etapa"],
                    list(resposta.keys()),
                )
                return resposta
            sessao["etapa"] = "uso_imovel"
            resposta = {
                "mensagem": "Qual será o principal uso do imóvel?",
                "opcoes": ["Moradia", "Investimento", "Moradia e investimento"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # USO IMÓVEL
        # ========================================

        if etapa == "uso_imovel":
            sessao["uso_imovel"] = mensagem
            sessao["etapa"] = "primeiro_imovel"
            resposta = {
                "mensagem": "Será seu primeiro imóvel?",
                "opcoes": ["Sim", "Não"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # PRIMEIRO IMÓVEL
        # ========================================

        if etapa == "primeiro_imovel":
            sessao["primeiro_imovel"] = mensagem
            sessao["etapa"] = "quartos"
            resposta = {
                "mensagem": "Quantos quartos você deseja?",
                "opcoes": ["1 quarto", "2 quartos", "3 quartos", "4 quartos ou mais"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # OBJETIVO RURAL
        # ========================================

        if etapa == "objetivo_rural":
            sessao["objetivo_rural"] = mensagem
            sessao["etapa"] = "hectares"
            resposta = {
                "mensagem": "Ótimo 👍\n\n" "Qual tamanho aproximado procura?",
                "opcoes": [
                    "Até 1 hectare",
                    "1 a 5 hectares",
                    "5 a 20 hectares",
                    "Acima de 20 hectares",
                ],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # HECTARES
        # ========================================

        if etapa == "hectares":
            sessao["hectares"] = mensagem
            sessao["etapa"] = "localizacao"
            resposta = {
                "mensagem": "Perfeito 😊\n\n" "Qual localização deseja para o imóvel?",
                "opcoes": [],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # OBJETIVO TERRENO
        # ========================================

        if etapa == "objetivo_terreno":
            sessao["objetivo_terreno"] = mensagem
            sessao["etapa"] = "localizacao"
            resposta = {
                "mensagem": "Excelente 👍\n\n"
                "Qual localização deseja para o terreno?",
                "opcoes": [],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # QUARTOS
        # ========================================

        if etapa == "quartos":
            sessao["quartos"] = mensagem
            sessao["etapa"] = "banheiros"
            resposta = {
                "mensagem": "Perfeito 👍\n\n" "Quantos banheiros você deseja?",
                "opcoes": ["1 banheiro", "2 banheiros", "3 banheiros", "4 ou mais"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # BANHEIROS
        # ========================================

        if etapa == "banheiros":
            sessao["banheiros"] = mensagem
            sessao["etapa"] = "vagas"
            resposta = {
                "mensagem": "Ótimo 😊\n\n" "Quantas vagas de garagem você precisa?",
                "opcoes": ["Sem garagem", "1 vaga", "2 vagas", "3 ou mais"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # VAGAS
        # ========================================

        if etapa == "vagas":
            sessao["vagas"] = mensagem
            if "alugar" in sessao["objetivo"].lower():
                sessao["etapa"] = "mobiliado"
                resposta = {
                    "mensagem": "Perfeito 👍\n\n" "Você procura imóvel:",
                    "opcoes": ["Mobiliado", "Semimobiliado", "Não importa"],
                }
            else:
                sessao["etapa"] = "localizacao"
                resposta = {
                    "mensagem": "Perfeito 👍\n\n"
                    "Qual localização deseja para o imóvel?",
                    "opcoes": [],
                }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # MOBILIADO
        # ========================================

        if etapa == "mobiliado":
            sessao["mobiliado"] = mensagem
            sessao["etapa"] = "pet"
            resposta = {
                "mensagem": "Você possui animais de estimação?",
                "opcoes": ["Sim", "Não"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # PET
        # ========================================

        if etapa == "pet":
            sessao["pet"] = mensagem
            sessao["etapa"] = "localizacao"
            resposta = {
                "mensagem": "Excelente 😊\n\n" "Qual localização deseja para o imóvel?",
                "opcoes": [],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # LOCALIZAÇÃO
        # ========================================

        if etapa == "localizacao":
            if not validar_localizacao(mensagem):
                resposta = {
                    "mensagem": "Não consegui identificar a localização 😊\n\n"
                    "Pode informar a cidade, bairro, região ou referência desejada?",
                    "opcoes": [],
                }
                logger.info(
                    "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                    session_id,
                    sessao["etapa"],
                    list(resposta.keys()),
                )
                return resposta
            sessao["localizacao"] = mensagem
            sessao["etapa"] = "faixa_valor"
            if "alugar" in sessao["objetivo"].lower():
                resposta = {
                    "mensagem": "Ótimo 😊\n\n" "Qual faixa de aluguel você procura?",
                    "opcoes": [
                        "Até R$ 800",
                        "R$ 800 a R$ 1.500",
                        "R$ 1.500 a R$ 3.000",
                        "R$ 3.000 a R$ 5.000",
                        "Acima de R$ 5.000",
                    ],
                }
            else:
                resposta = {
                    "mensagem": "Excelente 😊\n\n" "Qual faixa de valor você procura?",
                    "opcoes": [
                        "Até R$ 150 mil",
                        "R$ 150 mil a R$ 300 mil",
                        "R$ 300 mil a R$ 500 mil",
                        "R$ 500 mil a R$ 1 milhão",
                        "Acima de R$ 1 milhão",
                    ],
                }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # FAIXA VALOR
        # ========================================

        if etapa == "faixa_valor":
            sessao["faixa_valor"] = mensagem
            sessao["etapa"] = "financiamento"
            resposta = {
                "mensagem": "Você pretende utilizar financiamento?",
                "opcoes": ["Sim", "Não", "Ainda vou verificar"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # FINANCIAMENTO
        # ========================================

        if etapa == "financiamento":
            sessao["financiamento"] = mensagem
            sessao["etapa"] = "fgts"
            resposta = {
                "mensagem": "Pretende utilizar FGTS?",
                "opcoes": ["Sim", "Não", "Não sei"],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # FGTS
        # ========================================

        if etapa == "fgts":
            sessao["fgts"] = mensagem
            sessao["etapa"] = "renda_familiar"
            resposta = {
                "mensagem": "Qual sua renda familiar aproximada?",
                "opcoes": [
                    "Até R$ 3.000",
                    "R$ 3.000 a R$ 5.000",
                    "R$ 5.000 a R$ 8.000",
                    "Acima de R$ 8.000",
                ],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # RENDA FAMILIAR
        # ========================================

        if etapa == "renda_familiar":
            sessao["renda_familiar"] = mensagem
            sessao["etapa"] = "prazo_compra"
            resposta = {
                "mensagem": "Quando pretende comprar o imóvel?",
                "opcoes": [
                    "Imediatamente",
                    "Até 3 meses",
                    "Até 6 meses",
                    "Mais de 6 meses",
                ],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # PRAZO COMPRA
        # ========================================

        if etapa == "prazo_compra":
            sessao["prazo_compra"] = mensagem
            sessao["etapa"] = "whatsapp"
            resposta = {
                "mensagem": "Perfeito 😊\n\n"
                "Informe seu WhatsApp com DDD para continuar.",
                "opcoes": [],
            }
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                sessao["etapa"],
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # WHATSAPP
        # ========================================

        if etapa in ["whatsapp", "whatsapp_permuta"]:
            whatsapp = re.sub(r"\D", "", mensagem)
            logger.info(
                "processar_chatbot etapa whatsapp | session_id=%s | whatsapp=%s",
                session_id,
                whatsapp,
            )
            sessao["whatsapp"] = whatsapp
            perfil = classificar_perfil(sessao)
            score = calcular_score(sessao)
            relatorio = criar_relatorio(perfil, sessao, whatsapp, score)
            enviado = enviar_whatsapp(relatorio)
            logger.info(
                "enviar_whatsapp retornou %s | session_id=%s", enviado, session_id
            )
            del sessoes[session_id]
            resposta = {
                "mensagem": "✅ Atendimento concluído com sucesso!\n\n"
                "Nossa equipe já recebeu suas informações.\n\n"
                "Em breve um corretor entrará em contato 😊",
            }
            if NUMERO_CORRETOR:
                resposta["link_whatsapp"] = f"https://wa.me/{NUMERO_CORRETOR}"
            else:
                resposta["aviso"] = (
                    "NUMERO_CORRETOR não configurado. Configure a variável de ambiente "
                    "NUMERO_CORRETOR para habilitar o link direto ao corretor."
                )
                resposta["relatorio"] = relatorio
            logger.info(
                "Saindo de processar_chatbot() | session_id=%s | etapa=%s | resposta_keys=%s",
                session_id,
                etapa,
                list(resposta.keys()),
            )
            return resposta

        # ========================================
        # FALLBACK
        # ========================================

        resposta = {
            "mensagem": "Desculpe, não consegui entender.\n\n" "Tente novamente 😊"
        }
        logger.info(
            "Saindo de processar_chatbot() | session_id=%s | etapa=%s | fallback | resposta_keys=%s",
            session_id,
            etapa,
            list(resposta.keys()),
        )
        return resposta
    except Exception:
        logger.exception(
            "Erro encontrado em processar_chatbot() | session_id=%s", session_id
        )
        raise
