from sklearn.cluster import KMeans

import pandas as pd


def classificar_lead(dados):
    score = 0

    if dados.get("tempo_site", 0) > 300:
        score += 20

    if dados.get("interacoes_chatbot", 0) > 3:
        score += 25

    if dados.get("clicou_whatsapp"):
        score += 40

    if dados.get("retorno_site", 0) > 2:
        score += 20

    if dados.get("pesquisa_detalhada"):
        score += 15

    if score >= 70:
        return "lead_quente"
    if score >= 40:
        return "lead_morno"

    return "lead_frio"


def executar_kmeans(df):
    modelo = KMeans(n_clusters=5, random_state=42)

    features = df[["tempo_total", "interacoes", "retornos", "score"]]
    clusters = modelo.fit_predict(features)
    df["cluster"] = clusters

    return df
