import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv(
    "KMEANS_MODEL_PATH",
    "backend/models/kmeans_model.joblib",
)

SCALER_PATH = os.getenv(
    "KMEANS_SCALER_PATH",
    "backend/models/kmeans_scaler.joblib",
)

DEFAULT_N_CLUSTERS = int(os.getenv("KMEANS_N_CLUSTERS", "4"))
MIN_TRAINING_SAMPLES = int(os.getenv("KMEANS_MIN_TRAINING_SAMPLES", "10"))

FEATURE_NAMES = [
    "tipo_imovel",
    "operacao",
    "renda_relativa",
    "percentual_entrada",
    "urgencia",
    "composicao_renda",
    "permuta",
    "fgts",
]

_kmeans_model: Optional[KMeans] = None
_kmeans_scaler: Optional[StandardScaler] = None


def _texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _extrair_valor_numerico(valor: Any) -> float:
    if valor is None:
        return 0.0

    texto = str(valor).strip().lower()

    if not texto:
        return 0.0

    if "prefiro não informar" in texto or "prefiro nao informar" in texto:
        return 0.0

    numeros = re.findall(
        r"\d+(?:[.,]\d+)?",
        texto,
    )

    if not numeros:
        return 0.0

    valores = []

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

    texto_milhao = any(
        termo in texto
        for termo in [
            "milhão",
            "milhao",
            "milhões",
            "milhoes",
        ]
    )

    texto_mil = "mil" in texto

    if texto_milhao:
        valores = [valor * 1_000_000 if valor < 1000 else valor for valor in valores]
    elif texto_mil:
        valores = [valor * 1_000 if valor < 1000 else valor for valor in valores]

    if len(valores) == 1:
        return valores[0]

    return sum(valores[:2]) / 2.0


def encode_tipo_imovel(tipo: Any) -> int:
    texto = _texto(tipo).lower()

    if any(
        termo in texto
        for termo in [
            "fazenda",
            "granja",
            "chácara",
            "chacara",
            "sítio",
            "sitio",
            "rural",
        ]
    ):
        return 1

    if "terreno" in texto or "lote" in texto:
        return 2

    if "comercial" in texto:
        return 3

    if "apartamento" in texto or "kitnet" in texto or "cobertura" in texto:
        return 4

    if "casa" in texto:
        return 5

    return 0


def encode_operacao(objetivo: Any) -> int:
    texto = _texto(objetivo).lower()

    if "alugar" in texto or "locação" in texto or "locacao" in texto:
        return 1

    if "invest" in texto:
        return 2

    return 0


def _obter_faixa_valor(lead_dict: Dict[str, Any]) -> float:
    valor = lead_dict.get("faixa_preco_interesse") or lead_dict.get("faixa_valor")
    return _extrair_valor_numerico(valor)


def _obter_renda_total(lead_dict: Dict[str, Any]) -> float:
    renda_total = _extrair_valor_numerico(lead_dict.get("renda_total_declarada"))

    if renda_total > 0:
        return renda_total

    return _extrair_valor_numerico(lead_dict.get("renda_familiar"))


def _obter_valor_entrada(lead_dict: Dict[str, Any]) -> float:
    valor = lead_dict.get("valor_entrada") or lead_dict.get("entrada")
    return _extrair_valor_numerico(valor)


def _obter_prazo(lead_dict: Dict[str, Any]) -> str:
    return _texto(
        lead_dict.get("prazo_compra") or lead_dict.get("momento_compra")
    ).lower()


def _obter_composicao(lead_dict: Dict[str, Any]) -> float:
    composicao = _texto(lead_dict.get("composicao_renda")).lower()

    if composicao in {
        "sim",
        "s",
        "poderei",
        "vou compor",
        "pretendo compor",
    }:
        return 1.0

    participantes = lead_dict.get("participantes_renda")

    if isinstance(participantes, list) and len(participantes) > 1:
        return 1.0

    quantidade = lead_dict.get("quantidade_participantes")

    try:
        if int(quantidade or 0) > 1:
            return 1.0
    except (TypeError, ValueError):
        pass

    return 0.0


