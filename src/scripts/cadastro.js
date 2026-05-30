const API_URL = "http://127.0.0.1:5005";

function usuarioLogado() {
    return JSON.parse(localStorage.getItem("usuario"));
}

function verificarPermissaoAdmin() {
    const usuario = usuarioLogado();

    if (!usuario || usuario.perfil !== "ADMIN") {
        alert("Apenas administradores podem acessar esta tela.");
        window.location.href = "home.html";
    }
}

async function salvarUsuario() {
    const id = document.getElementById("usuarioId").value;
    const nome = document.getElementById("nome").value.trim();
    const email = document.getElementById("email").value.trim();
    const perfil = document.getElementById("perfil").value;
    const senha = document.getElementById("senha").value;
    const confirmar = document.getElementById("confirmarSenha").value;
    const token = localStorage.getItem("token");

    if (!nome || !email || !perfil) {
        alert("Preencha nome, email e perfil.");
        return;
    }

    if (!id) {
        if (!senha || !confirmar) {
            alert("Preencha a senha.");
            return;
        }

        if (senha !== confirmar) {
            alert("Senhas não conferem.");
            return;
        }

        await cadastrarUsuario(nome, email, senha, perfil, token);
    } else {
        await editarUsuario(id, nome, email, perfil, token);
    }
}

async function cadastrarUsuario(nome, email, senha, perfil, token) {
    try {
        const resposta = await fetch(`${API_URL}/usuarios`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ nome, email, senha, perfil })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro || "Erro ao cadastrar usuário.");
            return;
        }

        alert("Usuário cadastrado com sucesso.");
        limparFormulario();
        carregarUsuarios();

    } catch (e) {
        console.error(e);
    }
}

async function editarUsuario(id, nome, email, perfil, token) {
    try {
        const resposta = await fetch(`${API_URL}/usuarios/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ nome, email, perfil })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro || "Erro ao editar usuário.");
            return;
        }

        alert("Usuário atualizado.");
        limparFormulario();
        carregarUsuarios();

    } catch (e) {
        console.error(e);
    }
}

async function carregarUsuarios() {
    const token = localStorage.getItem("token");

    try {
        const resposta = await fetch(`${API_URL}/usuarios`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const dados = await resposta.json();

        if (!Array.isArray(dados)) {
            console.error(dados);
            return;
        }

        const lista = document.getElementById("listaUsuarios");
        lista.innerHTML = "";

        dados.forEach(usuario => {
            lista.innerHTML += `
                <div class="usuario-card">
                    <div>
                        <strong>${usuario.nome}</strong>
                        <p>${usuario.email}</p>
                        <span>${usuario.perfil}</span>
                    </div>

                    <div class="acoes">
                        <span class="${usuario.ativo ? 'ativo' : 'inativo'}">
                            ${usuario.ativo ? 'ATIVO' : 'INATIVO'}
                        </span>

                        <button onclick="prepararEdicao(
                            ${usuario.id},
                            '${usuario.nome}',
                            '${usuario.email}',
                            '${usuario.perfil}'
                        )">
                            Editar
                        </button>

                        <button onclick="alterarStatus(${usuario.id}, ${!usuario.ativo})">
                            ${usuario.ativo ? 'Desativar' : 'Ativar'}
                        </button>
                    </div>
                </div>
            `;
        });

    } catch (e) {
        console.error(e);
    }
}

function prepararEdicao(id, nome, email, perfil) {
    document.getElementById("usuarioId").value = id;
    document.getElementById("nome").value = nome;
    document.getElementById("email").value = email;
    document.getElementById("perfil").value = perfil;

    document.getElementById("senha").value = "";
    document.getElementById("confirmarSenha").value = "";

    document.getElementById("senha").disabled = true;
    document.getElementById("confirmarSenha").disabled = true;
}

async function alterarStatus(id, ativo) {
    const token = localStorage.getItem("token");

    try {
        const resposta = await fetch(`${API_URL}/usuarios/${id}/status`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ ativo })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro || "Erro ao alterar status.");
            return;
        }

        carregarUsuarios();

    } catch (e) {
        console.error(e);
    }
}

function limparFormulario() {
    document.getElementById("usuarioId").value = "";
    document.getElementById("nome").value = "";
    document.getElementById("email").value = "";
    document.getElementById("perfil").value = "ADMIN";
    document.getElementById("senha").value = "";
    document.getElementById("confirmarSenha").value = "";

    document.getElementById("senha").disabled = false;
    document.getElementById("confirmarSenha").disabled = false;
}

verificarPermissaoAdmin();
carregarUsuarios();