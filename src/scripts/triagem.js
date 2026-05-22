const API_URL = "http://127.0.0.1:5005";

async function enviarTriagem() {
    const token = localStorage.getItem("token");

    const dados = {
    nome: document.getElementById("nome").value,
    sexo: document.getElementById("sexo").value,
    idade: document.getElementById("idade").value,
    pressao: document.getElementById("pressao").value,
    frequencia_cardiaca: document.getElementById("frequencia_cardiaca").value,
    temperatura: document.getElementById("temperatura").value,
    saturacao: document.getElementById("saturacao").value,
    freq_respiratoria: document.getElementById("freq_respiratoria").value,
    glicemia: document.getElementById("glicemia").value,
    sintoma: document.getElementById("sintoma").value,
    descricao: document.getElementById("descricao").value,
    escala_dor: document.getElementById("escalaDor").value,
    especialidade: document.getElementById("especialidade").value,
    protocolo: document.getElementById("protocolo").value,
    descricao_protocolo: document.getElementById("descricao_protocolo").value
};

    try {
        const resposta = await fetch(`${API_URL}/triagem`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(dados)
        });

        const res = await resposta.json();

        if (!resposta.ok) {
            alert(res.erro);
            return;
        }

        alert("Triagem cadastrada com sucesso!");

    } catch (e) {
        console.error(e);
    }
}
function formatarSinaisVitais(t) {
    return {
        temperatura: `${t.temperatura} °C`,
        frequencia_cardiaca: `${t.frequencia_cardiaca} BPM`,
        saturacao: `${t.saturacao}%`,
        pressao: `${t.pressao} mmHg`,
        freq_respiratoria: `${t.freq_respiratoria} irpm`,
        glicemia: `${t.glicemia} mg/dL`
    };
}