import { useState } from "react"

function ChatBot() {

  const [message, setMessage] = useState("")
  const [minimized, setMinimized] = useState(false)

  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text:
        "Olá 👋 Sou a assistente virtual da RA Inteligência Imobiliária. Posso ajudar a encontrar um imóvel ideal para seu perfil."
    }
  ])


  function sendMessage() {

    if (message.trim() === "") return

    const userMessage = {
      sender: "user",
      text: message
    }

    const botResponse = {
      sender: "bot",
      text:
        "Perfeito. Estou analisando imóveis compatíveis com seu perfil."
    }

    setMessages([
      ...messages,
      userMessage,
      botResponse
    ])

    setMessage("")
  }


  return (

    <>

      {/* BOTÃO RESTAURAR */}

      {
        minimized && (

          <button
            onClick={() => setMinimized(false)}

            style={{
              position: "fixed",

              bottom: "95px",

              right: "25px",

              backgroundColor: "#d4a017",

              color: "#ffffff",

              border: "none",

              borderRadius: "18px",

              padding: "16px 22px",

              cursor: "pointer",

              fontWeight: "bold",

              zIndex: 99999,

              boxShadow:
                "0px 10px 25px rgba(0,0,0,0.25)"
            }}
          >
            💬 Fale com o corretor
          </button>

        )
      }



      {/* CHAT */}

      {
        !minimized && (

          <div
            style={{
              position: "fixed",

              right: "25px",

              bottom: "90px",

              width: "360px",

              height: "580px",

              backgroundColor: "#ffffff",

              borderRadius: "24px",

              overflow: "hidden",

              boxShadow:
                "0px 20px 45px rgba(0,0,0,0.22)",

              zIndex: 99999,

              display: "flex",

              flexDirection: "column"
            }}
          >

            {/* HEADER */}

            <div
              style={{
                background:
                  "linear-gradient(135deg, #0f172a, #1e293b)",

                padding: "18px 20px",

                display: "flex",

                justifyContent: "space-between",

                alignItems: "center"
              }}
            >

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px"
                }}
              >

                <div
                  style={{
                    width: "54px",

                    height: "54px",

                    borderRadius: "50%",

                    backgroundColor: "#d4a017",

                    display: "flex",

                    justifyContent: "center",

                    alignItems: "center",

                    fontSize: "24px"
                  }}
                >
                  👩
                </div>


                <div>

                  <h3
                    style={{
                      margin: 0,
                      color: "#ffffff"
                    }}
                  >
                    Assistente Virtual
                  </h3>

                  <p
                    style={{
                      margin: 0,

                      color: "#cbd5e1",

                      fontSize: "13px"
                    }}
                  >
                    Online agora
                  </p>

                </div>

              </div>



              {/* BOTÃO MINIMIZAR */}

              <button
                onClick={() => setMinimized(true)}

                style={{
                  background: "transparent",

                  border: "none",

                  color: "#ffffff",

                  fontSize: "26px",

                  cursor: "pointer",

                  lineHeight: 1
                }}
              >
                −
              </button>

            </div>



            {/* MENSAGENS */}

            <div
              style={{
                flex: 1,

                backgroundColor: "#f8fafc",

                padding: "20px",

                overflowY: "auto"
              }}
            >

              {
                messages.map((msg, index) => (

                  <div
                    key={index}

                    style={{
                      display: "flex",

                      justifyContent:
                        msg.sender === "user"
                          ? "flex-end"
                          : "flex-start",

                      marginBottom: "16px"
                    }}
                  >

                    <div
                      style={{
                        backgroundColor:
                          msg.sender === "user"
                            ? "#d4a017"
                            : "#ffffff",

                        color:
                          msg.sender === "user"
                            ? "#ffffff"
                            : "#111827",

                        padding: "14px 16px",

                        borderRadius: "16px",

                        maxWidth: "80%",

                        lineHeight: "1.6",

                        boxShadow:
                          "0px 4px 10px rgba(0,0,0,0.05)"
                      }}
                    >
                      {msg.text}
                    </div>

                  </div>

                ))
              }

            </div>



            {/* INPUT */}

            <div
              style={{
                padding: "16px",

                borderTop:
                  "1px solid #e5e7eb",

                display: "flex",

                gap: "10px"
              }}
            >

              <input
                type="text"

                placeholder="Digite sua mensagem..."

                value={message}

                onChange={(e) =>
                  setMessage(e.target.value)
                }

                onKeyDown={(e) => {

                  if (e.key === "Enter") {
                    sendMessage()
                  }

                }}

                style={{
                  flex: 1,

                  padding: "15px",

                  borderRadius: "14px",

                  border:
                    "1px solid #d1d5db",

                  outline: "none",

                  fontSize: "15px"
                }}
              />


              <button
                onClick={sendMessage}

                style={{
                  backgroundColor: "#d4a017",

                  color: "#ffffff",

                  border: "none",

                  padding: "0px 18px",

                  borderRadius: "14px",

                  cursor: "pointer",

                  fontWeight: "bold"
                }}
              >
                Enviar
              </button>

            </div>

          </div>

        )
      }

    </>

  )

}

export default ChatBot