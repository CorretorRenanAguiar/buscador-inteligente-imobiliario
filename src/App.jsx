import Header from "./componentes/Header"
import Busca from "./componentes/Busca"
import CookieBanner from "./componentes/CookieBanner"
import ChatBot from "./componentes/Chatbot"

function App() {

  return (

    <div
      style={{
        width: "100%",
        minHeight: "100vh",
        overflowX: "auto",
        backgroundColor: "#0f172a",
        fontFamily: "Arial, sans-serif"
      }}
    >

      <Header />



      {/* HERO */}

      <section
        style={{
          width: "100%",
          minHeight: "100vh",

          backgroundImage:
            "linear-gradient(rgba(15,23,42,0.70), rgba(15,23,42,0.70)), url('https://images.unsplash.com/photo-1600585154526-990dced4db0d?q=80&w=1600')",

          backgroundSize: "cover",
          backgroundPosition: "center",

          paddingTop: "120px",
          paddingBottom: "120px"
        }}
      >


        {/* CONTAINER */}

        <div
          style={{
            width: "100%",
            maxWidth: "1500px",
            margin: "0 auto",
            padding: "0px 30px",
            boxSizing: "border-box"
          }}
        >


          {/* FAIXA */}

          <div
            style={{
              background:
                "linear-gradient(90deg, rgba(212,160,23,0.20), rgba(255,255,255,0.08))",

              border: "1px solid rgba(255,255,255,0.1)",

              backdropFilter: "blur(8px)",

              padding: "18px 28px",

              borderRadius: "18px",

              marginBottom: "40px",

              display: "inline-block"
            }}
          >

            <p
              style={{
                color: "#facc15",
                margin: 0,
                fontWeight: "bold",
                letterSpacing: "4px",
                fontSize: "15px"
              }}
            >
              IA • MACHINE LEARNING • MERCADO IMOBILIÁRIO
            </p>

          </div>



          {/* TÍTULO */}

          <div
            style={{
              maxWidth: "850px",
              marginBottom: "60px"
            }}
          >

            <h1
              style={{
                color: "#ffffff",
                fontSize: "72px",
                lineHeight: "1.05",
                marginBottom: "20px"
              }}
            >
              Buscador Inteligente
              <br />
              para o mercado
              <br />
              imobiliário
            </h1>


            <p
              style={{
                color: "#d1d5db",
                fontSize: "22px",
                lineHeight: "1.8"
              }}
            >
              Plataforma de recomendação imobiliária
              baseada em Inteligência Artificial para
              segmentação automatizada de leads,
              análise comportamental e recomendação
              inteligente de imóveis.
            </p>

          </div>



          {/* CARROSSEL DE IMÓVEIS */}

          <div
            style={{
              display: "flex",
              gap: "24px",
              overflowX: "auto",
              paddingBottom: "15px",
              marginBottom: "50px"
            }}
          >

            {[
              {
                titulo: "Apartamento 2 quartos",
                bairro: "São Pedro",
                preco: "R$ 219.000",
                imagem:
                  "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?q=80&w=1200"
              },

              {
                titulo: "Casa moderna",
                bairro: "Jardim da Serra",
                preco: "R$ 780.000",
                imagem:
                  "https://images.unsplash.com/photo-1600585154526-990dced4db0d?q=80&w=1200"
              },

              {
                titulo: "Cobertura premium",
                bairro: "Cascatinha",
                preco: "R$ 1.290.000",
                imagem:
                  "https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=1200"
              },

              {
                titulo: "Apartamento Studio",
                bairro: "Centro",
                preco: "R$ 189.000",
                imagem:
                  "https://images.unsplash.com/photo-1484154218962-a197022b5858?q=80&w=1200"
              }
            ].map((imovel, index) => (

              <div
                key={index}

                style={{
                  minWidth: "320px",

                  backgroundColor:
                    "rgba(255,255,255,0.08)",

                  borderRadius: "24px",

                  overflow: "hidden",

                  backdropFilter: "blur(8px)",

                  border:
                    "1px solid rgba(255,255,255,0.08)"
                }}
              >

                <img
                  src={imovel.imagem}

                  style={{
                    width: "100%",
                    height: "220px",
                    objectFit: "cover"
                  }}
                />


                <div
                  style={{
                    padding: "22px"
                  }}
                >

                  <h3
                    style={{
                      color: "#ffffff",
                      marginBottom: "10px"
                    }}
                  >
                    {imovel.titulo}
                  </h3>


                  <p
                    style={{
                      color: "#cbd5e1",
                      marginBottom: "15px"
                    }}
                  >
                    {imovel.bairro}
                  </p>


                  <h2
                    style={{
                      color: "#facc15"
                    }}
                  >
                    {imovel.preco}
                  </h2>

                </div>

              </div>

            ))}

          </div>



          {/* BUSCA */}

          <Busca />

        </div>

      </section>



      {/* CHAT */}

      <ChatBot />



      {/* COOKIE */}

      <CookieBanner />

    </div>

  )

}

export default App