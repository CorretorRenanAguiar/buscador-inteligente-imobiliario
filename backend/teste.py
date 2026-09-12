from typing import Any, Dict

try:
    import database_supabase as database
except ModuleNotFoundError:
    import backend.database_supabase as database


class FakeResponse:
    def __init__(self, dados):
        self.data = dados


class FakeTable:
    def __init__(self, nome_tabela: str):
        self.nome_tabela = nome_tabela
        self.registro = None

    def insert(self, registro: Dict[str, Any]):
        self.registro = registro
        return self

    def execute(self):
        print()
        print("=" * 70)
        print("SIMULAÇÃO DE INSERT")
        print("=" * 70)
        print(f"Tabela: {self.nome_tabela}")
        print()

        print("PAYLOAD ENVIADO:")
        print("-" * 70)

        for chave, valor in self.registro.items():
            print(f"{chave}: {valor!r}")

        print()
        print("=" * 70)

        return FakeResponse([self.registro])


class FakeSupabase:
    def __init__(self):
        self.tabela = None

    def table(self, nome_tabela: str):
        self.tabela = FakeTable(nome_tabela)
        return self.tabela


fake_supabase = FakeSupabase()


def fake_get_supabase():
    return fake_supabase


database.get_supabase = fake_get_supabase


def verificar_payload(registro: Dict[str, Any]):
    print()
    print("=" * 70)
    print("VALIDAÇÃO DO PAYLOAD")
    print("=" * 70)

    colunas_supabase = {
        "id",
        "telefone",
        "faixa_preco_interesse",
        "tipo_interesse",
        "objetivo",
        "origem_lead",
        "score_lead",
        "classificacao_lead",
        "created_at",
        "tipo_imovel",
        "quartos",
        "banheiros",
        "vagas_garagem",
        "aceita_pet",
        "bairro_interesse",
        "momento_compra",
        "financiamento",
        "fgts",
        "renda_familiar",
        "convertido",
        "visitou_imovel",
        "fechou_negocio",
        "sessao_id",
        "observacoes",
        "cluster_lead",
        "intencao_compra",
        "maturidade_lead",
        "prioridade_lead",
        "composicao_renda",
        "quantidade_participantes",
        "renda_total_declarada",
        "participantes_renda",
        "justificativas_ia",
    }

    colunas_enviadas = set(registro.keys())

    colunas_nao_existentes = colunas_enviadas - colunas_supabase

    colunas_esperadas_nao_enviadas = colunas_supabase - colunas_enviadas

    colunas_esperadas_nao_enviadas.discard("id")
    colunas_esperadas_nao_enviadas.discard("created_at")

    if colunas_nao_existentes:
        print("ERRO: O código está tentando enviar colunas inexistentes:")
        for coluna in sorted(colunas_nao_existentes):
            print(f"  - {coluna}")
    else:
        print("OK: nenhuma coluna inexistente está sendo enviada.")

    if colunas_esperadas_nao_enviadas:
        print()
        print("ATENÇÃO: existem colunas do schema que não estão no payload:")
        for coluna in sorted(colunas_esperadas_nao_enviadas):
            print(f"  - {coluna}")
    else:
        print("OK: todas as colunas graváveis esperadas estão presentes.")

    print()
    print("VALIDAÇÃO DOS TIPOS:")
    print("-" * 70)

    verificacoes = {
        "composicao_renda": bool,
        "quantidade_participantes": int,
        "renda_total_declarada": (int, float),
        "participantes_renda": list,
        "justificativas_ia": list,
        "score_lead": (int, type(None)),
        "cluster_lead": (int, type(None)),
    }

    for campo, tipo_esperado in verificacoes.items():
        valor = registro.get(campo)

        if valor is None:
            print(f"{campo}: NULL")
            continue

        if isinstance(valor, tipo_esperado):
            print(f"{campo}: OK ({type(valor).__name__})")
        else:
            print(f"{campo}: ERRO (recebido {type(valor).__name__})")


