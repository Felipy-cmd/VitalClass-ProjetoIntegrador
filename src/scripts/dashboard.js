const API_URL = "http://127.0.0.1:5005";

async function carregarDashboard() {
    const token = localStorage.getItem("token");

    try {
        const resposta = await fetch(`${API_URL}/dashboard`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            console.error(dados);
            alert(dados.erro || "Erro ao carregar dashboard");
            return;
        }

        document.getElementById("totalTriagens").innerText = dados.total;
        document.getElementById("totalAtendidos").innerText = dados.atendidos;
        document.getElementById("totalEspera").innerText = dados.em_espera;
        document.getElementById("totalGraves").innerText = dados.graves;

        montarGrafico(dados.por_classificacao);
        montarListaProximos(dados.proximos);
        montarAlertas(dados);

    } catch (erro) {
        console.error("Erro dashboard:", erro);
    }
}

function montarGrafico(classificacoes) {
    const area = document.getElementById("graficoClassificacao");
    area.innerHTML = "";

    const maior = Math.max(...classificacoes.map(c => c.total), 1);

    classificacoes.forEach(item => {
        const classe = (item.classificacao || "sem").toLowerCase();
        const largura = (item.total / maior) * 100;

        area.innerHTML += `
            <div class="linha-grafico">
                <div class="grafico-info">
                    <span class="bolinha ${classe}"></span>
                    <strong>${item.classificacao || "Sem classificação"}</strong>
                    <small>${item.total} paciente(s)</small>
                </div>

                <div class="barra-fundo">
                    <div class="barra ${classe}" style="width:${largura}%"></div>
                </div>
            </div>
        `;
    });
}

function montarListaProximos(lista) {
    const area = document.getElementById("listaProximos");
    area.innerHTML = "";

    if (!lista || lista.length === 0) {
        area.innerHTML = "<p class='vazio'>Nenhum paciente aguardando.</p>";
        return;
    }

    lista.forEach(p => {
        const cor = (p.classificacao || "").toLowerCase();

        area.innerHTML += `
            <div class="item-paciente">
                <span class="bolinha ${cor}"></span>

                <div class="dados-paciente">
                    <strong>${p.nome}</strong>
                    <small>#${p.numero_atendimento} • ${p.sintoma || "Sem sintoma informado"}</small>
                </div>

                <span class="tag-status">${p.status}</span>
            </div>
        `;
    });
}

function montarAlertas(dados) {
    const area = document.getElementById("alertasDashboard");
    area.innerHTML = "";

    if (dados.graves > 0) {
        area.innerHTML += `
            <div class="alerta alerta-grave">
                <strong>Atenção:</strong> existem ${dados.graves} caso(s) grave(s) aguardando atendimento.
            </div>
        `;
    }

    if (dados.em_espera > 5) {
        area.innerHTML += `
            <div class="alerta alerta-medio">
                <strong>Fluxo elevado:</strong> há ${dados.em_espera} paciente(s) na fila.
            </div>
        `;
    }

    if (dados.em_espera === 0) {
        area.innerHTML += `
            <div class="alerta alerta-ok">
                Nenhum paciente aguardando atendimento no momento.
            </div>
        `;
    }
}

carregarDashboard();