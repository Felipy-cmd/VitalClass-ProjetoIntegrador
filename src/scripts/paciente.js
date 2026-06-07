const API_URL = "http://127.0.0.1:5005";

let triagemSelecionada = null;

function usuarioLogado() {
    return JSON.parse(localStorage.getItem("usuario"));
}

function podeEditar() {
    const usuario = usuarioLogado();

    if (!usuario) {
        return false;
    }

    return usuario.perfil === "ADMIN" || usuario.perfil === "ENFERMEIRO";
}

async function buscarTriagens() {
    const token = localStorage.getItem("token");
    const termo = document.getElementById("campoBusca").value.trim();

    try {
        const resposta = await fetch(`${API_URL}/triagens/buscar?q=${encodeURIComponent(termo)}`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const dados = await resposta.json();

        if (!Array.isArray(dados)) {
            console.error(dados);
            alert(dados.erro || "Erro ao buscar triagens");
            return;
        }

        renderizarLista(dados);

    } catch (erro) {
        console.error("Erro ao buscar triagens:", erro);
    }
}

function renderizarLista(dados) {
    const lista = document.getElementById("list");
    lista.innerHTML = "";

    if (dados.length === 0) {
        lista.innerHTML = "<p style='color:#aaa;'>Nenhuma triagem encontrada.</p>";
        return;
    }

    dados.forEach(triagem => {
        const cor = (triagem.classificacao || "").toLowerCase();

        lista.innerHTML += `
            <div class="paciente" onclick="selecionarTriagem(${triagem.id})">
                <span class="urgente ${cor}"></span>
                <p class="nome">${triagem.nome}</p>
                <span class="hora">#${triagem.numero_atendimento}</span>
                <span class="data">${formatarData(triagem.data_hora)}</span>
            </div>
        `;
    });
}

async function selecionarTriagem(id) {
    const token = localStorage.getItem("token");

    try {
        const resposta = await fetch(`${API_URL}/triagem/${id}`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const triagem = await resposta.json();

        if (!resposta.ok) {
            alert(triagem.erro || "Erro ao carregar triagem");
            return;
        }

        triagemSelecionada = triagem;

        preencherCampos(triagem);
        carregarHistoricoPaciente(triagem.nome);

    } catch (erro) {
        console.error("Erro ao selecionar triagem:", erro);
    }
}

async function carregarHistoricoPaciente(nome) {
    const token = localStorage.getItem("token");

    try {
        const resposta = await fetch(`${API_URL}/paciente/${encodeURIComponent(nome)}/historico`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const historico = await resposta.json();

        if (!Array.isArray(historico)) {
            console.error(historico);
            return;
        }

        renderizarLista(historico);

    } catch (erro) {
        console.error("Erro ao carregar histórico:", erro);
    }
}

function preencherCampos(t) {
    document.getElementById("nomePaciente").value = t.nome || "";
    document.getElementById("sexoPaciente").value = t.sexo || "";
    document.getElementById("idadePaciente").value = t.idade || "";
    document.getElementById("classificacaoPaciente").value = t.classificacao || "";
    document.getElementById("statusPaciente").value = t.status || "";
    document.getElementById("atendimentoPaciente").value = t.numero_atendimento || "";

    const btnEditar = document.getElementById("btnEditar");

    if (!podeEditar()) {
        btnEditar.style.display = "none";
    }
}

function habilitarEdicao() {
    if (!triagemSelecionada) {
        alert("Selecione uma triagem primeiro.");
        return;
    }

    if (!podeEditar()) {
        alert("Você não tem permissão para editar.");
        return;
    }

    document.getElementById("nomePaciente").removeAttribute("readonly");
    document.getElementById("sexoPaciente").removeAttribute("readonly");
    document.getElementById("idadePaciente").removeAttribute("readonly");

    document.getElementById("btnSalvar").style.display = "inline-block";
}

async function salvarEdicao() {
    const token = localStorage.getItem("token");

    if (!triagemSelecionada) {
        alert("Selecione uma triagem primeiro.");
        return;
    }

    const dados = {
        ...triagemSelecionada,
        nome: document.getElementById("nomePaciente").value,
        sexo: document.getElementById("sexoPaciente").value,
        idade: document.getElementById("idadePaciente").value
    };

    try {
        const resposta = await fetch(`${API_URL}/triagem/${triagemSelecionada.id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(dados)
        });

        const res = await resposta.json();

        if (!resposta.ok) {
            alert(res.erro || "Erro ao salvar alterações");
            return;
        }
        

        alert("Alterações salvas com sucesso.");
        document.getElementById("btnSalvar").style.display = "none";

        buscarTriagens();

    } catch (erro) {
        console.error("Erro ao salvar edição:", erro);
    }
}

function gerarRelatorio() {
    if (!triagemSelecionada) {
        alert("Selecione uma triagem primeiro.");
        return;
    }

    const t = triagemSelecionada;

    const relatorio = `
RELATÓRIO DE TRIAGEM - VITALCLASS

Paciente: ${t.nome}
Sexo: ${t.sexo}
Idade: ${t.idade}
Nº Atendimento: #${t.numero_atendimento}
Data/Hora: ${formatarData(t.data_hora)}

CLASSIFICAÇÃO DE RISCO
Classificação: ${t.classificacao}
Status: ${t.status}

SINAIS VITAIS
Temperatura: ${t.temperatura} °C
FC: ${t.frequencia_cardiaca} BPM
Saturação: ${t.saturacao}%
Pressão: ${t.pressao} mmHg
Frequência Respiratória: ${t.freq_respiratoria} irpm
Glicemia Capilar: ${t.glicemia} mg/dL

SINTOMA PRINCIPAL
${t.sintoma}

DESCRIÇÃO / ALERGIAS
${t.descricao}

ESPECIALIDADE
${t.especialidade}

PROTOCOLO ASSISTENCIAL
${t.protocolo}

DESCRIÇÃO DO PROTOCOLO
${t.descricao_protocolo}
`;

    const janela = window.open("", "_blank");
    janela.document.write(`
        <html>
        <head>
            <title>Relatório de Triagem</title>
        </head>
        <body>
            <pre>${relatorio}</pre>
        </body>
        </html>
    `);
    janela.document.close();
    janela.print();
}

function formatarData(data) {
    if (!data) return "";
    return new Date(data).toLocaleString("pt-BR");
}

buscarTriagens();