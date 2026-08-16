import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None


def get_supabase():
    """Retorna uma instância do cliente Supabase. Cria sob demanda.

    Lança RuntimeError se credenciais não estiverem configuradas.
    """
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase URL/KEY não configurados no ambiente")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _supabase_client
