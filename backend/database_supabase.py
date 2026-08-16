import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None


def get_supabase():
    """
    Retorna uma instância reutilizável do cliente Supabase.
    """
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "Supabase URL/KEY não configurados no ambiente"
            )

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


def _inteiro_da_resposta(valor: Any) -> Optional[int]:
    if valor is None:
        return None

    encontrado = __import__("re").search(r"\d+", str(valor))

    if not encontrado:
        return None

    try:
        return int(encontrado.group())
    except ValueError:
        return None


def salvar_lead_supabase(
    sessao: Dict[str, Any],
    qualificacao: Dict[str, Any],
    session_id: str,
) -> Dict[str, Any]:
    """
    Persiste no Supabase os dados declarados pelo lead e o resultado
    da qualificação híbrida.

    O sistema não consulta CPF, Serasa ou qualquer fonte externa de
    crédito. Os dados financeiros são exclusivamente declarados pelo lead.
    """

    lead = qualificacao.get("lead_normalizado", {})

    status = qualificacao.get("status", "QUALIFICADO")
    score = qualificacao.get("score")
    cluster = qualificacao.get("cluster")
    intencao = qualificacao.get("intencao_compra")
    maturidade = qualificacao.get("maturidade")
    prioridade = qualificacao.get("prioridade")
    perfil_cluster = qualificacao.get("perfil_cluster")
    recomendacao = qualificacao.get("recomendacao")
    observacoes_filtro = qualificacao.get("observacoes_filtro", [])

    observacoes = []

    if perfil_cluster:
        observacoes.append(
            f"Perfil do cluster: {perfil_cluster}"
        )

    if qualificacao.get("dados_financeiros_declarados"):
        observacoes.append(
            "Dados financeiros declarados pelo lead; "
            "capacidade financeira não verificada."
        )

    if observacoes_filtro:
        observacoes.extend(
            f"Filtro: {item}"
            for item in observacoes_filtro
        )

    if recomendacao:
        observacoes.append(
            f"Recomendação: {recomendacao}"
        )

    registro = {
        "telefone": _texto(sessao.get("whatsapp")),
        "bairro": _texto(sessao.get("localizacao")),
        "faixa_preco_interesse": _texto(sessao.get("faixa_valor")),
        "tipo_interesse": _texto(sessao.get("tipo_imovel")),
        "objetivo": _texto(sessao.get("objetivo")),
        "origem_lead": "Site",
        "score_lead": score,
        "classificacao_lead": (
            perfil_cluster
            if status == "QUALIFICADO"
            else status
        ),
        "tipo_imovel": _texto(sessao.get("tipo_imovel")),
        "quartos": _inteiro_da_resposta(sessao.get("quartos")),
        "banheiros": _inteiro_da_resposta(sessao.get("banheiros")),
        "vagas_garagem": _inteiro_da_resposta(sessao.get("vagas")),
        "aceita_pet": _texto(sessao.get("pet")),
        "bairro_interesse": _texto(sessao.get("localizacao")),
        "momento_compra": _texto(sessao.get("prazo_compra")),
        "financiamento": _texto(sessao.get("financiamento")),
        "fgts": _texto(sessao.get("fgts")),
        "renda_familiar": _texto(sessao.get("renda_familiar")),
        "score_localizacao": None,
        "score_financeiro": None,
        "score_urgencia": None,
        "score_completo": score,
        "convertido": None,
        "visitou_imovel": None,
        "fechou_negocio": None,
        "sessao_id": _texto(session_id),
        "observacoes": "\n".join(observacoes) if observacoes else None,
        "cluster_lead": cluster,
        "intencao_compra": _texto(intencao),
        "maturidade_lead": _texto(maturidade),
        "prioridade_lead": _texto(prioridade),
    }

    try:
        resposta = (
            get_supabase()
            .table("leads")
            .insert(registro)
            .execute()
        )

        logger.info(
            "Lead salvo no Supabase. sessao_id=%s",
            session_id,
        )

        return {
            "sucesso": True,
            "dados": resposta.data,
        }

    except Exception as erro:
        logger.exception(
            "Erro ao salvar lead no Supabase. sessao_id=%s",
            session_id,
        )

        return {
            "sucesso": False,
            "erro": str(erro),
        }
