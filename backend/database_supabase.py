import logging
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None


def get_supabase():
    """Retorna uma instância reutilizável do cliente Supabase."""
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase URL/KEY não configurados no ambiente")

        _supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )

    return _supabase_client


def _texto(valor: Any) -> Optional[str]:
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    return texto


def _inteiro(valor: Any) -> Optional[int]:
    if valor is None:
        return None

    if isinstance(valor, bool):
        return None

    if isinstance(valor, int):
        return valor

    if isinstance(valor, float):
        return int(valor)

    encontrado = re.search(r"\d+", str(valor))

    if not encontrado:
        return None

    try:
        return int(encontrado.group())
    except (ValueError, TypeError):
        return None


def _numerico(valor: Any) -> Optional[float]:
    """
    Converte valores monetários ou numéricos para float.

    Exemplos aceitos:
    4000
    4000.50
    "R$ 4.000,00"
    "4 mil"
    "R$ 4 mil"
    "10000"
    """

    if valor is None:
        return None

    if isinstance(valor, bool):
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip().lower()

    if not texto:
        return None

    texto = texto.replace("r$", "").replace(" ", "").strip()

    numeros = re.findall(
        r"\d+(?:[.,]\d+)?",
        texto,
    )

    if not numeros:
        return None

    try:
        numero = numeros[0]

        if "." in numero and "," in numero:
            numero = numero.replace(".", "")
            numero = numero.replace(",", ".")

        elif "," in numero:
            numero = numero.replace(",", ".")

        elif "." in numero:
            partes = numero.split(".")

            if len(partes[-1]) == 3:
                numero = numero.replace(".", "")

        valor_numerico = float(numero)

        if "milhão" in texto or "milhao" in texto:
            valor_numerico *= 1_000_000

        elif "mil" in texto and valor_numerico < 1000:
            valor_numerico *= 1000

        return valor_numerico

    except (ValueError, TypeError):
        return None


def _booleano_composicao(valor: Any) -> Optional[bool]:
    if valor is None:
        return None

    if isinstance(valor, bool):
        return valor

    texto = str(valor).strip().lower()

    valores_verdadeiros = {
        "sim",
        "s",
        "true",
        "1",
        "poderei",
        "vou compor",
        "pretendo compor",
        "posso compor",
        "composição",
        "composicao",
    }

    valores_falsos = {
        "não",
        "nao",
        "n",
        "false",
        "0",
        "não vou compor",
        "nao vou compor",
        "somente minha renda",
        "somente minha",
    }

    if texto in valores_verdadeiros:
        return True

    if texto in valores_falsos:
        return False

    if "compor" in texto or "outras pessoas" in texto:
        return True

    if "somente minha renda" in texto:
        return False

    return None


def _obter_renda_participante(
    participante: Dict[str, Any],
) -> Optional[float]:
    """
    Obtém a renda declarada de um participante.

    Aceita diferentes nomes de chave para manter compatibilidade
    com versões anteriores do chatbot.
    """

    candidatos = [
        participante.get("renda_declarada"),
        participante.get("renda"),
        participante.get("renda_mensal"),
        participante.get("valor"),
    ]

    for candidato in candidatos:
        valor = _numerico(candidato)

        if valor is not None:
            return valor

    return None


def _calcular_renda_total_participantes(
    participantes: Any,
) -> Optional[float]:
    """
    Soma as rendas declaradas dos participantes.

    Retorna None quando não houver participantes válidos
    ou quando nenhuma renda puder ser identificada.
    """

    if not isinstance(participantes, list):
        return None

    total = 0.0
    encontrou_renda = False

    for participante in participantes:
        if not isinstance(participante, dict):
            continue

        renda = _obter_renda_participante(participante)

        if renda is None:
            continue

        total += renda
        encontrou_renda = True

    if not encontrou_renda:
        return None

    return total


