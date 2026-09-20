import json
import os
import re
from typing import Any, Dict, Optional

import redis
from dotenv import load_dotenv
from supabase import create_client

from evolution_api import enviar_mensagem_whatsapp, obter_numero_corretor

load_dotenv()

# Configuração do Supabase

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Sessões do chatbot

SESSION_PREFIX = "chatbot:sessao:"
MEMORY_SESSIONS: Dict[str, Dict[str, Any]] = {}
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/6")

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None


def _session_key(session_id: str, tenant_id: str = "RA_IMOBILIARIA") -> str:
    return f"{SESSION_PREFIX}{tenant_id}:{session_id}"


def _carregar_sessao(
    session_id: str, tenant_id: str = "RA_IMOBILIARIA"
) -> Dict[str, Any]:
    if not session_id:
        return {}

    chave = _session_key(session_id, tenant_id)

    if redis_client is not None:
        valor = redis_client.get(chave)
        if valor:
            try:
                return json.loads(valor)
            except (TypeError, ValueError):
                return {}

    return MEMORY_SESSIONS.get(chave, {})


def _salvar_sessao(
    sessao: Dict[str, Any], session_id: str, tenant_id: str = "RA_IMOBILIARIA"
) -> None:
    if not session_id:
        return

    chave = _session_key(session_id, tenant_id)
    payload = json.dumps(sessao, ensure_ascii=False)

    if redis_client is not None:
        redis_client.set(chave, payload, ex=3600)
        return

    MEMORY_SESSIONS[chave] = sessao


def _remover_sessao(session_id: str, tenant_id: str = "RA_IMOBILIARIA") -> None:
    if not session_id:
        return

    chave = _session_key(session_id, tenant_id)

    if redis_client is not None:
        redis_client.delete(chave)
        return

    MEMORY_SESSIONS.pop(chave, None)


# Palavras relacionadas a troca/permuta

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
    "aceitar imovel",
]

# Localizações inválidas

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
    "nada",
]

# Validação da localização


def validar_localizacao(texto):
    texto = texto.strip().lower()

    if len(texto) < 3:
        return False

    if texto in LOCALIZACOES_INVALIDAS:
        return False

    return True


# Detecção de permuta


def detectar_permuta(texto):
    texto = texto.lower()

    for palavra in PALAVRAS_PERMUTA:
        if palavra in texto:
            return True

    return False


# Cálculo do score do lead


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

    if len(whatsapp) >= 11:
        score += 2

    if tipo == "imóvel comercial":
        score += 3

    if tipo in ["fazenda", "granja", "sítio", "sitio", "chácara", "chacara"]:
        score += 3

    if dados.get("permuta"):
        score += 5

    return score


# Classificação do perfil do lead


def classificar_perfil(dados):
    tipo = dados.get("tipo_imovel", "").lower()
    objetivo = dados.get("objetivo", "").lower()

    if "alugar" in objetivo:
        return "Locação"

    if "invest" in objetivo:
        return "Investidor"

    if tipo in ["fazenda", "granja", "sítio", "sitio", "chácara", "chacara"]:
        return "Rural"

    if tipo == "lançamento":
        return "Lançamento"

    return "Residencial"


# Persistência do lead no Supabase


def _extrair_numero(texto):
    if not texto:
        return 0

    numeros = re.findall(r"\d+", str(texto))
    if numeros:
        return int(numeros[0])

    return 0


def salvar_lead_supabase(dados):
    try:
        score = calcular_score(dados)
        classificacao = "frio"

        if score >= 8:
            classificacao = "quente"
        elif score >= 4:
            classificacao = "morno"

        payload = {
            "telefone": dados.get("whatsapp"),
            "bairro": dados.get("localizacao"),
            "bairro_interesse": dados.get("localizacao"),
            "faixa_preco_interesse": dados.get("faixa_valor"),
            "tipo_interesse": dados.get("objetivo"),
            "tipo_imovel": dados.get("tipo_imovel"),
            "objetivo": dados.get("objetivo"),
            "quartos": _extrair_numero(dados.get("quartos")),
            "banheiros": _extrair_numero(dados.get("banheiros")),
            "vagas_garagem": _extrair_numero(dados.get("vagas_garagem")),
            "aceita_pet": dados.get("aceita_pet"),
            "momento_compra": dados.get("momento_compra"),
            "financiamento": dados.get("financiamento"),
            "fgts": dados.get("fgts"),
            "renda_familiar": dados.get("renda_familiar"),
            "origem_lead": "chatbot",
            "score_lead": score,
            "classificacao_lead": classificacao,
            "observacoes": str(
                {
                    "perfil": classificar_perfil(dados),
                    "objetivo_rural": dados.get("objetivo_rural"),
                    "hectares": dados.get("hectares"),
                    "mobiliado": dados.get("mobiliado"),
                    "permuta": dados.get("permuta"),
                }
            ),
        }

        resposta = supabase.table("leads").insert(payload).execute()
        print("====================================")
        print("LEAD SALVO SUPABASE")
        print(resposta)
        print("====================================")
        return True

    except Exception as erro:
        print("====================================")
        print("ERRO SUPABASE")
        print(str(erro))
        print("====================================")
        return False


