import { supabase } from "../lib/supabase";

function TesteSupabase() {
  async function testarBanco() {

    console.log("TESTE DE CONEXÃO COM SUPABASE");

    const leadTeste = {
      telefone: "(32)99999-9999",
      bairro: "São Pedro",
      faixa_preco_interesse: "R$ 200.000 a R$ 350.000",
      tipo_interesse: "Apartamento",
      objetivo: "Compra",
      origem_lead: "Teste Frontend"
    };

    console.log("Dados enviados:", leadTeste);

    try {
      const { error } = await supabase
        .from("leads")
        .insert([leadTeste]);

      if (error) {

        console.error("ERRO AO INSERIR NO SUPABASE");

        console.error("Mensagem:", error.message);
        console.error("Código:", error.code);
        console.error("Detalhes:", error.details);
        console.error("Hint:", error.hint);

        alert(
          `Erro ao inserir no Supabase:\n\n${error.message}`
        );

        return;
      }


      console.log("SUPABASE: INSERT REALIZADO COM SUCESSO");


      alert("Conexão com Supabase OK! Lead de teste salvo.");

    } catch (erro) {

      console.error("ERRO INESPERADO");

      console.error(erro);

      alert(
        `Erro inesperado ao conectar com o Supabase:\n\n${erro.message}`
      );
    }
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
  );
}

export default TesteSupabase;