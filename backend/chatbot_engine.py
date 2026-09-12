import logging
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from backend.database_supabase import salvar_lead_supabase
from backend.enhanced_filters_kmeans import qualificar_sessao_chatbot
from backend.evolution_api import enviar_mensagem_whatsapp

load_dotenv()

logger = logging.getLogger(__name__)

PALAVRAS_PERMUTA = [
    "permuta",
    "troca",
    "permutar",
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
    "aqui",
    "lá",
    "la",
    "ali",
    "acolá",
    "acola",
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

sessoes: Dict[str, Dict[str, Any]] = {}


def _normalizar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip().lower()


def _valor_representativo_renda(valor: Any) -> float:
    if valor is None:
        return 0.0

    texto = str(valor).strip().lower()

    if not texto or "prefiro não informar" in texto or "prefiro nao informar" in texto:
        return 0.0

    numeros = re.findall(r"\d+(?:[.,]\d+)?", texto)
    valores: List[float] = []

    for numero in numeros:
        try:
            if "." in numero and "," in numero:
                numero = numero.replace(".", "").replace(",", ".")
            elif "," in numero:
                numero = numero.replace(",", ".")
            elif "." in numero:
                partes = numero.split(".")
                if len(partes[-1]) == 3:
                    numero = numero.replace(".", "")
            valores.append(float(numero))
        except ValueError:
            continue

    if not valores:
        return 0.0

    tem_milhao = (
        "milhão" in texto
        or "milhao" in texto
        or "milhões" in texto
        or "milhoes" in texto
    )
    tem_mil = "mil" in texto

    multiplicador = 1.0
    if tem_milhao and all(v < 1000 for v in valores):
        multiplicador = 1_000_000.0
    elif tem_mil and all(v < 1000 for v in valores):
        multiplicador = 1_000.0

    valores = [v * multiplicador for v in valores]

    if len(valores) == 1:
        return valores[0]

    return sum(valores[:2]) / 2.0


def _calcular_renda_total_composicao(participantes: List[Dict[str, Any]]) -> float:
    total = 0.0
    for participante in participantes:
        renda = participante.get("renda_declarada") or participante.get("renda")
        valor = participante.get("renda_estimada")
        if valor is None:
            valor = _valor_representativo_renda(renda)
        if valor > 0:
            total += valor
    return total


def _formatar_renda(valor: float) -> Optional[str]:
    if valor is None or valor <= 0:
        return None
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def detectar_permuta(texto: str) -> bool:
    texto_normalizado = texto.lower()
    for palavra in PALAVRAS_PERMUTA:
        if palavra in texto_normalizado:
            return True
    return False


def validar_localizacao(texto: str) -> bool:
    texto_normalizado = texto.strip().lower()
    if len(texto_normalizado) < 3:
        return False
    if texto_normalizado in LOCALIZACOES_INVALIDAS:
        return False
    return True


def _resposta_sim(mensagem: str) -> bool:
    texto = mensagem.strip().lower()
    return texto in ["sim", "s", "sim.", "sim!", "quero", "pretendo"]


def _resposta_nao(mensagem: str) -> bool:
    texto = mensagem.strip().lower()
    return texto in ["não", "nao", "n", "não.", "nao.", "não!", "nao!"]


def _extrair_quantidade(mensagem: str) -> Optional[int]:
    encontrado = re.search(r"\d+", mensagem)
    if encontrado:
        try:
            quantidade = int(encontrado.group())
            if quantidade > 0:
                return quantidade
        except ValueError:
            pass

    texto = mensagem.strip().lower()
    if "mais de 4" in texto:
        return 5
    if "duas" in texto:
        return 2
    if "três" in texto or "tres" in texto:
        return 3
    if "quatro" in texto:
        return 4
    return None


def criar_relatorio(
    sessao: Dict[str, Any],
    whatsapp: str,
    qualificacao: Dict[str, Any],
) -> str:
    score = qualificacao.get("score", 0)
    cluster = qualificacao.get("cluster")
    perfil_cluster = qualificacao.get("perfil_cluster", "Modelo ainda não treinado")
    intencao = qualificacao.get("intencao_compra", "NÃO CLASSIFICADA")
    maturidade = qualificacao.get("maturidade", "NÃO CLASSIFICADA")
    prioridade = qualificacao.get("prioridade", "NÃO CLASSIFICADA")
    recomendacao = qualificacao.get(
        "recomendacao", "Realizar atendimento personalizado."
    )
    justificativas = qualificacao.get("justificativas", [])
    observacoes = qualificacao.get("observacoes_filtro", [])

    cluster_texto = (
        str(cluster)
        if cluster is not None
        else "Ainda não disponível — modelo K-Means aguardando treinamento"
    )

    justificativas_texto = (
        "\n".join(f"- {item}" for item in justificativas)
        if justificativas
        else "- Nenhuma justificativa adicional registrada."
    )

    observacoes_texto = (
        "\n".join(f"- {item}" for item in observacoes)
        if observacoes
        else "- Nenhuma observação adicional."
    )

    participantes = sessao.get("participantes_renda", [])
    if participantes:
        participantes_texto = "\n".join(
            f"- Participante {p.get('numero', idx)}: {p.get('renda_declarada', p.get('renda', 'Não informado'))}"
            for idx, p in enumerate(participantes, start=1)
        )
    else:
        participantes_texto = "- Nenhum participante adicional informado."

    composicao = sessao.get("composicao_renda", "Não informada")
    renda_total = sessao.get(
        "renda_total_declarada",
        sessao.get("renda_familiar", "Não informado"),
    )

    if isinstance(renda_total, (int, float)) and renda_total > 0:
        renda_total_formatada = _formatar_renda(renda_total)
    else:
        renda_total_formatada = str(renda_total)

    return f"""NOVO LEAD IMOBILIÁRIO

QUALIFICAÇÃO DO LEAD

Prioridade: {prioridade}

Score: {score}/100

Cluster K-Means:
{cluster_texto}

Perfil do cluster:
{perfil_cluster}

Intenção de compra:
{intencao}

Maturidade da decisão:
{maturidade}

PERFIL IMOBILIÁRIO

Objetivo:
{sessao.get('objetivo', 'Não informado')}

Tipo de imóvel:
{sessao.get('tipo_imovel', 'Não informado')}

Uso do imóvel:
{sessao.get('uso_imovel', 'Não informado')}

Primeiro imóvel:
{sessao.get('primeiro_imovel', 'Não informado')}

Quartos:
{sessao.get('quartos', 'Não informado')}

Banheiros:
{sessao.get('banheiros', 'Não informado')}

Vagas:
{sessao.get('vagas', 'Não informado')}

Possui pet:
{sessao.get('pet', 'Não informado')}

Mobiliado:
{sessao.get('mobiliado', 'Não informado')}

Objetivo rural:
{sessao.get('objetivo_rural', 'Não informado')}

Área/Hectares:
{sessao.get('hectares', 'Não informado')}

Localização:
{sessao.get('localizacao', 'Não informado')}

PERFIL FINANCEIRO DECLARADO

Faixa de valor:
{sessao.get('faixa_valor', 'Não informado')}

Financiamento:
{sessao.get('financiamento', 'Não informado')}

Composição de renda:
{composicao}

Quantidade de participantes:
{sessao.get('quantidade_participantes', 'Não informado')}

Participantes e rendas:
{participantes_texto}

Renda total declarada/estimada:
{renda_total_formatada}

FGTS:
{sessao.get('fgts', 'Não informado')}

Valor aproximado de entrada:
{sessao.get('valor_entrada', 'Não informado')}

Prazo de compra:
{sessao.get('prazo_compra', 'Não informado')}

Permuta:
{'Sim' if sessao.get('permuta') else 'Não'}

CONTATO

WhatsApp:
{whatsapp}

JUSTIFICATIVAS DA CLASSIFICAÇÃO

{justificativas_texto}

RECOMENDAÇÃO DE ABORDAGEM

{recomendacao}

OBSERVAÇÕES DOS FILTROS

{observacoes_texto}

ATENÇÃO

Os dados financeiros foram declarados pelo próprio lead.

Quando houver faixas de renda, a renda total estimada utiliza um valor representativo da faixa informada exclusivamente para fins de análise e segmentação.

A renda declarada não representa aprovação de financiamento, capacidade de crédito comprovada ou análise bancária.

Quando houver composição de renda, o sistema identifica apenas uma possibilidade declarada de composição e recomenda análise ou simulação posterior pelo corretor e pela instituição financeira.

A classificação do sistema representa apoio à decisão comercial, não aprovação de crédito.

O sistema não realiza consulta de CPF, SPC, Serasa ou qualquer verificação externa de crédito.""".strip()


async def processar_chatbot(
    mensagem: str,
    session_id: str,
    tenant_id: str = "desenvolvimento",
) -> Dict[str, Any]:
    mensagem = mensagem.strip()

    if not mensagem:
        return {"mensagem": "Por favor, envie uma mensagem para continuarmos."}

    if session_id not in sessoes:
        sessoes[session_id] = {
            "etapa": "objetivo",
            "tenant_id": tenant_id,
        }
        return {
            "mensagem": (
                "Olá!\n\n"
                "Sou a assistente virtual imobiliária de Renan Aguiar.\n\n"
                "Vou entender rapidamente o perfil do imóvel que você procura.\n\n"
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

    if "tenant_id" not in sessao and tenant_id:
        sessao["tenant_id"] = tenant_id

    etapa = sessao.get("etapa", "objetivo")

    if detectar_permuta(mensagem):
        sessao["permuta"] = True
        sessao["etapa"] = "whatsapp_permuta"
        return {
            "mensagem": (
                "Entendi.\n\n"
                "Casos de permuta exigem análise personalizada.\n\n"
                "Informe seu WhatsApp com DDD para que um corretor especializado entre em contato."
            ),
            "opcoes": [],
        }

    if etapa == "objetivo":
        sessao["objetivo"] = mensagem
        sessao["etapa"] = "tipo_imovel"

        if "alugar" in _normalizar_texto(mensagem):
            return {
                "mensagem": "Perfeito.\n\nQual tipo de imóvel você procura?",
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
            "mensagem": "Perfeito.\n\nQual tipo de imóvel você procura?",
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
        tipo = _normalizar_texto(mensagem)

        if tipo in ["granja", "chácara", "chacara", "fazenda", "sítio", "sitio"]:
            sessao["etapa"] = "objetivo_rural"
            return {
                "mensagem": "Excelente.\n\nQual o objetivo principal do imóvel?",
                "opcoes": [
                    "Lazer",
                    "Moradia",
                    "Produção rural",
                    "Investimento",
                ],
            }

        if tipo == "terreno":
            sessao["etapa"] = "objetivo_terreno"
            return {
                "mensagem": "Perfeito.\n\nQual a finalidade do terreno?",
                "opcoes": [
                    "Construir para morar",
                    "Investimento",
                    "Construção comercial",
                ],
            }

        sessao["etapa"] = "uso_imovel"
        return {
            "mensagem": "Qual será o principal uso do imóvel?",
            "opcoes": [
                "Moradia",
                "Investimento",
                "Moradia e investimento",
            ],
        }

    if etapa == "uso_imovel":
        sessao["uso_imovel"] = mensagem
        sessao["etapa"] = "primeiro_imovel"
        return {
            "mensagem": "Será seu primeiro imóvel?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "primeiro_imovel":
        sessao["primeiro_imovel"] = mensagem
        sessao["etapa"] = "quartos"
        return {
            "mensagem": "Quantos quartos você deseja?",
            "opcoes": [
                "1 quarto",
                "2 quartos",
                "3 quartos",
                "4 quartos ou mais",
            ],
        }

    if etapa == "objetivo_rural":
        sessao["objetivo_rural"] = mensagem
        sessao["etapa"] = "hectares"
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
        return {
            "mensagem": "Perfeito.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
        }

    if etapa == "objetivo_terreno":
        sessao["objetivo_terreno"] = mensagem
        sessao["etapa"] = "localizacao"
        return {
            "mensagem": "Excelente.\n\nQual localização deseja para o terreno?",
            "opcoes": [],
        }

    if etapa == "quartos":
        sessao["quartos"] = mensagem
        sessao["etapa"] = "banheiros"
        return {
            "mensagem": "Perfeito.\n\nQuantos banheiros você deseja?",
            "opcoes": [
                "1 banheiro",
                "2 banheiros",
                "3 banheiros",
                "4 ou mais",
            ],
        }

    if etapa == "banheiros":
        sessao["banheiros"] = mensagem
        sessao["etapa"] = "vagas"
        return {
            "mensagem": "Ótimo.\n\nQuantas vagas de garagem você precisa?",
            "opcoes": [
                "Sem garagem",
                "1 vaga",
                "2 vagas",
                "3 ou mais",
            ],
        }

    if etapa == "vagas":
        sessao["vagas"] = mensagem

        if "alugar" in _normalizar_texto(sessao.get("objetivo")):
            sessao["etapa"] = "mobiliado"
            return {
                "mensagem": "Perfeito.\n\nVocê procura imóvel:",
                "opcoes": [
                    "Mobiliado",
                    "Semimobiliado",
                    "Não importa",
                ],
            }

        sessao["etapa"] = "localizacao"
        return {
            "mensagem": "Perfeito.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
        }

    if etapa == "mobiliado":
        sessao["mobiliado"] = mensagem
        sessao["etapa"] = "pet"
        return {
            "mensagem": "Você possui animais de estimação?",
            "opcoes": ["Sim", "Não"],
        }

    if etapa == "pet":
        sessao["pet"] = mensagem
        sessao["etapa"] = "localizacao"
        return {
            "mensagem": "Excelente.\n\nQual localização deseja para o imóvel?",
            "opcoes": [],
        }

    if etapa == "localizacao":
        if not validar_localizacao(mensagem):
            return {
                "mensagem": (
                    "Não consegui identificar a localização.\n\n"
                    "Pode informar a cidade, bairro, região ou referência desejada?"
                ),
                "opcoes": [],
            }

        sessao["localizacao"] = mensagem
        sessao["etapa"] = "faixa_valor"

        if "alugar" in _normalizar_texto(sessao.get("objetivo")):
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

        if "alugar" in _normalizar_texto(sessao.get("objetivo")):
            sessao["etapa"] = "whatsapp"
            return {
                "mensagem": "Perfeito.\n\nInforme seu WhatsApp com DDD para continuar.",
                "opcoes": [],
            }

        sessao["etapa"] = "financiamento"
        return {
            "mensagem": "Você pretende utilizar financiamento bancário para essa compra?",
            "opcoes": [
                "Sim",
                "Não",
                "Ainda vou verificar",
            ],
        }

    if etapa == "financiamento":
        sessao["financiamento"] = mensagem

        if _resposta_sim(mensagem):
            sessao["etapa"] = "composicao_renda"
            return {
                "mensagem": (
                    "Para essa compra, você pretende utilizar somente a sua renda "
                    "ou poderá contar com a renda de outras pessoas?"
                ),
                "opcoes": [
                    "Somente minha renda",
                    "Poderei contar com a renda de outras pessoas",
                    "Ainda não sei",
                ],
            }

        sessao["composicao_renda"] = "Não"
        sessao["quantidade_participantes"] = 1
        sessao["etapa"] = "renda_propria"
        return {
            "mensagem": "Qual é a sua renda mensal aproximada?",
            "opcoes": [
                "Até R$ 3.000",
                "R$ 3.000 a R$ 5.000",
                "R$ 5.000 a R$ 8.000",
                "Acima de R$ 8.000",
                "Prefiro não informar",
            ],
        }

    if etapa == "composicao_renda":
        texto = _normalizar_texto(mensagem)

        if "poderei" in texto or "outras" in texto or _resposta_sim(mensagem):
            sessao["composicao_renda"] = "Sim"
            sessao["etapa"] = "quantidade_participantes"
            return {
                "mensagem": "Entendi.\n\nQuantas pessoas poderão participar da composição de renda?",
                "opcoes": [
                    "2 pessoas",
                    "3 pessoas",
                    "4 pessoas",
                    "Mais de 4 pessoas",
                ],
            }

        if "ainda" in texto:
            sessao["composicao_renda"] = "Ainda não sei"
            sessao["quantidade_participantes"] = 1
            sessao["etapa"] = "renda_propria"
            return {
                "mensagem": "Sem problema.\n\nPara uma primeira qualificação, qual é a sua renda mensal aproximada?",
                "opcoes": [
                    "Até R$ 3.000",
                    "R$ 3.000 a R$ 5.000",
                    "R$ 5.000 a R$ 8.000",
                    "Acima de R$ 8.000",
                    "Prefiro não informar",
                ],
            }

        sessao["composicao_renda"] = "Não"
        sessao["quantidade_participantes"] = 1
        sessao["etapa"] = "renda_propria"
        return {
            "mensagem": "Qual é a sua renda mensal aproximada?",
            "opcoes": [
                "Até R$ 3.000",
                "R$ 3.000 a R$ 5.000",
                "R$ 5.000 a R$ 8.000",
                "Acima de R$ 8.000",
                "Prefiro não informar",
            ],
        }

    if etapa == "quantidade_participantes":
        quantidade = _extrair_quantidade(mensagem)

        if quantidade is None:
            return {
                "mensagem": "Pode informar apenas a quantidade de pessoas que poderão participar da composição de renda?",
                "opcoes": [
                    "2 pessoas",
                    "3 pessoas",
                    "4 pessoas",
                    "Mais de 4 pessoas",
                ],
            }

        if quantidade < 2:
            return {
                "mensagem": "Como estamos falando de composição de renda, informe pelo menos 2 participantes.",
                "opcoes": [
                    "2 pessoas",
                    "3 pessoas",
                    "4 pessoas",
                    "Mais de 4 pessoas",
                ],
            }

        if quantidade > 10:
            return {
                "mensagem": "Para essa primeira qualificação, informe uma quantidade de até 10 participantes.",
                "opcoes": [
                    "2 pessoas",
                    "3 pessoas",
                    "4 pessoas",
                    "Mais de 4 pessoas",
                ],
            }

        sessao["quantidade_participantes"] = quantidade
        sessao["participantes_renda"] = []
        sessao["participante_atual"] = 1
        sessao["etapa"] = "renda_participante"

        return {
            "mensagem": f"Qual é a renda mensal aproximada da pessoa 1 de {quantidade}?",
            "opcoes": [
                "Até R$ 2.000",
                "R$ 2.000 a R$ 4.000",
                "R$ 4.000 a R$ 6.000",
                "R$ 6.000 a R$ 10.000",
                "Acima de R$ 10.000",
                "Prefiro não informar",
            ],
        }

    if etapa == "renda_participante":
        participante_atual = int(sessao.get("participante_atual", 1))
        quantidade_participantes = int(sessao.get("quantidade_participantes", 1))
        renda_informada = mensagem.strip()
        valor_renda = _valor_representativo_renda(renda_informada)

        participantes_renda = sessao.get("participantes_renda", [])
        participantes_renda.append(
            {
                "numero": participante_atual,
                "renda": renda_informada,
                "renda_declarada": renda_informada,
                "renda_estimada": valor_renda,
            }
        )
        sessao["participantes_renda"] = participantes_renda

        renda_total = sum(p.get("renda_estimada") or 0.0 for p in participantes_renda)
        sessao["renda_total_declarada"] = renda_total
        sessao["renda_familiar"] = renda_informada

        if participante_atual < quantidade_participantes:
            proximo_participante = participante_atual + 1
            sessao["participante_atual"] = proximo_participante

            return {
                "mensagem": f"Qual é a renda mensal aproximada da pessoa {proximo_participante} de {quantidade_participantes}?",
                "opcoes": [
                    "Até R$ 2.000",
                    "R$ 2.000 a R$ 4.000",
                    "R$ 4.000 a R$ 6.000",
                    "R$ 6.000 a R$ 10.000",
                    "Acima de R$ 10.000",
                    "Prefiro não informar",
                ],
            }

        sessao["etapa"] = "fgts"
        return {
            "mensagem": "Obrigado. A composição de renda foi registrada.\n\nAgora, pretende utilizar FGTS?",
            "opcoes": [
                "Sim",
                "Não",
                "Não sei",
            ],
        }

    if etapa == "renda_propria":
        renda_informada = mensagem.strip()
        valor_renda = _valor_representativo_renda(renda_informada)

        sessao["renda_familiar"] = renda_informada
        sessao["renda_total_declarada"] = valor_renda
        sessao["quantidade_participantes"] = 1
        sessao["participantes_renda"] = [
            {
                "numero": 1,
                "renda": renda_informada,
                "renda_declarada": renda_informada,
                "renda_estimada": valor_renda,
            }
        ]
        sessao["etapa"] = "fgts"

        return {
            "mensagem": "Pretende utilizar FGTS?",
            "opcoes": [
                "Sim",
                "Não",
                "Não sei",
            ],
        }

    if etapa == "fgts":
        sessao["fgts"] = mensagem
        sessao["etapa"] = "valor_entrada"
        return {
            "mensagem": "Qual é o valor aproximado que você pretende utilizar como entrada?",
            "opcoes": [
                "Ainda não sei",
                "Até R$ 30 mil",
                "R$ 30 mil a R$ 60 mil",
                "R$ 60 mil a R$ 100 mil",
                "Acima de R$ 100 mil",
            ],
        }

    if etapa == "valor_entrada":
        sessao["valor_entrada"] = mensagem
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

    if etapa == "prazo_compra":
        sessao["prazo_compra"] = mensagem
        sessao["etapa"] = "whatsapp"
        return {
            "mensagem": "Perfeito.\n\nInforme seu WhatsApp com DDD para continuar.",
            "opcoes": [],
        }

    if etapa in ["whatsapp", "whatsapp_permuta"]:
        whatsapp = re.sub(r"\D", "", mensagem)

        if len(whatsapp) < 10:
            return {
                "mensagem": "Não consegui identificar um número de WhatsApp válido.\n\nInforme o número com DDD.",
                "opcoes": [],
            }

        sessao["whatsapp"] = whatsapp

        try:
            qualificacao = qualificar_sessao_chatbot(sessao)
        except Exception as erro:
            logger.exception("Erro na qualificação do lead. session_id=%s", session_id)
            del sessoes[session_id]
            return {
                "mensagem": "Não foi possível concluir a qualificação neste momento.",
                "erro": str(erro),
            }

        persistencia = salvar_lead_supabase(
            sessao=sessao,
            qualificacao=qualificacao,
            session_id=session_id,
        )

        if not persistencia.get("sucesso"):
            logger.error(
                "Falha ao salvar lead no Supabase. session_id=%s erro=%s",
                session_id,
                persistencia.get("erro"),
            )
            del sessoes[session_id]
            return {
                "mensagem": "Não foi possível concluir o registro do seu atendimento neste momento.\n\nPor favor, tente novamente.",
                "qualificacao": {
                    "score": qualificacao.get("score"),
                    "cluster": qualificacao.get("cluster"),
                    "intencao_compra": qualificacao.get("intencao_compra"),
                    "maturidade": qualificacao.get("maturidade"),
                    "prioridade": qualificacao.get("prioridade"),
                    "perfil_cluster": qualificacao.get("perfil_cluster"),
                    "justificativas": qualificacao.get("justificativas", []),
                },
            }

        relatorio = criar_relatorio(
            sessao=sessao,
            whatsapp=whatsapp,
            qualificacao=qualificacao,
        )

        resultado_whatsapp = enviar_mensagem_whatsapp(
            mensagem=relatorio,
            tenant_id=sessao.get("tenant_id", "desenvolvimento"),
        )

        if resultado_whatsapp.get("sucesso") is True:
            logger.info(
                "Relatório do lead enviado ao WhatsApp. session_id=%s tenant_id=%s",
                session_id,
                sessao.get("tenant_id", "desenvolvimento"),
            )
            mensagem_final = (
                "Atendimento concluído com sucesso!\n\n"
                "Suas informações foram qualificadas e encaminhadas à nossa equipe.\n\n"
                "Em breve um corretor entrará em contato."
            )
        else:
            logger.error(
                "Falha no envio do relatório ao WhatsApp. session_id=%s erro=%s",
                session_id,
                resultado_whatsapp.get("erro"),
            )
            mensagem_final = (
                "Atendimento concluído com sucesso!\n\n"
                "Suas informações foram registradas em nossa base de atendimento.\n\n"
                "Nossa equipe realizará o acompanhamento."
            )

        resposta = {
            "mensagem": mensagem_final,
            "qualificacao": {
                "score": qualificacao.get("score"),
                "cluster": qualificacao.get("cluster"),
                "intencao_compra": qualificacao.get("intencao_compra"),
                "maturidade": qualificacao.get("maturidade"),
                "prioridade": qualificacao.get("prioridade"),
                "perfil_cluster": qualificacao.get("perfil_cluster"),
                "justificativas": qualificacao.get("justificativas", []),
            },
            "persistencia": {
                "sucesso": persistencia.get("sucesso"),
            },
            "whatsapp_corretor": {
                "sucesso": resultado_whatsapp.get("sucesso"),
            },
        }

        del sessoes[session_id]
        return resposta

    return {
        "mensagem": "Desculpe, não consegui entender.\n\nTente novamente.",
        "opcoes": [],
    }