def _obter_urgencia(lead_dict: Dict[str, Any]) -> float:
    prazo = _obter_prazo(lead_dict)

    if not prazo:
        return 0.0

    if any(
        termo in prazo
        for termo in [
            "imediata",
            "imediato",
            "imediatamente",
            "agora",
        ]
    ):
        return 3.0

    if "30 dias" in prazo or "1 mês" in prazo or "1 mes" in prazo:
        return 3.0

    if "3 meses" in prazo:
        return 2.0

    if "6 meses" in prazo:
        return 1.5

    if "12 meses" in prazo or "1 ano" in prazo:
        return 1.0

    return 0.5


def _obter_permuta(lead_dict: Dict[str, Any]) -> float:
    valor = lead_dict.get("permuta")

    if isinstance(valor, bool):
        return 1.0 if valor else 0.0

    texto = _texto(valor).lower()

    if texto in {"sim", "s", "true", "1"} or "permuta" in texto:
        return 1.0

    return 0.0


def _obter_fgts(lead_dict: Dict[str, Any]) -> float:
    texto = _texto(lead_dict.get("fgts")).lower()

    if texto in {
        "sim",
        "s",
        "true",
        "1",
        "vou utilizar",
        "pretendo utilizar",
    }:
        return 1.0

    return 0.0


def extract_features_for_kmeans(
    lead_dict: Dict[str, Any],
) -> np.ndarray:
    renda = _obter_renda_total(lead_dict)
    valor_imovel = _obter_faixa_valor(lead_dict)
    valor_entrada = _obter_valor_entrada(lead_dict)

    if valor_imovel > 0:
        entrada_percent = valor_entrada / valor_imovel
    else:
        entrada_percent = 0.0

    operacao_code = encode_operacao(lead_dict.get("objetivo"))
    tipo_code = encode_tipo_imovel(
        lead_dict.get("tipo_imovel") or lead_dict.get("tipo_interesse")
    )

    if operacao_code == 1:
        if renda > 0 and valor_imovel > 0:
            renda_relativa = renda / valor_imovel
        else:
            renda_relativa = 1.0
    else:
        parcela_estimada = valor_imovel * 0.008 if valor_imovel > 0 else 1.0
        if renda > 0:
            renda_relativa = renda / parcela_estimada
        else:
            renda_relativa = 1.0

    urgencia = _obter_urgencia(lead_dict)
    composicao = _obter_composicao(lead_dict)
    permuta = _obter_permuta(lead_dict)
    fgts = _obter_fgts(lead_dict)

    return np.array(
        [
            float(tipo_code),
            float(operacao_code),
            float(np.clip(renda_relativa, 0.0, 20.0)),
            float(np.clip(entrada_percent, 0.0, 1.0)),
            float(urgencia),
            float(composicao),
            float(permuta),
            float(fgts),
        ],
        dtype=float,
    )


def heuristic_lead_score(sessao: Dict[str, Any]) -> int:
    score = 40

    objetivo = _texto(sessao.get("objetivo")).lower()
    prazo = _obter_prazo(sessao)
    valor_entrada = _obter_valor_entrada(sessao)
    faixa_valor = _obter_faixa_valor(sessao)
    composicao = _texto(sessao.get("composicao_renda")).lower()
    whatsapp = _texto(sessao.get("whatsapp"))

    if "invest" in objetivo:
        score += 15
    elif "comprar" in objetivo:
        score += 10
    elif "alugar" in objetivo:
        score += 5

    if any(
        termo in prazo
        for termo in [
            "imediata",
            "imediato",
            "imediatamente",
            "agora",
        ]
    ):
        score += 15
    elif "3 meses" in prazo:
        score += 10
    elif "6 meses" in prazo:
        score += 5

    if valor_entrada >= 100000:
        score += 15
    elif valor_entrada >= 60000:
        score += 10
    elif valor_entrada >= 30000:
        score += 5

    if faixa_valor >= 1000000:
        score += 10
    elif faixa_valor >= 500000:
        score += 5

    if "sim" in composicao or "poderei" in composicao:
        score += 5

    if _obter_permuta(sessao):
        score += 10

    if len(re.sub(r"\D", "", whatsapp)) >= 10:
        score += 5

    return int(np.clip(score, 0, 100))


