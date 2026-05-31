import Header from "./componentes/Header"
import Busca from "./componentes/Busca"
import TesteSupabase from "./componentes/TesteSupabase"

import ChatBot from "./componentes/Chatbot"
import CookieBanner from "./componentes/CookieBanner"



function App() {

  return (

    <div
      style={{
        minHeight: "100vh",

        background:
          "linear-gradient(to bottom, #0f172a, #111827)",

        color: "#ffffff",

        overflowX: "hidden"
      }}
    >

      {/* =========================================
          HEADER
      ========================================= */}

      <Header />



      {/* =========================================
          BUSCA
      ========================================= */}

      <Busca />



      {/* =========================================
          SEÇÃO PRINCIPAL
      ========================================= */}

      <section
        style={{
          width: "100%",

          maxWidth: "1400px",

          margin: "0 auto",

          padding:
            "40px 20px 120px 20px",

          boxSizing: "border-box"
        }}
      >

        {/* =========================================
            DESTAQUE
        ========================================= */}

        <div
          style={{
            background:
              "linear-gradient(135deg, #111827, #1e293b)",

            border:
              "1px solid rgba(255,255,255,0.08)",

            borderRadius: "28px",

            padding: "50px",

            marginBottom: "40px",

            boxShadow:
              "0px 15px 40px rgba(0,0,0,0.25)"
          }}
        >

          <h1
            style={{
              fontSize: "48px",

              marginBottom: "20px",

              color: "#ffffff",

              lineHeight: "1.2"
            }}
          >
            Plataforma Inteligente
            para Segmentação e
            Recomendação Imobiliária
          </h1>



          <p
            style={{
              fontSize: "18px",

              lineHeight: "1.9",

              color: "#d1d5db",

              maxWidth: "900px"
            }}
          >
            Sistema inteligente baseado em
            Inteligência Artificial (IA),
            Machine Learning (ML),
            análise comportamental,
            segmentação inteligente de leads
            e recomendação automatizada
            de imóveis.
          </p>

        </div>



        {/* =========================================
            BOTÃO TESTE SUPABASE
        ========================================= */}

        <TesteSupabase />

      </section>



      {/* =========================================
          CHATBOT
      ========================================= */}

      <ChatBot />



      {/* =========================================
          COOKIES
      ========================================= */}

      <CookieBanner />

    </div>

  )

}

export default App