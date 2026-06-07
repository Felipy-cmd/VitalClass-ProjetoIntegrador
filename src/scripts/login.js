const API_URL = "http://127.0.0.1:5005";

async function fazerLogin() {
    const email = document.getElementById("email").value;
    const senha = document.getElementById("senha").value;
    const erro  = document.getElementById("erroLogin");

<<<<<<< Updated upstream
    // Esconde o erro antes de tentar
=======
>>>>>>> Stashed changes
    erro.classList.remove("visivel");

    try {
        const resposta = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, senha })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            erro.classList.add("visivel");
            return;
        }

        localStorage.setItem("token", dados.token);
        localStorage.setItem("usuario", JSON.stringify(dados.usuario));
        window.location.href = "home.html";

    } catch (e) {
        erro.classList.add("visivel");
        console.error(e);
    }
}

// Permite logar pressionando Enter
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("senha").addEventListener("keydown", (e) => {
        if (e.key === "Enter") fazerLogin();
    });
});
