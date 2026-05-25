import { useState, useEffect, useRef } from "react"

export default function ChatBot() {

    const [aberto, setAberto] = useState(false)

    const [mensagens, setMensagens] = useState([])

    const [input, setInput] = useState("")

    const mensagensRef = useRef(null)

    const [sessao] = useState(() => Date.now().toString())

    // =====================================
    // AUTO SCROLL
    // =====================================

    useEffect(() => {

        if (mensagensRef.current) {

            mensagensRef.current.scrollTop =
                mensagensRef.current.scrollHeight

        }

    }, [mensagens])

    // =====================================
    // ENVIAR MENSAGEM
    // =====================================

    async function enviarMensagem(texto) {

        if (!texto.trim()) return

        const novasMensagens = [

            ...mensagens,

            {
                autor: "usuario",
                texto
            }

        ]

        setMensagens(novasMensagens)

        setInput("")

        try {

            const resposta = await fetch(
                "https://buscador-inteligente-imobiliario-production-b5a8.up.railway.app/chat",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        mensagem: texto,

                        session_id: sessao

                    })

                }

            )

            const dados = await resposta.json()

            setMensagens([

                ...novasMensagens,

                {

                    autor: "bot",

                    texto: dados.mensagem,

                    opcoes:
                        dados.opcoes || [],

                    link_whatsapp:
                        dados.link_whatsapp
                            ? dados.link_whatsapp.replace(/\D/g, "")
                            : null

                }

            ])

        } catch (erro) {

            console.log(erro)

            setMensagens([

                ...novasMensagens,

                {

                    autor: "bot",

                    texto:
                        "❌ Erro ao conectar com o servidor."

                }

            ])

        }

    }

    // =====================================
    // ABRIR CHAT
    // =====================================

    function abrirChat() {

        setAberto(true)

        if (mensagens.length === 0) {

            enviarMensagem("iniciar")

        }

    }

    return (

        <>

            {/* ================================= */}
            {/* BOTÃO FLUTUANTE */}
            {/* ================================= */}

            {

                !aberto && (

                    <button

                        onClick={abrirChat}

                        style={{

                            position: "fixed",

                            bottom: "20px",

                            right: "20px",

                            width: "65px",

                            height: "65px",

                            borderRadius: "50%",

                            border: "none",

                            background: "#d4a017",

                            color: "#fff",

                            fontSize: "28px",

                            cursor: "pointer",

                            zIndex: 99999,

                            boxShadow:
                                "0 6px 20px rgba(0,0,0,0.3)"

                        }}

                    >

                        💬

                    </button>

                )

            }

            {/* ================================= */}
            {/* CHAT */}
            {/* ================================= */}

            {

                aberto && (

                    <div

                        style={{

                            position: "fixed",

                            bottom: "20px",

                            right: "20px",

                            width: "350px",

                            height: "520px",

                            background: "#fff",

                            borderRadius: "18px",

                            overflow: "hidden",

                            zIndex: 99999,

                            display: "flex",

                            flexDirection: "column",

                            boxShadow:
                                "0 12px 35px rgba(0,0,0,0.25)"

                        }}

                    >

                        {/* HEADER */}

                        <div

                            style={{

                                background: "#08142b",

                                color: "#fff",

                                padding: "14px",

                                display: "flex",

                                justifyContent:
                                    "space-between",

                                alignItems: "center"

                            }}

                        >

                            <div>

                                <div

                                    style={{

                                        fontWeight: "bold",

                                        fontSize: "15px"

                                    }}

                                >

                                    RA Inteligência Imobiliária

                                </div>

                                <div

                                    style={{

                                        fontSize: "12px",

                                        opacity: 0.8

                                    }}

                                >

                                    Atendimento Inteligente

                                </div>

                            </div>

                            <button

                                onClick={() =>
                                    setAberto(false)
                                }

                                style={{

                                    background: "transparent",

                                    border: "none",

                                    color: "#fff",

                                    fontSize: "24px",

                                    cursor: "pointer"

                                }}

                            >

                                −

                            </button>

                        </div>

                        {/* MENSAGENS */}

                        <div

                            ref={mensagensRef}

                            style={{

                                flex: 1,

                                overflowY: "auto",

                                padding: "14px",

                                background: "#f4f4f4",

                                display: "flex",

                                flexDirection: "column",

                                gap: "12px"

                            }}

                        >

                            {

                                mensagens.map(

                                    (

                                        msg,

                                        index

                                    ) => (

                                        <div

                                            key={index}

                                            style={{

                                                display: "flex",

                                                flexDirection: "column",

                                                alignItems:
                                                    msg.autor === "bot"
                                                    ? "flex-start"
                                                    : "flex-end"

                                            }}

                                        >

                                            {/* BOLHA */}

                                            <div

                                                style={{

                                                    background:
                                                        msg.autor === "bot"
                                                        ? "#fff"
                                                        : "#d4a017",

                                                    color:
                                                        msg.autor === "bot"
                                                        ? "#000"
                                                        : "#fff",

                                                    padding: "12px",

                                                    borderRadius: "14px",

                                                    maxWidth: "85%",

                                                    whiteSpace: "pre-line",

                                                    fontSize: "14px",

                                                    lineHeight: "1.4"

                                                }}

                                            >

                                                {msg.texto}

                                            </div>

                                            {/* OPÇÕES */}

                                            {

                                                msg.opcoes?.length > 0 && (

                                                    <div

                                                        style={{

                                                            display: "flex",

                                                            flexWrap: "wrap",

                                                            gap: "8px",

                                                            marginTop: "10px"

                                                        }}

                                                    >

                                                        {

                                                            msg.opcoes.map(

                                                                (

                                                                    opcao,

                                                                    i

                                                                ) => (

                                                                    <button

                                                                        key={i}

                                                                        onClick={() =>
                                                                            enviarMensagem(
                                                                                opcao
                                                                            )
                                                                        }

                                                                        style={{

                                                                            background:
                                                                                "#d4a017",

                                                                            color:
                                                                                "#fff",

                                                                            border:
                                                                                "none",

                                                                            borderRadius:
                                                                                "10px",

                                                                            padding:
                                                                                "10px 14px",

                                                                            cursor:
                                                                                "pointer",

                                                                            fontSize:
                                                                                "13px",

                                                                            fontWeight:
                                                                                "bold"

                                                                        }}

                                                                    >

                                                                        {opcao}

                                                                    </button>

                                                                )

                                                            )

                                                        }

                                                    </div>

                                                )

                                            }

                                            {/* BOTÃO WHATSAPP */}

                                            {

                                                msg.link_whatsapp && (

                                                    <a

                                                        href={`https://wa.me/${msg.link_whatsapp}`}

                                                        target="_blank"

                                                        rel="noreferrer"

                                                        style={{

                                                            marginTop: "10px",

                                                            display:
                                                                "inline-block",

                                                            background:
                                                                "#25D366",

                                                            color: "#fff",

                                                            padding:
                                                                "10px 14px",

                                                            borderRadius:
                                                                "10px",

                                                            textDecoration:
                                                                "none",

                                                            fontSize: "14px",

                                                            fontWeight:
                                                                "bold"

                                                        }}

                                                    >

                                                        Falar no WhatsApp

                                                    </a>

                                                )

                                            }

                                        </div>

                                    )

                                )

                            }

                        </div>

                        {/* INPUT */}

                        <div

                            style={{

                                borderTop:
                                    "1px solid #ddd",

                                padding: "10px",

                                display: "flex",

                                gap: "10px",

                                background: "#fff"

                            }}

                        >

                            <input

                                type="text"

                                value={input}

                                placeholder="Digite sua mensagem..."

                                onChange={(e) =>
                                    setInput(
                                        e.target.value
                                    )
                                }

                                onKeyDown={(e) => {

                                    if (
                                        e.key === "Enter"
                                    ) {

                                        enviarMensagem(
                                            input
                                        )

                                    }

                                }}

                                style={{

                                    flex: 1,

                                    padding: "12px",

                                    borderRadius: "10px",

                                    border:
                                        "1px solid #ccc",

                                    outline: "none",

                                    fontSize: "14px"

                                }}

                            />

                            <button

                                onClick={() =>
                                    enviarMensagem(
                                        input
                                    )
                                }

                                style={{

                                    background: "#d4a017",

                                    color: "#fff",

                                    border: "none",

                                    padding:
                                        "0 16px",

                                    borderRadius: "10px",

                                    cursor: "pointer",

                                    fontWeight: "bold"

                                }}

                            >

                                ➤

                            </button>

                        </div>

                    </div>

                )

            }

        </>

    )

}