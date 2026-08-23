# ============================================================
# EVOLUTION API
# Evolution API Integration for WhatsApp Communication
# ============================================================

import logging
import os
import requests
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

TENANT_EVOLUTION_CONFIG: Dict[str, Dict[str, str]] = {
    "desenvolvimento": {
        "instance": os.getenv("EVOLUTION_INSTANCE_DEV", ""),
        "phone": os.getenv("EVOLUTION_PHONE_DEV", ""),
        "token": os.getenv("EVOLUTION_TOKEN_DEV", ""),
    },
}

def get_tenant_evolution_config(tenant_id: str) -> Optional[Dict[str, str]]:
    config = TENANT_EVOLUTION_CONFIG.get(tenant_id)
    if not config or not config.get("instance"):
        logger.warning(f"Nenhuma configuração Evolution encontrada para tenant: {tenant_id}")
        return None
    return config

def enviar_relatorio_whatsapp(relatorio: str, tenant_id: str = "desenvolvimento") -> Tuple[bool, str]:
    config = get_tenant_evolution_config(tenant_id)
    if not config:
        return False, f"Tenant {tenant_id} não possui configuração Evolution"
    
    instance = config.get("instance")
    phone = config.get("phone")
    token = config.get("token")
    
    if not all([instance, phone, token]):
        logger.error(f"Configuração incompleta para tenant {tenant_id}")
        return False, "Configuração Evolution incompleta"
    
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{instance}"
        headers = {"Content-Type": "application/json", "apikey": token}
        payload = {"number": phone, "text": relatorio}
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code in [200, 201]:
            logger.info(f"Relatório enviado via Evolution para {phone} (tenant: {tenant_id})")
            return True, "Relatório enviado com sucesso"
        else:
            logger.error(f"Erro Evolution API: {response.status_code}")
            return False, f"Erro ao enviar: {response.status_code}"
    except requests.Timeout:
        logger.error("Timeout ao conectar Evolution API")
        return False, "Timeout na conexão"
    except Exception as e:
        logger.exception(f"Erro ao enviar via Evolution: {str(e)}")
        return False, f"Erro: {str(e)}"

def verificar_evolução_health(tenant_id: str = "desenvolvimento") -> bool:
    config = get_tenant_evolution_config(tenant_id)
    if not config:
        return False
    instance = config.get("instance")
    token = config.get("token")
    if not instance or not token:
        return False
    try:
        url = f"{EVOLUTION_API_URL}/instance/info/{instance}"
        headers = {"apikey": token}
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

