import copy
import unittest
from unittest.mock import patch

try:
    from backend import chatbot_engine
except ImportError:
    import chatbot_engine


class FakeQuery:
    def __init__(self, client, table_name, operation="select"):
        self.client = client
        self.table_name = table_name
        self.operation = operation
        self.payload = None
        self.filters = {}
        self.order_field = None
        self.order_desc = False

    def select(self, _columns):
        self.operation = "select"
        return self

    def order(self, field, desc=False):
        self.order_field = field
        self.order_desc = desc
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = copy.deepcopy(payload)
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = copy.deepcopy(payload)
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def execute(self):
        records = self.client.records[self.table_name]

        if self.operation == "select":
            result = list(records)
            if self.order_field == "criado_em":
                result.sort(
                    key=lambda item: item.get("criado_em", ""),
                    reverse=self.order_desc,
                )
            return type("Response", (), {"data": result})()

        if self.operation == "insert":
            record = copy.deepcopy(self.payload)
            record["id"] = self.client.next_ids[self.table_name]
            self.client.next_ids[self.table_name] += 1
            records.append(record)
            return type("Response", (), {"data": [record]})()

        if self.operation == "update":
            for record in records:
                if all(record.get(field) == value for field, value in self.filters.items()):
                    record.update(copy.deepcopy(self.payload))
            return type("Response", (), {"data": records})()

        raise AssertionError(f"Operação inesperada: {self.operation}")


class FakeSupabase:
    def __init__(self):
        self.records = {"leads": [], "interacoes_lead": []}
        self.next_ids = {"leads": 100, "interacoes_lead": 500}

    def table(self, table_name):
        return FakeQuery(self, table_name)


class ChatbotHistoricoTest(unittest.TestCase):
    def setUp(self):
        self.supabase_original = chatbot_engine.supabase
        self.supabase = FakeSupabase()
        chatbot_engine.supabase = self.supabase

    def tearDown(self):
        chatbot_engine.supabase = self.supabase_original

    def _sessao(self, telefone="32999990000", **extras):
        sessao = {
            "whatsapp": telefone,
            "objetivo": "Comprar imóvel",
            "tipo_imovel": "Apartamento",
            "localizacao": "Centro",
            "faixa_valor": "R$ 300 mil a R$ 500 mil",
            "momento_compra": "Até 3 meses",
            "quartos": "2 quartos",
            "banheiros": "1 banheiro",
            "vagas_garagem": "1 vaga",
        }
        sessao.update(extras)
        return sessao

    def test_telefone_nao_encontrado_cria_lead_e_interacao(self):
        resultado = chatbot_engine.persistir_lead_e_interacao(
            self._sessao(),
            "sessao-nova",
            {"score": 60},
        )

        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["status_contato"], "novo")
        self.assertEqual(resultado["lead_id"], 100)
        self.assertEqual(len(self.supabase.records["leads"]), 1)
        self.assertEqual(len(self.supabase.records["interacoes_lead"]), 1)
        self.assertEqual(
            self.supabase.records["interacoes_lead"][0]["lead_id"],
            100,
        )

    def test_telefone_encontrado_e_recorrente_sem_criar_segundo_lead(self):
        self.supabase.records["leads"].append(
            {
                "id": 7,
                "telefone": "+55 (32) 99999-0000",
                "criado_em": "2026-01-01T10:00:00",
                "bairro": "Antigo",
            }
        )

        resultado = chatbot_engine.persistir_lead_e_interacao(
            self._sessao("32999990000", localizacao="Novo bairro"),
            "sessao-retorno",
            {"score": 70},
        )

        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["status_contato"], "recorrente")
        self.assertEqual(resultado["lead_id"], 7)
        self.assertEqual(len(self.supabase.records["leads"]), 1)
        self.assertEqual(len(self.supabase.records["interacoes_lead"]), 1)
        self.assertEqual(
            self.supabase.records["leads"][0]["bairro"],
            "Novo bairro",
        )

    def test_dois_atendimentos_do_mesmo_telefone_criam_interacoes_diferentes(self):
        primeiro = chatbot_engine.persistir_lead_e_interacao(
            self._sessao(),
            "sessao-1",
            {"score": 50},
        )
        segundo = chatbot_engine.persistir_lead_e_interacao(
            self._sessao(localizacao="Outro bairro"),
            "sessao-2",
            {"score": 80},
        )

        self.assertEqual(primeiro["lead_id"], segundo["lead_id"])
        self.assertNotEqual(
            primeiro["interacao_id"],
            segundo["interacao_id"],
        )
        self.assertEqual(len(self.supabase.records["leads"]), 1)
        self.assertEqual(len(self.supabase.records["interacoes_lead"]), 2)
        self.assertEqual(
            [item["sessao_id"] for item in self.supabase.records["interacoes_lead"]],
            ["sessao-1", "sessao-2"],
        )

    def test_ausencia_de_telefone_preserva_fluxo_atual(self):
        with patch.object(
            chatbot_engine,
            "salvar_lead_supabase",
            return_value=True,
        ) as salvar:
            resultado = chatbot_engine.persistir_lead_e_interacao(
                self._sessao(""),
                "sessao-sem-telefone",
                {"score": 20},
            )

        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["status_contato"], "novo")
        self.assertIsNone(resultado["interacao_id"])
        salvar.assert_called_once()
        self.assertEqual(self.supabase.records["leads"], [])
        self.assertEqual(self.supabase.records["interacoes_lead"], [])


if __name__ == "__main__":
    unittest.main()