def _determinar_intencao(sessao: Dict[str, Any]) -> str:
    objetivo = _texto(sessao.get("objetivo")).lower()
    uso = _texto(sessao.get("uso_imovel")).lower()
    tipo = _texto(sessao.get("tipo_imovel")).lower()

    if "invest" in objetivo or "invest" in uso:
        return "INVESTIDOR"

    if "alugar" in objetivo:
        return "LOCAÇÃO"

    if any(
        termo in tipo
        for termo in [
            "fazenda",
            "granja",
            "chácara",
            "chacara",
            "sítio",
            "sitio",
            "rural",
        ]
    ):
        return "RURAL / LAZER"

    if "comprar" in objetivo or "moradia" in uso:
        return "COMPRA RESIDENCIAL"

    return "POTENCIAL COMPRADOR"


def _determinar_maturidade(sessao: Dict[str, Any]) -> str:
    prazo = _obter_prazo(sessao)
    objetivo = _texto(sessao.get("objetivo")).lower()

    if "alugar" in objetivo:
        return "ALTA (LOCAÇÃO)"

    if any(
        termo in prazo
        for termo in [
            "imediata",
            "imediato",
            "imediatamente",
            "agora",
        ]
    ):
        return "ALTA (DECISÃO IMEDIATA)"

    if "3 meses" in prazo:
        return "MÉDIA (CURTO PRAZO)"

    if "6 meses" in prazo:
        return "MÉDIA (MÉDIO PRAZO)"

    if "mais de 6 meses" in prazo:
        return "BAIXA (LONGO PRAZO)"

    return "EM MATURAÇÃO"


def _determinar_prioridade(score: int, maturidade: str) -> str:
    if "ALTA" in maturidade or score >= 75:
        return "ALTA"

    if "MÉDIA" in maturidade or score >= 55:
        return "MÉDIA"

    return "NORMAL"


def _gerar_justificativas(
    sessao: Dict[str, Any],
    score: int,
) -> List[str]:
    justificativas = []

    objetivo = sessao.get("objetivo")
    if objetivo:
        justificativas.append(f"Objetivo do cliente: {objetivo}.")

    prazo = sessao.get("prazo_compra") or sessao.get("momento_compra")

    if prazo:
        justificativas.append(f"Prazo informado para fechamento: {prazo}.")

    composicao = sessao.get("composicao_renda")
    quantidade = sessao.get("quantidade_participantes")

    if composicao:
        texto_composicao = str(composicao).lower()
        if "sim" in texto_composicao or "poderei" in texto_composicao:
            justificativas.append(
                f"Possibilidade de composição de renda identificada com {quantidade or 'múltiplos'} participante(s)."
            )

    renda_total = sessao.get("renda_total_declarada")
    if renda_total:
        justificativas.append(
            f"Renda total declarada considerando a composição informada: {renda_total}."
        )

    valor_entrada = sessao.get("valor_entrada")
    if valor_entrada:
        justificativas.append(f"Valor de entrada declarado: {valor_entrada}.")

    if _obter_permuta(sessao):
        justificativas.append("Lead indicou possibilidade de permuta.")

    if sessao.get("renda_total_declarada") or sessao.get("renda_familiar"):
        justificativas.append(
            "Informação financeira declarada pelo lead; capacidade de crédito não foi verificada."
        )
    else:
        justificativas.append(
            "Informação financeira não declarada; ausência de renda não foi tratada como reprovação."
        )

    justificativas.append(f"Pontuação de triagem comercial: {score}/100.")
    justificativas.append(
        "A classificação representa apoio à decisão comercial e não aprovação de crédito."
    )

    return justificativas


