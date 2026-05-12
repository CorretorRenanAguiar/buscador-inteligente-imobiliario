import { supabase } from "../lib/supabase"

function TesteSupabase() {

  async function testarBanco() {

    const { data, error } = await supabase
      .from("leads")
      .insert([
        {
          nome: "Renan Aguiar",

          email: "teste@gmail.com",

          telefone: "(32)99999-9999",

          cidade: "Juiz de Fora",

          bairro: "São Pedro",

          faixa_renda: "R$ 3.000 a R$ 5.000",

          faixa_preco_interesse:
            "R$ 200.000 a R$ 350.000",

          tipo_interesse: "Apartamento",

          objetivo: "Compra",

          origem_lead: "Site"
        }
      ])

    if (error) {

      console.error(
        "ERRO AO INSERIR:",
        error
      )

      alert("Erro ao conectar banco")

      return
    }

    console.log("SUCESSO:", data)

    alert("Lead salvo com sucesso!")

  }

  return (

    <div
      style={{
        marginTop: "40px",
        textAlign: "center"
      }}
    >

      <button
        onClick={testarBanco}

        style={{
          backgroundColor: "#d4a017",

          color: "#ffffff",

          border: "none",

          padding: "16px 28px",

          borderRadius: "12px",

          fontSize: "16px",

          cursor: "pointer",

          fontWeight: "bold"
        }}
      >
        Testar Conexão Supabase
      </button>

    </div>

  )

}

export default TesteSupabase