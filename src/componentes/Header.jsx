function Header() {

  return (

    <header
      style={{
        position: "fixed",
        top: 0,
        width: "100%",
        zIndex: 999,
        backgroundColor: "#0f172a",
        padding: "20px 60px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        boxSizing: "border-box"
      }}
    >

      {/* LOGO */}

      <div>

        <h1
          style={{
            color: "#d4a017",
            margin: 0,
            fontSize: "34px",
            lineHeight: "1"
          }}
        >
          RA
        </h1>

        <p
          style={{
            color: "#ffffff",
            margin: 0,
            fontSize: "14px",
            letterSpacing: "2px"
          }}
        >
          INTELIGÊNCIA IMOBILIÁRIA
        </p>

      </div>


      {/* MENU */}

      <nav
        style={{
          display: "flex",
          gap: "40px"
        }}
      >

        <a href="#" style={menuStyle}>Sobre</a>
        <a href="#" style={menuStyle}>Imóveis</a>
        <a href="#" style={menuStyle}>Comprar</a>
        <a href="#" style={menuStyle}>Alugar</a>
        <a href="#" style={menuStyle}>Contato</a>

      </nav>

    </header>

  )

}

const menuStyle = {
  color: "#ffffff",
  textDecoration: "none",
  fontWeight: "bold",
  fontSize: "17px"
}

export default Header