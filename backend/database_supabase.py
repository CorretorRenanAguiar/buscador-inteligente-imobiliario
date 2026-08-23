# ============================================================
# DATABASE SUPABASE
# Camada oficial de acesso ao Supabase
# ============================================================

from supabase import create_client
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("SUPABASE_URL ou SUPABASE_KEY não configuradas")
            raise ValueError("Variáveis de ambiente Supabase não definidas")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

def salvar_lead_supabase(dados: Dict[str, Any], tenant_id: str = "desenvolvimento") -> Optional[str]:
    try:
        supabase = get_supabase()
        lead_data = {
            "tenant_id": tenant_id,
            "telefone": dados.get("whatsapp", ""),
            "bairro": dados.get("localizacao", ""),
            "faixa_preco_interesse": dados.get("faixa_valor", ""),
            "tipo_interesse": dados.get("tipo_imovel", ""),
            "objetivo": dados.get("objetivo", ""),
            "origem_lead": "CHATBOT",
            "score_lead": dados.get("score", 0),
            "classificacao_lead": dados.get("perfil", ""),
            "tipo_imovel": dados.get("tipo_imovel", ""),
            "quartos": dados.get("quartos", None),
            "banheiros": dados.get("banheiros", None),
            "vagas_garagem": dados.get("vagas_garagem", None),
            "aceita_pet": dados.get("aceita_pet", False),
            "bairro_interesse": dados.get("localizacao", ""),
            "momento_compra": dados.get("momento_compra", ""),
            "financiamento": dados.get("financiamento", ""),
            "fgts": dados.get("fgts", False),
            "renda_familiar": dados.get("renda_familiar", ""),
            "score_completo": dados.get("score", 0),
            "convertido": False,
            "visitou_imovel": False,
            "fechou_negocio": False,
            "sessao_id": dados.get("session_id", ""),
            "observacoes": dados.get("observacoes", ""),
            "cluster_lead": dados.get("cluster", "PENDENTE"),
            "intencao_compra": dados.get("intencao_compra", ""),
            "maturidade_lead": dados.get("maturidade", ""),
            "prioridade_lead": dados.get("prioridade", ""),
            "data_criacao": datetime.utcnow().isoformat(),
        }
        response = supabase.table("leads").insert(lead_data).execute()
        if response.data and len(response.data) > 0:
            lead_id = response.data[0].get("id")
            logger.info(f"Lead {lead_id} salvo no Supabase (tenant: {tenant_id})")
            return lead_id
        return None
    except Exception as e:
        logger.exception(f"Erro ao salvar lead no Supabase: {str(e)}")
        return None

def registrar_evento(lead_id: Optional[str], tipo_evento: str, tenant_id: str = "desenvolvimento", dados_adicionais: Optional[Dict[str, Any]] = None) -> bool:
    try:
        supabase = get_supabase()
        evento_data = {
            "lead_id": lead_id,
            "tipo_evento": tipo_evento,
            "tenant_id": tenant_id,
            "origem_evento": "CHATBOT",
            "data_evento": datetime.utcnow().isoformat(),
            "dados_contexto": dados_adicionais or {},
        }
        response = supabase.table("historico_eventos_lead").insert(evento_data).execute()
        return bool(response.data)
    except Exception as e:
        logger.exception(f"Erro ao registrar evento: {str(e)}")
        return False

def obter_lead_por_sessao(session_id: str, tenant_id: str = "desenvolvimento") -> Optional[Dict[str, Any]]:
    try:
        supabase = get_supabase()
        response = supabase.table("leads").select("*").eq("sessao_id", session_id).eq("tenant_id", tenant_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.exception(f"Erro ao obter lead por sessão: {str(e)}")
        return None

def atualizar_lead(lead_id: str, dados: Dict[str, Any], tenant_id: str = "desenvolvimento") -> bool:
    try:
        supabase = get_supabase()
        response = supabase.table("leads").update(dados).eq("id", lead_id).eq("tenant_id", tenant_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.exception(f"Erro ao atualizar lead: {str(e)}")
        return False

