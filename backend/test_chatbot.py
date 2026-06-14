import asyncio
from chatbot_engine import processar_chatbot

async def run_test():
    session_id = "test123"
    # cria a sessão inicial (simula usuário que inicia conversa)
    resp = await processar_chatbot("", session_id)
    print("INIT OUTPUT:")
    print(resp)
    print("-"*60)

    steps = [
        "Comprar imóvel",            # objetivo
        "Apartamento",               # tipo_imovel
        "Moradia",                   # uso_imovel
        "Sim",                       # primeiro_imovel
        "2 quartos",                 # quartos
        "1 banheiro",                # banheiros
        "1 vaga",                    # vagas
        "São Paulo",                 # localizacao
        "R$ 300 mil a R$ 500 mil",   # faixa_valor
        "Sim",                       # financiamento
        "Não",                       # fgts
        "R$ 5.000 a R$ 8.000",       # renda_familiar
        "Até 3 meses",               # prazo_compra
        "(11) 99999-0000",          # whatsapp
    ]

    for i, msg in enumerate(steps):
        resp = await processar_chatbot(msg, session_id)
        print(f"STEP {i+1}: input= {msg!r}")
        print("OUTPUT:")
        print(resp)
        print("-"*60)

    # After flow, check session cleanup
    try:
        from chatbot_engine import sessoes
        print("Sessões agora:", sessoes)
    except Exception as e:
        print("Não foi possível acessar sessoes:", e)

if __name__ == "__main__":
    asyncio.run(run_test())