def _gerar_recomendacao(
    sessao: Dict[str, Any],
    prioridade: str,
) -> str:
    if _obter_permuta(sessao):
        return "Contatar o lead prioritariamente para coletar informações sobre a possível permuta."

    composicao = _texto(sessao.get("composicao_renda")).lower()
    if "sim" in composicao or "poderei" in composicao:
        return (
            "Lead apresenta possibilidade de composição de renda. "
            "Encaminhar para análise ou simulação posterior sem interpretar como aprovação."
        )

    if prioridade == "ALTA":
        return "Realizar contato ativo e apresentar opções compatíveis com o perfil."

    objetivo = _texto(sessao.get("objetivo")).lower()
    if "alugar" in objetivo:
        return "Encaminhar opções de locação compatíveis com os dados informados."

    return "Apresentar opções compatíveis com o perfil informado."


def _interpretar_cluster(cluster_id: Optional[int]) -> Optional[str]:
    if cluster_id is None:
        return None
    return f"Segmento comportamental K-Means #{cluster_id}"


def carregar_modelo_kmeans() -> Tuple[Optional[KMeans], Optional[StandardScaler]]:
    global _kmeans_model, _kmeans_scaler

    if _kmeans_model is not None and _kmeans_scaler is not None:
        return _kmeans_model, _kmeans_scaler

    if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)):
        return None, None

    try:
        modelo = load(MODEL_PATH)
        scaler = load(SCALER_PATH)

        features_modelo = getattr(modelo, "n_features_in_", None)
        features_scaler = getattr(scaler, "n_features_in_", None)
        features_esperadas = len(FEATURE_NAMES)

        if (
            features_modelo != features_esperadas
            or features_scaler != features_esperadas
        ):
            logger.warning(
                "Artefatos K-Means incompatíveis com as %d features esperadas.",
                features_esperadas,
            )
            return None, None

        _kmeans_model = modelo
        _kmeans_scaler = scaler
        return _kmeans_model, _kmeans_scaler

    except Exception as erro:
        logger.exception("Erro ao carregar modelo K-Means: %s", erro)
        _kmeans_model = None
        _kmeans_scaler = None
        return None, None


def _validar_dataset(X: np.ndarray, k: int) -> None:
    if X.ndim != 2:
        raise ValueError("Dataset deve possuir duas dimensões.")

    if X.shape[1] != len(FEATURE_NAMES):
        raise ValueError("Quantidade de features incompatível.")

    minimo = max(MIN_TRAINING_SAMPLES, k)
    if X.shape[0] < minimo:
        raise ValueError(
            f"Quantidade insuficiente de amostras para treinamento. Mínimo: {minimo}. Disponíveis: {X.shape[0]}."
        )

    if not np.all(np.isfinite(X)):
        raise ValueError("Dataset contém valores não finitos.")


def train_kmeans(
    df: pd.DataFrame,
    k: int = DEFAULT_N_CLUSTERS,
) -> Tuple[KMeans, StandardScaler]:
    if df.empty:
        raise ValueError("A base de treinamento está vazia.")

    if k < 2:
        raise ValueError("O K-Means precisa de pelo menos 2 clusters.")

    vetores = []
    for _, linha in df.iterrows():
        try:
            vetor = extract_features_for_kmeans(linha.to_dict())
            if np.all(np.isfinite(vetor)):
                vetores.append(vetor)
        except Exception as erro:
            logger.warning("Lead ignorado durante treinamento: %s", erro)

    if not vetores:
        raise ValueError("Nenhum lead válido encontrado.")

    X = np.vstack(vetores)
    _validar_dataset(X, k)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    model = KMeans(n_clusters=k, random_state=42, n_init=20)
    model.fit(Xs)

    diretorio_modelo = os.path.dirname(MODEL_PATH)
    diretorio_scaler = os.path.dirname(SCALER_PATH)

    if diretorio_modelo:
        os.makedirs(diretorio_modelo, exist_ok=True)
    if diretorio_scaler:
        os.makedirs(diretorio_scaler, exist_ok=True)

    dump(model, MODEL_PATH)
    dump(scaler, SCALER_PATH)

    global _kmeans_model, _kmeans_scaler
    _kmeans_model = model
    _kmeans_scaler = scaler

    logger.info(
        "K-Means treinado com sucesso. Amostras: %d. Features: %d. Clusters: %d.",
        X.shape[0],
        X.shape[1],
        k,
    )

    return model, scaler


