import unittest
from unittest.mock import Mock, patch

import requests

try:
    from backend import evolution_api
except ImportError:
    import evolution_api


class EvolutionApiTest(unittest.TestCase):
    def setUp(self):
        self.configuracao_original = {
            "url": evolution_api.EVOLUTION_API_URL,
            "key": evolution_api.EVOLUTION_API_KEY,
            "timeout": evolution_api.EVOLUTION_TIMEOUT,
        }
        evolution_api.EVOLUTION_API_URL = "http://localhost:8080"
        evolution_api.EVOLUTION_API_KEY = "chave-de-teste"
        evolution_api.EVOLUTION_TIMEOUT = 3
        self.instance_original = evolution_api.os.environ.get(
            "EVOLUTION_INSTANCE_RA_IMOBILIARIA"
        )
        self.numero_original = evolution_api.os.environ.get(
            "NUMERO_CORRETOR_RA_IMOBILIARIA"
        )
        evolution_api.os.environ["EVOLUTION_INSTANCE_RA_IMOBILIARIA"] = "renan_tcc"
        evolution_api.os.environ["NUMERO_CORRETOR_RA_IMOBILIARIA"] = (
            "+55 (32) 99999-0000"
        )

    def tearDown(self):
        evolution_api.EVOLUTION_API_URL = self.configuracao_original["url"]
        evolution_api.EVOLUTION_API_KEY = self.configuracao_original["key"]
        evolution_api.EVOLUTION_TIMEOUT = self.configuracao_original["timeout"]
        for nome, valor in (
            ("EVOLUTION_INSTANCE_RA_IMOBILIARIA", self.instance_original),
            ("NUMERO_CORRETOR_RA_IMOBILIARIA", self.numero_original),
        ):
            if valor is None:
                evolution_api.os.environ.pop(nome, None)
            else:
                evolution_api.os.environ[nome] = valor

    def test_constroi_requisicao_evolution(self):
        requisicao = evolution_api.construir_requisicao_evolution(
            "Relatório de teste", "RA_IMOBILIARIA"
        )

        self.assertEqual(
            requisicao["url"],
            "http://localhost:8080/message/sendText/renan_tcc",
        )
        self.assertEqual(requisicao["headers"]["apikey"], "chave-de-teste")
        self.assertEqual(
            requisicao["payload"],
            {"number": "5532999990000", "text": "Relatório de teste"},
        )

    def test_envia_com_mock_http(self):
        resposta = Mock()
        resposta.status_code = 201
        resposta.json.return_value = {"status": "PENDING"}
        with patch.object(evolution_api.requests, "post", return_value=resposta) as post:
            resultado = evolution_api.enviar_mensagem_whatsapp("Olá")

        self.assertTrue(resultado["sucesso"])
        post.assert_called_once()

    def test_trata_falha_de_conexao(self):
        with patch.object(
            evolution_api.requests,
            "post",
            side_effect=requests.exceptions.ConnectionError("indisponível"),
        ):
            resultado = evolution_api.enviar_mensagem_whatsapp("Olá")

        self.assertFalse(resultado["sucesso"])
        self.assertEqual(resultado["erro"], "Não foi possível comunicar com a Evolution API.")


if __name__ == "__main__":
    unittest.main()