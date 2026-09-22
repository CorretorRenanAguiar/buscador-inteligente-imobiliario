import unittest
from unittest.mock import patch

try:
    from backend import chatbot_engine
except ImportError:
    import chatbot_engine


class ChatbotCorretorTest(unittest.IsolatedAsyncioTestCase):
    async def test_sou_corretor_encaminha_sem_qualificar_lead(self):
        session_id = "teste-corretor"
        redis_original = chatbot_engine.redis_client
        chatbot_engine.redis_client = None
        chatbot_engine.MEMORY_SESSIONS.clear()

        try:
            with patch.object(chatbot_engine, "salvar_lead_supabase") as salvar, patch.object(
                chatbot_engine, "enviar_whatsapp"
            ) as enviar, patch.object(
                chatbot_engine, "qualificar_sessao_chatbot"
            ) as qualificar, patch.object(
                chatbot_engine, "calcular_score"
            ) as score, patch.object(
                chatbot_engine,
                "obter_numero_corretor",
                return_value="5511999999999",
            ):
                inicio = await chatbot_engine.processar_chatbot(
                    "iniciar",
                    session_id,
                )
                resposta = await chatbot_engine.processar_chatbot(
                    "Sou corretor",
                    session_id,
                )

            self.assertIn("Qual é o seu objetivo?", inicio["mensagem"])
            self.assertEqual(
                resposta["tipo_atendimento"],
                "corretor_parceiro",
            )
            self.assertEqual(
                resposta["encaminhamento"],
                "atendimento_humano",
            )
            self.assertIn("equipe responsável", resposta["mensagem"])
            self.assertNotIn("score", resposta)
            salvar.assert_not_called()
            enviar.assert_not_called()
            qualificar.assert_not_called()
            score.assert_not_called()
            self.assertEqual(
                chatbot_engine._carregar_sessao(
                    session_id,
                    "RA_IMOBILIARIA",
                ),
                {},
            )
        finally:
            chatbot_engine.MEMORY_SESSIONS.clear()
            chatbot_engine.redis_client = redis_original


if __name__ == "__main__":
    unittest.main()
