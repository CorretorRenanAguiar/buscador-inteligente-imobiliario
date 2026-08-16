"""
enhanced_filters_kmeans.py

Motor híbrido de qualificação de leads imobiliários.

Pipeline:
1. Normalização dos dados coletados pelo chatbot;
2. Filtros determinísticos de regras de negócio;
3. Score heurístico;
4. Engenharia de atributos;
5. Segmentação por K-Means;
6. Interpretação operacional;
7. Prioridade e recomendação de abordagem.

Observações metodológicas:
- Dados financeiros são DECLARADOS pelo lead.
- Não há consulta de CPF, Serasa, Receita Federal ou fonte externa.
- Ausência de entrada/parcela não reprova o lead, pois o chatbot não coleta
  esses dados nesta etapa.
- O K-Means só atribui cluster quando existe modelo treinado.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
from joblib import dump, load
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "kmeans_model.joblib"
SCALER_PATH = BASE_DIR / "scaler.joblib"
DEFAULT_K = 3


def _normalizar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _numero_da_faixa(texto: Any) -> float:
    texto = _normalizar_texto(texto)
    if not texto:
        return 0.0

    numeros = [
        float(n.replace(".", "").replace(",", "."))
        for n in re.findall(r"\d+(?:[.,]\d+)?", texto)
    ]

    if not numeros:
        return 0.0

    if "milhao" in texto or "milhoes" in texto:
        numeros = [n * 1_000_000 for n in numeros]
    elif "mil" in texto:
        numeros = [n * 1_000 for n in numeros]

    if len(numeros) == 1:
        return numeros[0]

    return sum(numeros[:2]) / 2.0


def _renda_declarada(texto: Any) -> float:
    return _numero_da_faixa(texto)


def _valor_interesse(texto: Any) -> float:
    return _numero_da_faixa(texto)


def _sim(valor: Any) -> bool:
    return _normalizar_texto(valor) in {"sim", "s", "yes", "true", "1"}


def _tipo_imovel(tipo: Any) -> str:
    texto = _normalizar_texto(tipo)

    if texto in {"granja", "chacara", "sitio", "fazenda"}:
        return "rural"

    if texto == "terreno":
        return "terreno"

    return "urbano"


def _operacao(objetivo: Any) -> str:
    texto = _normalizar_texto(objetivo)
    if "alugar" in texto or "locacao" in texto:
        return "locacao"
    return "venda"


def _prazo_score(texto: Any) -> float:
    texto = _normalizar_texto(texto)

    if "imediatamente" in texto:
        return 1.0
    if "3 meses" in texto:
        return 0.85
    if "6 meses" in texto:
        return 0.65
    if "mais de 6" in texto:
        return 0.35

    return 0.50


def _tipo_score(tipo: Any) -> float:
    texto = _normalizar_texto(tipo)

    if texto in {"apartamento", "casa", "kitnet", "cobertura", "lancamento"}:
        return 0.70
    if texto == "terreno":
        return 0.55
    if texto in {"granja", "chacara", "sitio", "fazenda"}:
        return 0.60
    if texto == "imovel comercial":
        return 0.65

    return 0.50


def preparar_lead_do_chatbot(sessao: Dict[str, Any]) -> Dict[str, Any]:
    tipo = _tipo_imovel(sessao.get("tipo_imovel"))
    operacao = _operacao(sessao.get("objetivo"))

    renda = _renda_declarada(sessao.get("renda_familiar"))
    valor_interesse = _valor_interesse(sessao.get("faixa_valor"))

    financiamento = _normalizar_texto(sessao.get("financiamento"))
    fgts = _normalizar_texto(sessao.get("fgts"))

    primeiro_imovel = _sim(sessao.get("primeiro_imovel"))
    permuta = bool(sessao.get("permuta", False))

    prazo_score = _prazo_score(sessao.get("prazo_compra"))
    tipo_score = _tipo_score(sessao.get("tipo_imovel"))

    return {
        "tipo_imovel": tipo,
        "tipo_imovel_original": sessao.get("tipo_imovel"),
        "operacao": operacao,
        "objetivo": sessao.get("objetivo"),
        "uso_imovel": sessao.get("uso_imovel"),
        "primeiro_imovel": primeiro_imovel,
        "localizacao": sessao.get("localizacao"),
        "faixa_valor": sessao.get("faixa_valor"),
        "valor_interesse_estimado": valor_interesse,
        "renda_familiar": sessao.get("renda_familiar"),
        "renda_mensal_declarada": renda,
        "financiamento": financiamento,
        "fgts": fgts,
        "prazo_compra": sessao.get("prazo_compra"),
        "prazo_score": prazo_score,
        "permuta": permuta,
        "paga_diferenca": None,
        "entrada_informada": False,
        "entrada_percentual": 0.0,
        "quartos": sessao.get("quartos"),
        "banheiros": sessao.get("banheiros"),
        "vagas": sessao.get("vagas"),
        "pet": sessao.get("pet"),
        "mobiliado": sessao.get("mobiliado"),
        "objetivo_rural": sessao.get("objetivo_rural"),
        "hectares": sessao.get("hectares"),
        "interacoes": max(1, len(sessao)),
        "tempo_resposta": sessao.get("tempo_resposta", 9999),
        "tipo_score": tipo_score,
        "financiamento_indicado": financiamento == "sim",
        "fgts_indicado": fgts == "sim",
    }


def filtro_deterministico(
    lead: Dict[str, Any],
) -> Tuple[bool, list[str]]:
    """
    Aplica regras determinísticas sem transformar ausência de informação
    em reprovação automática.
    """
    motivos: list[str] = []

    tipo = lead.get("tipo_imovel")
    operacao = lead.get("operacao")
    financiamento = _normalizar_texto(lead.get("financiamento"))

    if operacao == "locacao":
        if lead.get("renda_mensal_declarada", 0) <= 0:
            motivos.append(
                "Renda não informada para validação de locação."
            )

    if tipo == "rural" and financiamento in {
        "sim",
        "mcmv",
        "minha casa minha vida",
        "habitacional",
    }:
        motivos.append(
            "Financiamento habitacional pode não ser aplicável ao imóvel rural; "
            "necessita validação do corretor."
        )

    return True, motivos


def heuristic_score(lead: Dict[str, Any]) -> int:
    """
    Score de sinais observáveis na conversa.
    Não representa capacidade de crédito.
    """
    score = 40

    score += int(float(lead.get("prazo_score", 0.5)) * 25)
    score += int(float(lead.get("tipo_score", 0.5)) * 10)

    if lead.get("renda_mensal_declarada", 0) > 0:
        score += 10

    if lead.get("valor_interesse_estimado", 0) > 0:
        score += 5

    if lead.get("financiamento_indicado"):
        score += 5

    if lead.get("fgts_indicado"):
        score += 3

    if lead.get("primeiro_imovel"):
        score += 2

    interacoes = int(lead.get("interacoes", 1))
    score += min(5, max(0, interacoes - 3))

    return max(0, min(100, score))


def classificar_intencao(lead: Dict[str, Any], score: int) -> str:
    prazo = float(lead.get("prazo_score", 0.5))

    if score >= 75 and prazo >= 0.80:
        return "ALTA"

    if score >= 55 and prazo >= 0.50:
        return "MÉDIA"

    return "BAIXA"


def classificar_maturidade(lead: Dict[str, Any]) -> str:
    campos = [
        lead.get("tipo_imovel"),
        lead.get("localizacao"),
        lead.get("faixa_valor"),
        lead.get("renda_familiar"),
        lead.get("financiamento"),
        lead.get("prazo_compra"),
    ]

    preenchidos = sum(
        1
        for campo in campos
        if campo not in (None, "", "Não informado")
    )

    if preenchidos >= 6:
        return "ALTA"

    if preenchidos >= 4:
        return "MÉDIA"

    return "BAIXA"


def extract_features(lead: Dict[str, Any]) -> np.ndarray:
    renda = float(lead.get("renda_mensal_declarada", 0) or 0)
    valor = float(lead.get("valor_interesse_estimado", 0) or 0)

    renda_valor = renda / valor if valor > 0 else 0.0

    return np.array(
        [
            _tipo_score(lead.get("tipo_imovel_original")),
            1.0 if lead.get("operacao") == "locacao" else 0.0,
            renda_valor,
            float(lead.get("prazo_score", 0.5)),
            1.0 if lead.get("financiamento_indicado") else 0.0,
            1.0 if lead.get("fgts_indicado") else 0.0,
            1.0 if lead.get("primeiro_imovel") else 0.0,
            float(lead.get("interacoes", 1)),
        ],
        dtype=float,
    )


def train_kmeans(
    leads: Iterable[Dict[str, Any]],
    k: int = DEFAULT_K,
    save: bool = True,
):
    leads = list(leads)

    if len(leads) < k:
        raise ValueError(
            f"São necessários pelo menos {k} leads para treinar o K-Means."
        )

    X = np.vstack([extract_features(lead) for lead in leads])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10,
    )

    model.fit(X_scaled)

    if save:
        dump(model, MODEL_PATH)
        dump(scaler, SCALER_PATH)

    return model, scaler


def carregar_modelo():
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        return None, None

    try:
        return load(MODEL_PATH), load(SCALER_PATH)
    except Exception:
        return None, None


def interpretar_cluster(
    cluster: Optional[int],
    score: int,
    intencao: str,
    maturidade: str,
) -> str:
    """
    A interpretação nominal do cluster é provisória.
    O significado definitivo dos clusters deve ser definido após análise
    dos centroides e dos dados reais de treinamento.
    """
    if cluster is None:
        return "Modelo ainda não treinado"

    if intencao == "ALTA" and maturidade == "ALTA":
        return "Perfil de compra estruturada"

    if intencao == "ALTA":
        return "Alta intenção de compra"

    if maturidade == "BAIXA":
        return "Perfil exploratório"

    return f"Cluster {cluster}"


def definir_prioridade(
    score: int,
    intencao: str,
    maturidade: str,
) -> str:
    if score >= 75 and intencao == "ALTA":
        return "ALTA"

    if score >= 55 or intencao == "MÉDIA":
        return "MÉDIA"

    return "BAIXA"


def gerar_recomendacao(
    lead: Dict[str, Any],
    prioridade: str,
    intencao: str,
    maturidade: str,
) -> str:
    financiamento = _normalizar_texto(lead.get("financiamento"))
    prazo = _normalizar_texto(lead.get("prazo_compra"))

    if prioridade == "ALTA":
        if financiamento == "sim":
            return (
                "Recomenda-se contato prioritário e abordagem direcionada "
                "para financiamento, validando com o corretor as condições "
                "reais de aquisição."
            )

        return (
            "Recomenda-se contato prioritário e abordagem personalizada, "
            "explorando as preferências declaradas e a próxima etapa da compra."
        )

    if prioridade == "MÉDIA":
        return (
            "Recomenda-se acompanhamento ativo, com abordagem orientativa "
            "e atualização das informações conforme o lead evoluir."
        )

    if "mais de 6" in prazo:
        return (
            "Recomenda-se nutrição do relacionamento e acompanhamento "
            "periódico, sem priorizar contato comercial imediato."
        )

    return (
        "Recomenda-se acompanhamento e qualificação progressiva antes "
        "de intensificar a abordagem comercial."
    )


def classify_lead(
    lead: Dict[str, Any],
    model=None,
    scaler=None,
) -> Dict[str, Any]:
    aprovado, observacoes_filtro = filtro_deterministico(lead)

    if not aprovado:
        return {
            "status": "DESCARTADO",
            "score": 0,
            "cluster": None,
            "perfil_cluster": "Lead não qualificado",
            "intencao_compra": "BAIXA",
            "maturidade": "BAIXA",
            "prioridade": "BAIXA",
            "recomendacao": "Não priorizar até revisão pelo corretor.",
            "observacoes_filtro": observacoes_filtro,
            "dados_financeiros_declarados": True,
            "capacidade_financeira_verificada": False,
        }

    score = heuristic_score(lead)
    intencao = classificar_intencao(lead, score)
    maturidade = classificar_maturidade(lead)

    cluster = None

    if model is not None and scaler is not None:
        try:
            features = extract_features(lead).reshape(1, -1)
            features_scaled = scaler.transform(features)
            cluster = int(model.predict(features_scaled)[0])
        except Exception:
            cluster = None

    prioridade = definir_prioridade(
        score=score,
        intencao=intencao,
        maturidade=maturidade,
    )

    perfil_cluster = interpretar_cluster(
        cluster=cluster,
        score=score,
        intencao=intencao,
        maturidade=maturidade,
    )

    recomendacao = gerar_recomendacao(
        lead=lead,
        prioridade=prioridade,
        intencao=intencao,
        maturidade=maturidade,
    )

    return {
        "status": "QUALIFICADO",
        "score": score,
        "cluster": cluster,
        "perfil_cluster": perfil_cluster,
        "intencao_compra": intencao,
        "maturidade": maturidade,
        "prioridade": prioridade,
        "recomendacao": recomendacao,
        "observacoes_filtro": observacoes_filtro,
        "dados_financeiros_declarados": True,
        "capacidade_financeira_verificada": False,
    }


def qualificar_sessao_chatbot(
    sessao: Dict[str, Any],
    model=None,
    scaler=None,
) -> Dict[str, Any]:
    lead = preparar_lead_do_chatbot(sessao)

    if model is None or scaler is None:
        model, scaler = carregar_modelo()

    resultado = classify_lead(
        lead=lead,
        model=model,
        scaler=scaler,
    )

    resultado["lead_normalizado"] = lead

    return resultado


if __name__ == "__main__":
    lead_teste = {
        "objetivo": "Comprar imóvel",
        "tipo_imovel": "Apartamento",
        "uso_imovel": "Moradia",
        "primeiro_imovel": "Sim",
        "localizacao": "São Pedro",
        "faixa_valor": "R$ 150 mil a R$ 300 mil",
        "financiamento": "Sim",
        "fgts": "Sim",
        "renda_familiar": "R$ 5.000 a R$ 8.000",
        "prazo_compra": "Imediatamente",
        "quartos": "2 quartos",
        "banheiros": "1 banheiro",
        "vagas": "1 vaga",
        "permuta": False,
    }

    resultado = qualificar_sessao_chatbot(lead_teste)

    print("\n=== TESTE DO MOTOR INTEGRADO ===\n")
    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")
