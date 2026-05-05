const API_URL = "http://127.0.0.1:5005";

async function cadastrarUsuario() {
    const token = localStorage.getItem("token");

    const nome = document.getElementById("nome").value;
    const email = document.getElementById("email").value;
    const senha = document.getElementById("senha").value;
    const confirmar = document.getElementById("confirmarSenha").value;

    if (senha !== confirmar) {
        alert("Senhas não conferem");
        return;
    }

    try {
        const resposta = await fetch(`${API_URL}/usuarios`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
            nome: nome,
            email: email,
            senha: senha,
            perfil: "ADMIN"
          })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            alert(dados.erro);
            return;
        }

        alert("Usuário criado!");

    } catch (e) {
        console.error(e);
    }
}