def teste_composicao_renda():
    print()
    print("#" * 70)
    print("TESTE 1 - COMPOSIÇÃO DE RENDA")
    print("#" * 70)

    sessao = {
        "whatsapp": "32999999999",
        "localizacao": "São Pedro",
        "faixa_valor": "R$ 400 mil a R$ 500 mil",
        "tipo_imovel": "Casa",
        "objetivo": "Comprar imóvel",
        "quartos": "3 quartos",
        "banheiros": "2 banheiros",
        "vagas": "2 vagas",
        "pet": "Não",
        "prazo_compra": "Até 3 meses",
        "financiamento": "Sim",
        "fgts": "Sim",
        "composicao_renda": "Sim",
        "quantidade_participantes": 3,
        "participantes_renda": [
            {
                "numero": 1,
                "parentesco": "cliente",
                "renda_declarada": "R$ 4.000,00",
            },
            {
                "numero": 2,
                "parentesco": "cônjuge",
                "renda_declarada": "R$ 4.000,00",
            },
            {
                "numero": 3,
                "parentesco": "filho",
                "renda_declarada": "R$ 2.000,00",
            },
        ],
    }

    qualificacao = {
        "status": "QUALIFICADO",
        "score": 82,
        "cluster": None,
        "intencao_compra": "Alta",
        "maturidade": "Pronto",
        "prioridade": "Alta",
        "perfil_cluster": "Lead com alta intenção",
        "dados_financeiros_declarados": True,
        "observacoes_filtro": [],
        "recomendacao": "Encaminhar para atendimento comercial e simulação.",
        "justificativas": [
            "Prazo de compra de até 3 meses.",
            "Financiamento informado.",
            "Possibilidade de composição de renda.",
            "Dados financeiros declarados pelo lead.",
            "Classificação representa apoio à decisão comercial, não aprovação de crédito.",
        ],
    }

    resultado = database.salvar_lead_supabase(
        sessao=sessao,
        qualificacao=qualificacao,
        session_id="TESTE-COMPOSICAO-001",
    )

    print()
    print("RESULTADO:")
    print(resultado)

    registro = fake_supabase.tabela.registro

    verificar_payload(registro)

    print()
    print("=" * 70)
    print("VERIFICAÇÕES ESPECÍFICAS")
    print("=" * 70)

    renda_total = registro.get("renda_total_declarada")

    quantidade = registro.get("quantidade_participantes")

    composicao = registro.get("composicao_renda")

    print(f"Composição de renda: {composicao}")

    print(f"Quantidade de participantes: {quantidade}")

    print(
        f"Renda total declarada: R$ {renda_total:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    if renda_total == 10000:
        print("OK: renda total calculada corretamente.")
    else:
        print("ERRO: renda total deveria ser R$ 10.000,00.")

    if quantidade == 3:
        print("OK: quantidade de participantes correta.")
    else:
        print("ERRO: quantidade de participantes incorreta.")

    if composicao is True:
        print("OK: composição registrada como TRUE.")
    else:
        print("ERRO: composição deveria ser TRUE.")


def teste_sem_composicao():
    print()
    print("#" * 70)
    print("TESTE 2 - RENDA INDIVIDUAL")
    print("#" * 70)

    sessao = {
        "whatsapp": "32988888888",
        "localizacao": "Centro",
        "faixa_valor": "R$ 200 mil a R$ 300 mil",
        "tipo_imovel": "Apartamento",
        "objetivo": "Comprar imóvel",
        "financiamento": "Sim",
        "fgts": "Não",
        "composicao_renda": "Não",
        "renda_familiar": "R$ 5.000,00",
    }

    qualificacao = {
        "status": "QUALIFICADO",
        "score": 60,
        "cluster": None,
        "intencao_compra": "Média",
        "maturidade": "Em avaliação",
        "prioridade": "Média",
        "perfil_cluster": "Lead em avaliação",
        "dados_financeiros_declarados": True,
        "observacoes_filtro": [],
        "recomendacao": "Atendimento comercial.",
        "justificativas": [
            "Renda individual declarada.",
            "Financiamento informado.",
        ],
    }

    resultado = database.salvar_lead_supabase(
        sessao=sessao,
        qualificacao=qualificacao,
        session_id="TESTE-INDIVIDUAL-001",
    )

    print()
    print("RESULTADO:")
    print(resultado)

    registro = fake_supabase.tabela.registro

    verificar_payload(registro)

    print()

    if registro.get("composicao_renda") is False:
        print("OK: composição registrada como FALSE.")
    else:
        print("ERRO: composição deveria ser FALSE.")

    if registro.get("renda_total_declarada") == 5000:
        print("OK: renda individual preservada como renda_total_declarada.")
    else:
        print("ERRO: renda individual não foi persistida corretamente.")


if __name__ == "__main__":
    teste_composicao_renda()
    teste_sem_composicao()

    print()
    print("#" * 70)
    print("SIMULAÇÃO FINALIZADA")
    print("#" * 70)
    print()
    print("Nenhum dado foi enviado ao Supabase.")