def _formatar_renda(valor: Optional[float]) -> Optional[str]:
    if valor is None:
        return None

    valor_formatado = (
        f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    return valor_formatado


def _montar_observacoes(
    sessao: Dict[str, Any],
    qualificacao: Dict[str, Any],
) -> Optional[str]:
    """
    Monta um resumo textual para o corretor.

    As justificativas da IA são incluídas aqui para que o relatório
    possa apresentá-las mesmo que não leia diretamente o campo JSONB.
    """

    observacoes: List[str] = []

    perfil_cluster = qualificacao.get("perfil_cluster")

    if perfil_cluster:
        observacoes.append(f"Perfil do cluster: {perfil_cluster}")

    if qualificacao.get("dados_financeiros_declarados"):
        observacoes.append(
            "Dados financeiros declarados pelo lead; "
            "capacidade de crédito não verificada."
        )

    composicao = _booleano_composicao(sessao.get("composicao_renda"))

    if composicao is True:
        quantidade = _inteiro(sessao.get("quantidade_participantes"))

        if quantidade:
            observacoes.append(
                "Possibilidade de composição de renda "
                f"com {quantidade} participante(s)."
            )
        else:
            observacoes.append("Possibilidade de composição de renda identificada.")

    valor_entrada = _texto(sessao.get("valor_entrada"))

    if valor_entrada:
        observacoes.append(f"Valor aproximado de entrada: {valor_entrada}")

    filtros = qualificacao.get(
        "observacoes_filtro",
        [],
    )

    if isinstance(filtros, list):
        for filtro in filtros:
            if filtro:
                observacoes.append(f"Filtro: {filtro}")

    justificativas = qualificacao.get(
        "justificativas",
        [],
    )

    if isinstance(justificativas, list) and justificativas:
        observacoes.append("Justificativas da classificação:")

        for justificativa in justificativas:
            if justificativa:
                observacoes.append(f"- {justificativa}")

    recomendacao = qualificacao.get("recomendacao")

    if recomendacao:
        observacoes.append(f"Recomendação: {recomendacao}")

    observacoes.append(
        "A classificação representa apoio à decisão "
        "comercial e não aprovação de crédito."
    )

    return "\n".join(observacoes) if observacoes else None


def salvar_lead_supabase(
    sessao: Dict[str, Any],
    qualificacao: Dict[str, Any],
    session_id: str,
) -> Dict[str, Any]:
    """
    Persiste no Supabase os dados declarados pelo lead
    e o resultado da qualificação híbrida.

    A qualificação não representa aprovação de crédito.
    """

    status = qualificacao.get(
        "status",
        "QUALIFICADO",
    )

    score = _inteiro(qualificacao.get("score"))

    cluster = _inteiro(qualificacao.get("cluster"))

    intencao = _texto(qualificacao.get("intencao_compra"))

    maturidade = _texto(qualificacao.get("maturidade"))

    prioridade = _texto(qualificacao.get("prioridade"))

    perfil_cluster = _texto(qualificacao.get("perfil_cluster"))

    justificativas = qualificacao.get(
        "justificativas",
        [],
    )

    if not isinstance(justificativas, list):
        justificativas = []

    justificativas_json = justificativas if justificativas else None

    participantes = sessao.get("participantes_renda")

    if not isinstance(participantes, list):
        participantes = None

    if participantes == []:
        participantes = None

    composicao_renda = _booleano_composicao(sessao.get("composicao_renda"))

    quantidade_participantes = _inteiro(sessao.get("quantidade_participantes"))

    if quantidade_participantes is None and participantes:
        quantidade_participantes = len(participantes)

    renda_total_raw = sessao.get("renda_total_declarada")

    renda_familiar_raw = sessao.get("renda_familiar")

    renda_total_num = _numerico(renda_total_raw)

    if renda_total_num is None and participantes:
        renda_total_num = _calcular_renda_total_participantes(participantes)

    if renda_total_num is None:
        renda_total_num = _numerico(renda_familiar_raw)

    if renda_total_num is not None:
        renda_familiar_txt = _formatar_renda(renda_total_num)
    else:
        renda_familiar_txt = _texto(renda_familiar_raw)

    if composicao_renda is True and renda_total_num is not None:
        if not isinstance(
            justificativas,
            list,
        ):
            justificativas = []

        justificativa_composicao = (
            "Renda total declarada considerando "
            "a composição informada: "
            f"{_formatar_renda(renda_total_num)}."
        )

        if justificativa_composicao not in justificativas:
            justificativas.append(justificativa_composicao)

        justificativas_json = justificativas

    observacoes = _montar_observacoes(
        sessao,
        {
            **qualificacao,
            "justificativas": justificativas,
        },
    )

    registro = {
        "telefone": _texto(sessao.get("whatsapp")),
        "sessao_id": _texto(session_id),
        "bairro_interesse": _texto(sessao.get("localizacao")),
        "faixa_preco_interesse": _texto(sessao.get("faixa_valor")),
        "tipo_interesse": _texto(sessao.get("tipo_imovel")),
        "objetivo": _texto(sessao.get("objetivo")),
        "origem_lead": "Site",
        "tipo_imovel": _texto(sessao.get("tipo_imovel")),
        "quartos": _inteiro(sessao.get("quartos")),
        "banheiros": _inteiro(sessao.get("banheiros")),
        "vagas_garagem": _inteiro(sessao.get("vagas")),
        "aceita_pet": _texto(sessao.get("pet")),
        "momento_compra": _texto(sessao.get("prazo_compra")),
        "financiamento": _texto(sessao.get("financiamento")),
        "fgts": _texto(sessao.get("fgts")),
        "renda_familiar": renda_familiar_txt,
        "composicao_renda": composicao_renda,
        "quantidade_participantes": (quantidade_participantes),
        "renda_total_declarada": (renda_total_num),
        "participantes_renda": participantes,
        "score_lead": score,
        "classificacao_lead": (perfil_cluster if status == "QUALIFICADO" else status),
        "cluster_lead": cluster,
        "intencao_compra": intencao,
        "maturidade_lead": maturidade,
        "prioridade_lead": prioridade,
        "justificativas_ia": (justificativas_json),
        "observacoes": observacoes,
        "convertido": None,
        "visitou_imovel": None,
        "fechou_negocio": None,
    }

    try:
        resposta = get_supabase().table("leads").insert(registro).execute()

        logger.info(
            "Lead salvo com sucesso no Supabase. "
            "sessao_id=%s score=%s composicao=%s "
            "renda_total=%s",
            session_id,
            score,
            composicao_renda,
            renda_total_num,
        )

        return {
            "sucesso": True,
            "dados": resposta.data,
        }

    except Exception as erro:
        logger.exception(
            "Erro ao salvar lead no Supabase. " "sessao_id=%s",
            session_id,
        )

        return {
            "sucesso": False,
            "erro": str(erro),
        }