def treinar_kmeans(
    df: pd.DataFrame,
    k: int = DEFAULT_N_CLUSTERS,
) -> Dict[str, Any]:
    try:
        model, _ = train_kmeans(df, k)
        return {
            "sucesso": True,
            "treinado": True,
            "quantidade_clusters": int(model.n_clusters),
            "quantidade_features": len(FEATURE_NAMES),
            "features": FEATURE_NAMES,
            "modelo_path": MODEL_PATH,
            "scaler_path": SCALER_PATH,
        }
    except Exception as erro:
        logger.exception("Erro no treinamento do K-Means.")
        return {
            "sucesso": False,
            "treinado": False,
            "erro": str(erro),
        }


def qualificar_sessao_chatbot(sessao: Dict[str, Any]) -> Dict[str, Any]:
    score = heuristic_lead_score(sessao)
    intencao = _determinar_intencao(sessao)
    maturidade = _determinar_maturidade(sessao)
    prioridade = _determinar_prioridade(score, maturidade)
    justificativas = _gerar_justificativas(sessao, score)
    recomendacao = _gerar_recomendacao(sessao, prioridade)

    observacoes_filtro = []
    possui_renda = bool(
        sessao.get("renda_total_declarada") or sessao.get("renda_familiar")
    )

    if not possui_renda:
        observacoes_filtro.append(
            "Renda não declarada. Tratada como informação incompleta, não como reprovação."
        )

    composicao = _texto(sessao.get("composicao_renda")).lower()
    if "sim" in composicao or "poderei" in composicao:
        observacoes_filtro.append("Possibilidade de composição de renda identificada.")

    cluster_id = None
    model, scaler = carregar_modelo_kmeans()

    if model is not None and scaler is not None:
        try:
            vetor = extract_features_for_kmeans(sessao).reshape(1, -1)
            vetor_scaled = scaler.transform(vetor)
            cluster_id = int(model.predict(vetor_scaled)[0])
            justificativas.append(
                f"K-Means identificou o segmento comportamental #{cluster_id}."
            )
        except Exception as erro:
            logger.warning("Falha na inferência K-Means: %s", erro)
            justificativas.append(
                "K-Means indisponível para este lead. A classificação permanece baseada nas regras e no score."
            )
    else:
        justificativas.append(
            "Modelo K-Means ainda não treinado ou incompatível com as features atuais."
        )

    perfil_cluster = _interpretar_cluster(cluster_id)
    if perfil_cluster is None:
        perfil_cluster = f"Perfil baseado em regras: {intencao}"

    return {
        "status": "QUALIFICADO",
        "score": score,
        "cluster": cluster_id,
        "perfil_cluster": perfil_cluster,
        "intencao_compra": intencao,
        "maturidade": maturidade,
        "prioridade": prioridade,
        "recomendacao": recomendacao,
        "justificativas": justificativas,
        "observacoes_filtro": observacoes_filtro,
        "dados_financeiros_declarados": possui_renda,
    }


def status_modelo() -> Dict[str, Any]:
    modelo, scaler = carregar_modelo_kmeans()
    return {
        "modelo_existe": os.path.exists(MODEL_PATH),
        "scaler_existe": os.path.exists(SCALER_PATH),
        "modelo_carregado": modelo is not None,
        "scaler_carregado": scaler is not None,
        "model_path": MODEL_PATH,
        "scaler_path": SCALER_PATH,
        "quantidade_features": len(FEATURE_NAMES),
        "features": FEATURE_NAMES,
        "clusters": int(modelo.n_clusters) if modelo is not None else None,
    }
