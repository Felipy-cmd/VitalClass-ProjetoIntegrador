const API_URL = "http://127.0.0.1:5005";

setInterval(carregarFila, 20000);

async function carregarFila() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "index.html";
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/fila`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        });

        const dados = await resposta.json();

        if (!Array.isArray(dados)) {
            console.error(dados);
            return;
        }

        const lista = document.getElementById("listaPacientes");
        lista.innerHTML = "";

        let graves = 0;
        let atendidos = 0;

        dados.forEach(paciente => {
            const classificacao = (paciente.classificacao || "").toLowerCase();

            if (paciente.classificacao === "VERMELHO" || paciente.classificacao === "LARANJA") {
                graves++;
            }

            if (paciente.status === "FINALIZADO") {
                atendidos++;
            }

            const proximoSt  = proximoStatus(paciente.status);
            const textoBt    = textoBotao(paciente.status);
            const classesSt  = classeStatus(paciente.status);

            const div = document.createElement("div");
            div.className = "paciente";
            div.innerHTML = `
                <span class="urgente ${classificacao}"></span>
                <p>${paciente.nome}</p>
                <span class="status ${classesSt}">${paciente.status}</span>
                <span class="id">#${paciente.numero_atendimento}</span>
                <button class="btn-status">${textoBt}</button>
            `;

            div.querySelector(".btn-status").addEventListener("click", function() {
                alterarStatus(paciente.id, proximoSt);
            });

            lista.appendChild(div);
        });

        document.getElementById("espera").innerText    = dados.filter(p => p.status !== "FINALIZADO").length;
        document.getElementById("graves").innerText    = graves;
        document.getElementById("atendidos").innerText = atendidos;

    } catch (erro) {
        console.error("Erro ao carregar fila:", erro);
    }
}

function classeStatus(status) {
    if (status === "FINALIZADO")     return "atendido";
    if (status === "EM ATENDIMENTO") return "atendimento";
    return "espera";
}

function textoBotao(status) {
    if (status === "EM ESPERA")      return "Chamar";
    if (status === "EM ATENDIMENTO") return "Finalizar";
    return "Finalizado";
}

function proximoStatus(status) {
    if (status === "EM ESPERA")      return "EM ATENDIMENTO";
    if (status === "EM ATENDIMENTO") return "FINALIZADO";
    return "FINALIZADO";
}

async function alterarStatus(id, status) {
    const token = localStorage.getItem("token");

    try {
        await fetch(`${API_URL}/triagem/status/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type":  "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ status })
        });

        carregarFila();

    } catch (erro) {
        console.error("Erro ao atualizar status:", erro);
    }
}

carregarFila();