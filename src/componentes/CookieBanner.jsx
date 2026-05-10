import { useState } from "react"

function CookieBanner() {

  const [showPolicy, setShowPolicy] = useState(false)
  const [visible, setVisible] = useState(true)

  if (!visible) return null

  return (

    <>

      {/* =========================================
          BANNER DE COOKIES
      ========================================= */}

      <div
        style={{
          position: "fixed",
          bottom: 0,
          left: 0,
          width: "100%",

          background:
            "linear-gradient(90deg, #0f172a, #111827)",

          padding: "16px 24px",

          display: "flex",

          justifyContent: "space-between",

          alignItems: "center",

          gap: "20px",

          zIndex: 999999,

          borderTop:
            "1px solid rgba(255,255,255,0.08)",

          flexWrap: "wrap"
        }}
      >

        {/* TEXTO */}

        <p
          style={{
            color: "#e5e7eb",

            margin: 0,

            fontSize: "14px",

            lineHeight: "1.7",

            maxWidth: "950px"
          }}
        >
          Utilizamos cookies e tecnologias de rastreamento
          para personalizar recomendações imobiliárias,
          aprimorar algoritmos de Inteligência Artificial
          (IA) e Machine Learning (ML) e melhorar a
          experiência do usuário, conforme diretrizes
          da Lei Geral de Proteção de Dados (LGPD).
        </p>



        {/* BOTÕES */}

        <div
          style={{
            display: "flex",
            gap: "12px"
          }}
        >

          {/* LER POLÍTICA */}

          <button
            onClick={() => setShowPolicy(true)}

            style={{
              backgroundColor: "transparent",

              color: "#ffffff",

              border:
                "1px solid rgba(255,255,255,0.2)",

              padding: "12px 18px",

              borderRadius: "12px",

              cursor: "pointer",

              fontWeight: "bold"
            }}
          >
            Ler Política
          </button>



          {/* RECUSAR */}

          <button
            onClick={() => setVisible(false)}

            style={{
              backgroundColor: "#334155",

              color: "#ffffff",

              border: "none",

              padding: "12px 18px",

              borderRadius: "12px",

              cursor: "pointer",

              fontWeight: "bold"
            }}
          >
            Recusar
          </button>



          {/* ACEITAR */}

          <button
            onClick={() => setVisible(false)}

            style={{
              backgroundColor: "#d4a017",

              color: "#ffffff",

              border: "none",

              padding: "12px 18px",

              borderRadius: "12px",

              cursor: "pointer",

              fontWeight: "bold"
            }}
          >
            Aceitar
          </button>

        </div>

      </div>



      {/* =========================================
          MODAL DA POLÍTICA
      ========================================= */}

      {
        showPolicy && (

          <div
            style={{
              position: "fixed",

              top: 0,
              left: 0,

              width: "100%",
              height: "100%",

              backgroundColor:
                "rgba(0,0,0,0.72)",

              display: "flex",

              justifyContent: "center",

              alignItems: "center",

              zIndex: 9999999,

              padding: "30px",

              boxSizing: "border-box"
            }}
          >

            {/* CAIXA MODAL */}

            <div
              style={{
                width: "900px",

                maxHeight: "90vh",

                overflowY: "auto",

                backgroundColor: "#ffffff",

                borderRadius: "24px",

                padding: "40px",

                boxShadow:
                  "0px 25px 60px rgba(0,0,0,0.35)"
              }}
            >

              {/* TÍTULO */}

              <h2
                style={{
                  marginTop: 0,
                  color: "#111827",
                  fontSize: "30px"
                }}
              >
                Política de Cookies,
                Privacidade e Proteção de Dados
              </h2>



              {/* INTRODUÇÃO */}

              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                A plataforma RA Inteligência Imobiliária
                utiliza cookies, armazenamento local,
                identificadores de sessão e tecnologias
                de rastreamento com o objetivo de melhorar
                a experiência do usuário, personalizar
                recomendações imobiliárias e aprimorar os
                algoritmos de Inteligência Artificial (IA)
                e Machine Learning (ML) aplicados ao sistema.
              </p>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                Este sistema integra um projeto acadêmico
                e científico desenvolvido como requisito
                parcial para obtenção do título de
                Especialista em Desenvolvimento de
                Projetos Baseados em Tecnologia 4.0
                pelo Instituto Federal de Educação,
                Ciência e Tecnologia do Sudeste de
                Minas Gerais (IF Sudeste MG) —
                Campus Juiz de Fora.
              </p>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                A pesquisa possui como foco a aplicação
                de Inteligência Artificial (AI),
                Machine Learning (ML), análise de dados,
                automação e segmentação inteligente
                de leads no mercado imobiliário.
              </p>



              {/* EQUIPE */}

              <h3
                style={{
                  color: "#111827",
                  marginTop: "35px"
                }}
              >
                Equipe Acadêmica
              </h3>


              <ul
                style={{
                  lineHeight: "2",
                  color: "#374151"
                }}
              >

                <li>
                  Autor:
                  Renan Cesar Gomes de Aguiar
                </li>

                <li>
                  Orientadora:
                  Profa. Dra. Annik Passos Marocco
                </li>

                <li>
                  Coorientadora:
                  Profa. Dra. Silvana Terezinha Faceroli
                </li>

                <li>
                  Coorientadora:
                  Profa. Dra. Silvia Augusta do Nascimento
                </li>

              </ul>



              {/* DADOS COLETADOS */}

              <h3
                style={{
                  color: "#111827",
                  marginTop: "35px"
                }}
              >
                Informações que podem ser coletadas
              </h3>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                Durante a navegação na plataforma,
                poderão ser coletadas informações
                relacionadas ao comportamento do usuário,
                preferências imobiliárias e interações
                realizadas com o sistema.
              </p>


              <ul
                style={{
                  lineHeight: "2",
                  color: "#374151"
                }}
              >

                <li>Tipo de imóvel pesquisado;</li>

                <li>
                  Interesse em compra, venda ou locação;
                </li>

                <li>Faixa de preço pesquisada;</li>

                <li>
                  Bairros, regiões e cidades pesquisadas;
                </li>

                <li>
                  Quantidade de quartos e características desejadas;
                </li>

                <li>Tempo de navegação na plataforma;</li>

                <li>Páginas visualizadas;</li>

                <li>Cliques realizados;</li>

                <li>
                  Interações realizadas no chatbot inteligente;
                </li>

                <li>
                  Dados estatísticos de utilização;
                </li>

                <li>
                  Padrões de comportamento de navegação.
                </li>

              </ul>



              {/* FINALIDADE */}

              <h3
                style={{
                  color: "#111827",
                  marginTop: "35px"
                }}
              >
                Finalidade da utilização dos dados
              </h3>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                Os dados coletados são utilizados
                exclusivamente para fins acadêmicos,
                científicos, estatísticos e tecnológicos
                relacionados ao desenvolvimento do sistema
                inteligente de recomendação imobiliária.
              </p>


              <ul
                style={{
                  lineHeight: "2",
                  color: "#374151"
                }}
              >

                <li>
                  Segmentação automatizada de leads;
                </li>

                <li>
                  Recomendação inteligente de imóveis;
                </li>

                <li>
                  Aprimoramento dos algoritmos de IA;
                </li>

                <li>
                  Treinamento de modelos de Machine Learning;
                </li>

                <li>
                  Análise comportamental de navegação;
                </li>

                <li>
                  Classificação automatizada de perfis;
                </li>

                <li>
                  Geração de métricas estatísticas;
                </li>

                <li>
                  Desenvolvimento tecnológico do TCC.
                </li>

              </ul>



              {/* REFERENCIAIS */}

              <h3
                style={{
                  color: "#111827",
                  marginTop: "35px"
                }}
              >
                Fundamentação científica da pesquisa
              </h3>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                A fundamentação teórica do projeto utiliza
                pesquisas nacionais e internacionais sobre:
              </p>


              <ul
                style={{
                  lineHeight: "2",
                  color: "#374151"
                }}
              >

                <li>
                  Inteligência Artificial aplicada ao mercado imobiliário;
                </li>

                <li>
                  Machine Learning para previsão e recomendação imobiliária;
                </li>

                <li>
                  CRM e relacionamento com clientes;
                </li>

                <li>
                  Chatbots e automação do atendimento;
                </li>

                <li>
                  Marketing digital e transformação digital;
                </li>

                <li>
                  Segmentação inteligente de leads;
                </li>

                <li>
                  Proteção de dados, ética computacional e LGPD.
                </li>

              </ul>



              {/* LGPD */}

              <h3
                style={{
                  color: "#111827",
                  marginTop: "35px"
                }}
              >
                Direitos do usuário
              </h3>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                O usuário poderá, a qualquer momento,
                solicitar exclusão dos dados coletados,
                revogar o consentimento concedido
                ou interromper a coleta de informações,
                conforme previsto pela Lei Geral de
                Proteção de Dados (LGPD —
                Lei nº 13.709/2018) e pelo Guia
                Orientativo “Cookies e Proteção
                de Dados Pessoais” da Autoridade
                Nacional de Proteção de Dados (ANPD).
              </p>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                O gerenciamento de cookies também poderá
                ser realizado diretamente pelo navegador
                utilizado pelo usuário.
              </p>



              {/* CONSENTIMENTO */}

              <h3
                style={{
                  color: "#111827",
                  marginTop: "35px"
                }}
              >
                Consentimento
              </h3>


              <p
                style={{
                  lineHeight: "1.9",
                  color: "#374151"
                }}
              >
                Ao clicar em “Aceitar”, o usuário declara
                estar ciente sobre a utilização de cookies
                e tecnologias de rastreamento descritas
                nesta política, autorizando o tratamento
                das informações nas condições aqui apresentadas.
              </p>



              {/* BOTÃO FECHAR */}

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginTop: "35px"
                }}
              >

                <button
                  onClick={() => setShowPolicy(false)}

                  style={{
                    backgroundColor: "#d4a017",

                    color: "#ffffff",

                    border: "none",

                    padding: "14px 24px",

                    borderRadius: "12px",

                    cursor: "pointer",

                    fontWeight: "bold"
                  }}
                >
                  Fechar
                </button>

              </div>

            </div>

          </div>

        )
      }

    </>

  )

}

export default CookieBanner