import json
import os
import re
from typing import Any, Dict, Optional

import redis
from dotenv import load_dotenv
from supabase import create_client

from backend.evolution_api import enviar_mensagem_whatsapp, obter_numero_corretor

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

TIPOS_RURAIS = {"granja", "fazenda", "sítio", "sitio", "chácara", "chacara"}
TIPOS_LOCACAO_RESIDENCIAL = ["Casa", "Apartamento", "Kitnet", "Cobertura"]
TIPOS_LOCACAO_COMERCIAL = [
    "Loja",
    "Sala comercial",
    "Galpão",
    "Casa comercial",
    "Terreno",
    "Imóvel comercial",
]
MODALIDADES_GARANTIA_LOCATICA = [
    "Caução",
    "Seguro-fiança",
    "Cartão de crédito",
    "Fiador",
]


# Validação da localização


def _objetivo_eh_locacao(objetivo: str) -> bool:
    return "alugar" in (objetivo or "").lower()


def _tipo_eh_rural(tipo_imovel: str) -> bool:
    return (tipo_imovel or "").lower() in TIPOS_RURAIS


def _finalidade_locacao_normalizada(valor: str) -> str:
    if "comercial" in (valor or "").lower():
        return "Comercial"
    return "Residencial"


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
                    "uso_imovel": dados.get("uso_imovel"),
                    "primeiro_imovel": dados.get("primeiro_imovel"),
                    "objetivo_rural": dados.get("objetivo_rural"),
                    "hectares": dados.get("hectares"),
                    "finalidade_locacao": dados.get("finalidade_locacao"),
                    "garantia_locatica": dados.get("garantia_locatica"),
                    "caracteristicas_comercial": dados.get("caracteristicas_comercial"),
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
    objetivo = sessao.get("objetivo", "")
    eh_locacao = _objetivo_eh_locacao(objetivo)

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

        if _objetivo_eh_locacao(mensagem):
            sessao["etapa"] = "finalidade_locacao"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Perfeito 😊\n\nVocê procura um imóvel para locação residencial ou comercial?",
                "opcoes": ["Residencial", "Comercial"],
            }

        sessao["etapa"] = "tipo_imovel"
        _salvar_sessao(sessao, session_id, tenant_id)
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

    if etapa == "finalidade_locacao":
        finalidade_locacao = _finalidade_locacao_normalizada(mensagem)
        sessao["finalidade_locacao"] = finalidade_locacao
        sessao["etapa"] = "tipo_imovel"
        _salvar_sessao(sessao, session_id, tenant_id)

        if finalidade_locacao == "Comercial":
            return {
                "mensagem": "Ótimo.\n\nQual tipo de imóvel comercial você procura?",
                "opcoes": TIPOS_LOCACAO_COMERCIAL,
            }

        return {
            "mensagem": "Ótimo.\n\nQual tipo de imóvel residencial você procura?",
            "opcoes": TIPOS_LOCACAO_RESIDENCIAL,
        }

    if etapa == "tipo_imovel":
        sessao["tipo_imovel"] = mensagem
        tipo = mensagem.lower()

        if eh_locacao:
            if sessao.get("finalidade_locacao") == "Comercial":
                sessao["etapa"] = "caracteristicas_comercial"
                _salvar_sessao(sessao, session_id, tenant_id)
                return {
                    "mensagem": "Perfeito.\n\nQuais características são essenciais no imóvel comercial?",
                    "opcoes": [
                        "Loja de rua/vitrine",
                        "Recepção e salas",
                        "Espaço para estoque",
                        "Pé-direito alto",
                        "Não tenho preferência",
                    ],
                }

            sessao["etapa"] = "quartos"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Perfeito.\n\nQuantos quartos você deseja?",
                "opcoes": ["1 quarto", "2 quartos", "3 quartos", "4 quartos ou mais"],
            }

        if _tipo_eh_rural(tipo):
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

    if etapa == "caracteristicas_comercial":
        sessao["caracteristicas_comercial"] = mensagem
        sessao["etapa"] = "localizacao"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Excelente.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
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
        if eh_locacao:
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

        if eh_locacao:
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

        if eh_locacao:
            pergunta_momento = "Em quanto tempo pretende ocupar o imóvel?"
            if sessao.get("finalidade_locacao") == "Residencial":
                pergunta_momento = "Em quanto tempo pretende se mudar?"

            return {
                "mensagem": pergunta_momento,
                "opcoes": [
                    "Imediatamente",
                    "Até 3 meses",
                    "Até 6 meses",
                    "Acima de 6 meses",
                ],
            }

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

        if eh_locacao:
            sessao["etapa"] = "garantia_locatica"
            _salvar_sessao(sessao, session_id, tenant_id)
            return {
                "mensagem": "Qual modalidade de garantia locatícia você pretende usar?",
                "opcoes": MODALIDADES_GARANTIA_LOCATICA,
            }

        sessao["etapa"] = "financiamento"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Pretende utilizar financiamento imobiliário?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "garantia_locatica":
        sessao["garantia_locatica"] = mensagem
        sessao["etapa"] = "whatsapp"
        _salvar_sessao(sessao, session_id, tenant_id)
        return {
            "mensagem": "Perfeito.\n\nInforme seu WhatsApp com DDD para continuar.",
            "opcoes": [],
        }

    if etapa == "financiamento":
        sessao["financiamento"] = mensagem

        if _tipo_eh_rural(sessao.get("tipo_imovel")):
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

        linhas_relatorio = [
            "",
            "NOVO LEAD IMOBILIÁRIO",
            "",
            "Perfil:",
            str(perfil),
            "",
            "Objetivo:",
            str(sessao.get("objetivo", "Não informado")),
            "",
        ]

        if eh_locacao:
            linhas_relatorio.extend(
                [
                    "Finalidade da locação:",
                    str(sessao.get("finalidade_locacao", "Não informado")),
                    "",
                ]
            )

        linhas_relatorio.extend(
            [
                "Tipo de imóvel:",
                str(sessao.get("tipo_imovel", "Não informado")),
                "",
            ]
        )

        if sessao.get("quartos"):
            linhas_relatorio.extend(["Quartos:", str(sessao.get("quartos")), ""])
        if sessao.get("banheiros"):
            linhas_relatorio.extend(["Banheiros:", str(sessao.get("banheiros")), ""])
        if sessao.get("vagas_garagem"):
            linhas_relatorio.extend(["Vagas de garagem:", str(sessao.get("vagas_garagem")), ""])
        if sessao.get("aceita_pet"):
            linhas_relatorio.extend(["Aceita pet:", str(sessao.get("aceita_pet")), ""])
        if sessao.get("mobiliado"):
            linhas_relatorio.extend(["Mobiliado:", str(sessao.get("mobiliado")), ""])
        if sessao.get("caracteristicas_comercial"):
            linhas_relatorio.extend(
                [
                    "Características comerciais:",
                    str(sessao.get("caracteristicas_comercial")),
                    "",
                ]
            )
        if sessao.get("objetivo_rural"):
            linhas_relatorio.extend(
                ["Objetivo rural:", str(sessao.get("objetivo_rural")), ""]
            )
        if sessao.get("hectares"):
            linhas_relatorio.extend(["Área/Hectares:", str(sessao.get("hectares")), ""])

        linhas_relatorio.extend(
            [
                "Localização:",
                str(sessao.get("localizacao", "Não informado")),
                "",
                "Faixa de valor:",
                str(sessao.get("faixa_valor", "Não informado")),
                "",
                "Momento:",
                str(sessao.get("momento_compra", "Não informado")),
                "",
            ]
        )

        if eh_locacao:
            if sessao.get("garantia_locatica"):
                linhas_relatorio.extend(
                    [
                        "Garantia locatícia:",
                        str(sessao.get("garantia_locatica")),
                        "",
                    ]
                )
        else:
            if sessao.get("financiamento"):
                linhas_relatorio.extend(
                    ["Financiamento:", str(sessao.get("financiamento")), ""]
                )
            if sessao.get("fgts"):
                linhas_relatorio.extend(["FGTS:", str(sessao.get("fgts")), ""])
            if sessao.get("renda_familiar"):
                linhas_relatorio.extend(
                    ["Renda familiar:", str(sessao.get("renda_familiar")), ""]
                )

        linhas_relatorio.extend(
            [
                "Permuta:",
                "Sim" if sessao.get("permuta") else "Não",
                "",
                "WhatsApp do cliente:",
                whatsapp,
                "",
                "Score do lead:",
                str(score),
            ]
        )

        relatorio = "\n".join(linhas_relatorio)

        salvar_lead_supabase(sessao)
        enviado = enviar_whatsapp(relatorio, tenant_id)
        _remover_sessao(session_id, tenant_id)

        numero_corretor = obter_numero_corretor(tenant_id)

        if enviado:
            return {
                "mensagem": "Atendimento concluído com sucesso!\n\n"
                "Nossa equipe já recebeu suas informações.\n\n"
                "Em breve um corretor entrará em contato.",
                "link_whatsapp": f"https://wa.me/{numero_corretor}",
            }

        return {
            "mensagem": "O atendimento foi concluído, porém ocorreu uma falha no envio automático.\n\n"
            "Por favor, clique no botão abaixo para falar diretamente com o corretor.",
            "link_whatsapp": f"https://wa.me/{numero_corretor}",
        }

    return {"mensagem": "Desculpe, não consegui entender.\n\nTente novamente."}