# Envio do relatório para o WhatsApp


def enviar_whatsapp(relatorio, tenant_id="RA_IMOBILIARIA"):
    resultado = enviar_mensagem_whatsapp(
        str(relatorio),
        tenant_id=tenant_id,
    )
    return bool(resultado.get("sucesso"))


# Processamento do chatbot


async def processar_chatbot(mensagem, session_id, tenant_id="RA_IMOBILIARIA"):
    mensagem = mensagem.strip()
    tenant_id = (tenant_id or "RA_IMOBILIARIA").strip().upper()

    sessao = _carregar_sessao(session_id, tenant_id)

    if not sessao:
        sessao = {"etapa": "objetivo", "tenant_id": tenant_id}
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Olá 👋\n\n"
            "Sou a assistente virtual imobiliária de Renan Aguiar.\n\n"
            "Vou entender rapidamente o perfil do imóvel que você procura 😊\n\n"
            "Qual é o seu objetivo?",
            "opcoes": ["Comprar imóvel", "Alugar imóvel", "Investir", "Sou corretor"],
        }

    sessao["tenant_id"] = tenant_id
    etapa = sessao.get("etapa", "objetivo")

    if detectar_permuta(mensagem):
        sessao["permuta"] = True
        sessao["etapa"] = "whatsapp"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Entendi 😊\n\n"
            "Casos de permuta exigem análise personalizada.\n\n"
            "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato.",
            "opcoes": [],
        }

    if etapa == "objetivo":
        sessao["objetivo"] = mensagem
        sessao["etapa"] = "tipo_imovel"
        _salvar_sessao(sessao, session_id, tenant_id)

        if "alugar" in mensagem.lower():
            return {
                "mensagem": "Perfeito 😊\n\nQual tipo de imóvel você procura?",
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
            "mensagem": "Perfeito 😊\n\nQual tipo de imóvel você procura?",
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

    if etapa == "tipo_imovel":
        sessao["tipo_imovel"] = mensagem
        tipo = mensagem.lower()

        if tipo in ["granja", "fazenda", "sítio", "sitio", "chácara", "chacara"]:
            sessao["etapa"] = "objetivo_rural"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Excelente 😊\n\nQual o principal objetivo do imóvel rural?",
                "opcoes": ["Lazer", "Moradia", "Producao rural", "Investimento"],
            }

        if tipo == "terreno":
            sessao["etapa"] = "objetivo_terreno"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Perfeito.\n\nQual a finalidade do terreno?",
                "opcoes": [
                    "Construir para morar",
                    "Investimento",
                    "Construcao comercial",
                ],
            }

        sessao["etapa"] = "uso_imovel"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Qual será o principal uso do imóvel?",
            "opcoes": ["Moradia", "Comercial", "Investimento"],
        }

    if etapa == "uso_imovel":
        sessao["uso_imovel"] = mensagem
        sessao["etapa"] = "primeiro_imovel"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Será seu primeiro imóvel?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "primeiro_imovel":
        sessao["primeiro_imovel"] = mensagem
        sessao["etapa"] = "quartos"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Perfeito.\n\nQuantos quartos você deseja?",
            "opcoes": ["1 quarto", "2 quartos", "3 quartos", "4 quartos ou mais"],
        }

    if etapa == "objetivo_rural":
        sessao["objetivo_rural"] = mensagem
        sessao["etapa"] = "hectares"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Ótimo.\n\nQual tamanho aproximado procura?",
            "opcoes": [
                "Até 1 hectare",
                "1 a 5 hectares",
                "5 a 20 hectares",
                "Acima de 20 hectares",
            ],
        }

    if etapa == "hectares":
        sessao["hectares"] = mensagem
        sessao["etapa"] = "localizacao"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Perfeito.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
        }

    if etapa == "objetivo_terreno":
        sessao["objetivo_terreno"] = mensagem
        sessao["etapa"] = "localizacao"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Excelente.\n\nQual localização deseja para o terreno?",
            "opcoes": [],
        }

    if etapa == "quartos":
        sessao["quartos"] = mensagem
        if "alugar" in sessao["objetivo"].lower():
            sessao["etapa"] = "mobiliado"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Perfeito.\n\nVocê procura imóvel:",
                "opcoes": ["Mobiliado", "Semimobiliado", "Não importa"],
            }

        sessao["etapa"] = "banheiros"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Perfeito.\n\nQuantos banheiros você precisa?",
            "opcoes": ["1 banheiro", "2 banheiros", "3 banheiros", "4 ou mais"],
        }

    if etapa == "banheiros":
        sessao["banheiros"] = mensagem
        sessao["etapa"] = "vagas_garagem"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Ótimo.\n\nQuantas vagas de garagem você precisa?",
            "opcoes": ["Sem garagem", "1 vaga", "2 vagas", "3 ou mais"],
        }

    if etapa == "vagas_garagem":
        sessao["vagas_garagem"] = mensagem
        sessao["etapa"] = "aceita_pet"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Você possui animais de estimação?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "aceita_pet":
        sessao["aceita_pet"] = mensagem
        if "alugar" in sessao["objetivo"].lower():
            sessao["etapa"] = "mobiliado"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Perfeito.\n\nVocê procura imóvel:",
                "opcoes": ["Mobiliado", "Semimobiliado", "Não importa"],
            }

        sessao["etapa"] = "localizacao"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Excelente.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
        }

    if etapa == "mobiliado":
        sessao["mobiliado"] = mensagem
        sessao["etapa"] = "localizacao"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Excelente.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
        }

    if etapa == "localizacao":
        if not validar_localizacao(mensagem):
            return {
                "mensagem": "Não consegui identificar a localização.\n\n"
                "Pode informar cidade, bairro, região ou referência desejada?",
                "opcoes": [],
            }

        sessao["localizacao"] = mensagem
        sessao["etapa"] = "faixa_valor"
        _salvar_sessao(sessao, session_id, tenant_id)

        if "alugar" in sessao["objetivo"].lower():
            return {
                "mensagem": "Ótimo.\n\nQual faixa de aluguel você procura?",
                "opcoes": [
                    "Até R$ 800",
                    "R$ 800 a R$ 1.500",
                    "R$ 1.500 a R$ 3.000",
                    "R$ 3.000 a R$ 5.000",
                    "Acima de R$ 5.000",
                ],
            }

        return {
            "mensagem": "Excelente.\n\nQual faixa de valor você procura?",
            "opcoes": [
                "Até R$ 150 mil",
                "R$ 150 mil a R$ 300 mil",
                "R$ 300 mil a R$ 500 mil",
                "R$ 500 mil a R$ 1 milhão",
                "Acima de R$ 1 milhão",
            ],
        }

    if etapa == "faixa_valor":
        sessao["faixa_valor"] = mensagem
        sessao["etapa"] = "momento_compra"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Em quanto tempo pretende comprar o imóvel?",
            "opcoes": [
                "Imediatamente",
                "Até 3 meses",
                "Até 6 meses",
                "Acima de 6 meses",
            ],
        }

    if etapa == "momento_compra":
        sessao["momento_compra"] = mensagem
        sessao["etapa"] = "financiamento"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Pretende utilizar financiamento imobiliário?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "financiamento":
        sessao["financiamento"] = mensagem
        sessao["etapa"] = "fgts"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Possui saldo de FGTS disponível?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "fgts":
        sessao["fgts"] = mensagem
        sessao["etapa"] = "renda_familiar"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Qual sua renda familiar aproximada?",
            "opcoes": [
                "Até R$ 2 mil",
                "R$ 2 mil a R$ 4 mil",
                "R$ 4 mil a R$ 8 mil",
                "Acima de R$ 8 mil",
            ],
        }

    if etapa == "renda_familiar":
        sessao["renda_familiar"] = mensagem
        sessao["etapa"] = "whatsapp"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Perfeito.\n\nInforme seu WhatsApp com DDD para continuar.",
            "opcoes": [],
        }

    if etapa == "whatsapp":
        whatsapp = re.sub(r"\D", "", mensagem)
        sessao["whatsapp"] = whatsapp
        perfil = classificar_perfil(sessao)
        score = calcular_score(sessao)

        relatorio = f"""

NOVO LEAD IMOBILIARIO

Perfil:
{perfil}

Objetivo:
{sessao.get("objetivo")}

Tipo imovel:
{sessao.get("tipo_imovel")}

Quartos:
{sessao.get("quartos", "Nao informado")}

Mobiliado:
{sessao.get("mobiliado", "Nao informado")}

Objetivo rural:
{sessao.get("objetivo_rural", "Nao informado")}

Area/Hectares:
{sessao.get("hectares", "Nao informado")}

Localizacao:
{sessao.get("localizacao")}

Faixa valor:
{sessao.get("faixa_valor")}

Permuta:
{"Sim" if sessao.get("permuta") else "Nao"}

WhatsApp cliente:
{whatsapp}

Score Lead:
{score}
"""

        salvar_lead_supabase(sessao)
        enviado = enviar_whatsapp(relatorio, tenant_id)
        _remover_sessao(session_id, tenant_id)

        numero_corretor = obter_numero_corretor(tenant_id)

        if enviado:
            return {
                "mensagem": "Atendimento concluido com sucesso!\n\n"
                "Nossa equipe ja recebeu suas informacoes.\n\n"
                "Em breve um corretor entrara em contato.",
                "link_whatsapp": f"https://wa.me/{numero_corretor}",
            }

        return {
            "mensagem": "O atendimento foi concluido, porem ocorreu uma falha no envio automatico.\n\n"
            "Por favor, clique no botao abaixo para falar diretamente com o corretor.",
            "link_whatsapp": f"https://wa.me/{numero_corretor}",
        }

    return {"mensagem": "Desculpe, nao consegui entender.\n\nTente novamente."}
