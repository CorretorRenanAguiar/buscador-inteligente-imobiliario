import logging
import os
from supabase import create_client

logger = logging.getLogger("backend.database")

# =========================================
# CLIENT SUPABASE (lazy)
# =========================================

_supabase_client = None


def get_supabase():
    """Retorna uma instância do cliente Supabase. Cria sob demanda.

    Lança RuntimeError se credenciais não estiverem configuradas.
    """
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        logger.info("Criando cliente Supabase")
        if not supabase_url or not supabase_key:
            logger.error(
                "Variáveis SUPABASE_URL/SUPABASE_KEY não encontradas no ambiente"
            )
            raise RuntimeError("Supabase URL/KEY não configurados no ambiente")
        try:
            _supabase_client = create_client(supabase_url, supabase_key)
        except Exception:
            logger.exception("Falha ao criar cliente Supabase")
            raise
    return _supabase_client
