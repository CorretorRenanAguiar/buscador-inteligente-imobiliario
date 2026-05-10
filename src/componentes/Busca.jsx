import { useState } from "react"

function Busca() {

  const [tipoNegocio, setTipoNegocio] = useState("comprar")

  return (

    <div
      style={{
        backgroundColor: "#ffffff",
        borderRadius: "28px",
        padding: "35px",
        boxShadow: "0px 20px 45px rgba(0,0,0,0.25)"
      }}
    >

      {/* ABAS */}

      <div
        style={{
          display: "flex",
          marginBottom: "30px",
          gap: "10px"
        }}
      >

        <button
          onClick={() => setTipoNegocio("comprar")}
          style={{
            ...tabStyle,
            backgroundColor:
              tipoNegocio === "comprar"
                ? "#d4a017"
                : "#f3f4f6",

            color:
              tipoNegocio === "comprar"
                ? "#ffffff"
                : "#111827"
          }}
        >
          Comprar
        </button>


        <button
          onClick={() => setTipoNegocio("alugar")}
          style={{
            ...tabStyle,
            backgroundColor:
              tipoNegocio === "alugar"
                ? "#d4a017"
                : "#f3f4f6",

            color:
              tipoNegocio === "alugar"
                ? "#ffffff"
                : "#111827"
          }}
        >
          Alugar
        </button>

      </div>


      {/* FILTROS */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(220px, 1fr))",

          gap: "20px"
        }}
      >

        {/* TIPO */}

        <div>

          <label style={labelStyle}>
            Tipo de Imóvel
          </label>

          <select style={inputStyle}>

            <option>Selecione</option>

            <option>Apartamento</option>
            <option>Casa</option>
            <option>Cobertura</option>
            <option>Studio</option>
            <option>Loft</option>
            <option>Kitnet</option>
            <option>Flat</option>
            <option>Terreno</option>
            <option>Chácara</option>
            <option>Sítio</option>
            <option>Fazenda</option>
            <option>Sala Comercial</option>
            <option>Galpão</option>
            <option>Loja</option>

          </select>

        </div>


        {/* QUARTOS */}

        <div>

          <label style={labelStyle}>
            Quartos
          </label>

          <select style={inputStyle}>

            <option>Selecione</option>

            <option>1 quarto</option>
            <option>2 quartos</option>
            <option>3 quartos</option>
            <option>4 quartos</option>
            <option>5+ quartos</option>

          </select>

        </div>


        {/* BAIRRO */}

        <div>

          <label style={labelStyle}>
            Cidade / Bairro
          </label>

          <input
            type="text"
            placeholder="Digite bairro ou cidade"
            style={inputStyle}
          />

        </div>


        {/* VALOR */}

        <div>

          <label style={labelStyle}>
            Faixa de preço
          </label>

          <input
            type="text"
            placeholder="R$ 250.000"
            style={inputStyle}
          />

        </div>

      </div>


      {/* BOTÃO */}

      <div
        style={{
          marginTop: "30px",
          display: "flex",
          justifyContent: "flex-end"
        }}
      >

        <button
          style={{
            backgroundColor: "#d4a017",
            color: "#ffffff",
            border: "none",
            padding: "18px 32px",
            borderRadius: "16px",
            fontSize: "18px",
            fontWeight: "bold",
            cursor: "pointer"
          }}
        >
          Buscar imóveis
        </button>

      </div>

    </div>

  )

}

const tabStyle = {
  border: "none",
  padding: "16px 28px",
  borderRadius: "14px",
  fontWeight: "bold",
  cursor: "pointer",
  fontSize: "16px"
}

const labelStyle = {
  display: "block",
  marginBottom: "10px",
  fontWeight: "bold",
  color: "#111827"
}

const inputStyle = {
  width: "100%",
  padding: "18px",
  borderRadius: "14px",
  border: "1px solid #d1d5db",
  fontSize: "16px",
  boxSizing: "border-box"
}

export default Busca