import logging
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EVOLUTION_API_URL = os.getenv(
    "EVOLUTION_API_URL",
    "http://localhost:8080",
).rstrip("/")

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

DEFAULT_TENANT_ID = os.getenv(
    "DEFAULT_TENANT_ID",
    "RA_IMOBILIARIA",
).strip().upper()

EVOLUTION_TIMEOUT = int(os.getenv("EVOLUTION_TIMEOUT", "15"))


def _normalizar_numero(numero: Optional[str]) -> str:
    if not numero:
        return ""

    return "".join(caractere for caractere in str(numero) if caractere.isdigit())


def _mascarar_numero(numero: str) -> str:
    if len(numero) <= 4:
        return "****"
    return "*" * (len(numero) - 4) + numero[-4:]


def _configuracao_tenant(tenant_id: Optional[str]) -> Dict[str, str]:
    tenant = (tenant_id or DEFAULT_TENANT_ID).strip().upper()

    tenant_env = "".join(
        caractere if caractere.isalnum() else "_" for caractere in tenant
    )

    instance = os.getenv(
        f"EVOLUTION_INSTANCE_{tenant_env}",
        "",
    ).strip()

    corretor = _normalizar_numero(
        os.getenv(
            f"NUMERO_CORRETOR_{tenant_env}",
            "",
        )
    )

    return {
        "tenant_id": tenant,
        "instance": instance,
        "corretor": corretor,
    }


def obter_configuracao_tenant(tenant_id: Optional[str] = None) -> Dict[str, str]:
    return _configuracao_tenant(tenant_id)


def obter_numero_corretor(tenant_id: Optional[str] = None) -> str:
    return obter_configuracao_tenant(tenant_id).get("corretor", "")


def construir_requisicao_evolution(
    mensagem: str,
    tenant_id: Optional[str] = None,
    destino: Optional[str] = None,
) -> Dict[str, Any]:
    configuracao = _configuracao_tenant(tenant_id)
    numero = _normalizar_numero(destino or configuracao["corretor"])

    return {
        "url": f"{EVOLUTION_API_URL}/message/sendText/{configuracao['instance']}",
        "headers": {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
        },
        "payload": {
            "number": numero,
            "text": mensagem,
        },
    }


def enviar_mensagem_whatsapp(
    mensagem: str,
    tenant_id: Optional[str] = None,
    destino: Optional[str] = None,
) -> Dict[str, Any]:
    if not mensagem or not mensagem.strip():
        return {
            "sucesso": False,
            "erro": "Mensagem vazia.",
        }

    if not EVOLUTION_API_URL:
        return {
            "sucesso": False,
            "erro": "EVOLUTION_API_URL não configurada.",
        }

    if not EVOLUTION_API_KEY:
        return {
            "sucesso": False,
            "erro": "EVOLUTION_API_KEY não configurada.",
        }

    configuracao = _configuracao_tenant(tenant_id)
    instance = configuracao["instance"]
    numero = _normalizar_numero(destino or configuracao["corretor"])

    if not instance:
        logger.error(
            "Instância Evolution não configurada. tenant_id=%s",
            configuracao["tenant_id"],
        )
        return {
            "sucesso": False,
            "erro": (
                "Instância Evolution não configurada "
                f"para o tenant '{configuracao['tenant_id']}'."
            ),
        }

    if not numero:
        logger.error(
            "Número do corretor não configurado. tenant_id=%s",
            configuracao["tenant_id"],
        )
        return {
            "sucesso": False,
            "erro": (
                "Número do corretor não configurado "
                f"para o tenant '{configuracao['tenant_id']}'."
            ),
        }

    requisicao = construir_requisicao_evolution(mensagem, tenant_id, numero)

    try:
        response = requests.post(
            requisicao["url"],
            headers=requisicao["headers"],
            json=requisicao["payload"],
            timeout=EVOLUTION_TIMEOUT,
        )

        response.raise_for_status()

        try:
            resposta_api = response.json()
        except ValueError:
            resposta_api = {
                "status_code": response.status_code,
                "texto": response.text,
            }

        logger.info(
            "Mensagem enviada com sucesso pela Evolution. tenant_id=%s instance=%s destino=%s",
            configuracao["tenant_id"],
            instance,
            _mascarar_numero(numero),
        )

        return {
            "sucesso": True,
            "status_code": response.status_code,
            "tenant_id": configuracao["tenant_id"],
            "instance": instance,
            "resposta": resposta_api,
        }

    except requests.exceptions.Timeout as erro:
        logger.error(
            "Timeout na comunicação com a Evolution. tenant_id=%s instance=%s",
            configuracao["tenant_id"],
            instance,
        )
        return {
            "sucesso": False,
            "tenant_id": configuracao["tenant_id"],
            "instance": instance,
            "erro": "Timeout na comunicação com a Evolution API.",
            "detalhes": str(erro),
        }

    except requests.exceptions.HTTPError as erro:
        status_code = erro.response.status_code if erro.response is not None else None
        corpo = None

        if erro.response is not None:
            try:
                corpo = erro.response.json()
            except ValueError:
                corpo = erro.response.text

        logger.error(
            "Evolution recusou o envio. tenant_id=%s instance=%s status=%s",
            configuracao["tenant_id"],
            instance,
            status_code,
        )

        return {
            "sucesso": False,
            "status_code": status_code,
            "tenant_id": configuracao["tenant_id"],
            "instance": instance,
            "erro": "Evolution API recusou o envio.",
            "detalhes": corpo,
        }

    except requests.exceptions.RequestException as erro:
        logger.error(
            "Falha de conexão com a Evolution. tenant_id=%s instance=%s",
            configuracao["tenant_id"],
            instance,
        )
        return {
            "sucesso": False,
            "tenant_id": configuracao["tenant_id"],
            "instance": instance,
            "erro": "Não foi possível comunicar com a Evolution API.",
            "detalhes": str(erro),
        }

    except Exception as erro:
        logger.exception(
            "Erro inesperado no envio pela Evolution. tenant_id=%s instance=%s",
            configuracao["tenant_id"],
            instance,
        )
        return {
            "sucesso": False,
            "tenant_id": configuracao["tenant_id"],
            "instance": instance,
            "erro": "Erro inesperado no envio do WhatsApp.",
            "detalhes": str(erro),
        }


def verificar_configuracao_evolution(
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    configuracao = _configuracao_tenant(tenant_id)

    return {
        "configurado": bool(
            EVOLUTION_API_URL
            and EVOLUTION_API_KEY
            and configuracao["instance"]
            and configuracao["corretor"]
        ),
        "tenant_id": configuracao["tenant_id"],
        "api_url_configurada": bool(EVOLUTION_API_URL),
        "api_key_configurada": bool(EVOLUTION_API_KEY),
        "instance_configurada": bool(configuracao["instance"]),
        "numero_corretor_configurado": bool(configuracao["corretor"]),
    }
