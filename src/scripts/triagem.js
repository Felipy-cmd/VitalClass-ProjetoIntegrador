const API_URL = "http://127.0.0.1:5005";

if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}

function selecionarDor(botao, nivel) {
    document.querySelectorAll('.face').forEach(b => b.classList.remove('selecionado'));
    botao.classList.add('selecionado');
    document.getElementById('escalaDor').value = nivel;
}

function coletarCheckboxes() {
    return Array.from(
        document.querySelectorAll('.cb-grid input[type=checkbox]:checked')
    ).map(cb => cb.value);
}

function detectarProtocolo() {
    const s    = coletarCheckboxes();
    const sist = parseInt(document.getElementById('pressao_sistolica').value) || 0;
    const fc   = parseInt(document.getElementById('frequencia_cardiaca').value) || 0;
    const fr   = parseInt(document.getElementById('freq_respiratoria').value) || 0;
    const temp = parseFloat(document.getElementById('temperatura').value) || 0;

    let proto = null, classe = null;

    const iamCrit = ['dor_peito','dor_peito_braco','dor_peito_dorso'];
    const iamAll  = ['dor_peito','dor_peito_braco','dor_peito_dorso','falta_ar','nausea','sudorese'];
    const iamSc   = iamAll.filter(x => s.includes(x)).length;
    if (iamCrit.some(x => s.includes(x)) || iamSc >= 2) {
        proto = 'IAM';
        const verm = (s.includes('dor_peito') || s.includes('dor_peito_braco')) && s.includes('falta_ar') && iamSc >= 3;
        classe = verm ? 'VERMELHO' : 'LARANJA';
    }

    const avcCrit = ['desmaio_consciencia','crise_convulsiva','perda_forca'];
    const avcAll  = ['cefaleia_intensa','perda_forca','dormencia_subita','dificuldade_falar','dificuldade_compreender','perda_visao','desmaio_consciencia','crise_convulsiva'];
    const avcSc   = avcAll.filter(x => s.includes(x)).length;
    if (avcSc >= 1 && !proto) {
        proto  = 'AVC';
        classe = avcCrit.some(x => s.includes(x)) ? 'VERMELHO' : 'LARANJA';
    }

    const sepseSint = ['confusao_mental','sonolencia','desorientacao','hipertermia','sudorese_sepse'];
    const sepseSc   = sepseSint.filter(x => s.includes(x)).length;
    const svSepse   = (sist > 0 && sist <= 100) || fc > 90 || fr > 20 || temp >= 38.3;
    if (((sepseSc >= 1 && svSepse) || sepseSc >= 2) && !proto) {
        proto = 'SEPSE';
        const choque = sist > 0 && sist <= 90 && fc > 100 && ['confusao_mental','desorientacao','sonolencia'].some(x => s.includes(x));
        classe = choque ? 'VERMELHO' : 'LARANJA';
    }

    const el = document.getElementById('proto-resultado');
    if (proto) {
        const ic = { IAM: '❤️', AVC: '🧠', SEPSE: '🦠' };
        const cr = { VERMELHO: '🔴', LARANJA: '🟠', AMARELO: '🟡' };
        el.textContent = `${ic[proto]} Protocolo ${proto} detectado — ${cr[classe]} ${classe}`;
        el.className   = `proto-resultado ativo ${proto.toLowerCase()}`;
    } else {
        el.textContent = 'Nenhum protocolo detectado — preencha os sintomas e sinais vitais acima';
        el.className   = 'proto-resultado';
    }
}

async function enviarTriagem() {
    const token = localStorage.getItem("token");
    const nome  = document.getElementById("nome").value.trim();

    if (!nome) {
        alert("Informe o nome do paciente.");
        document.getElementById("nome").focus();
        return;
    }

    const sist  = document.getElementById("pressao_sistolica").value;
    const diast = document.getElementById("pressao_diastolica").value;
    const pressao = (sist && diast) ? `${sist}/${diast}` : (sist || "");

    const dados = {
        nome,
        sexo:                document.getElementById("sexo").value,
        idade:               document.getElementById("idade").value,
        cpf:                 document.getElementById("cpf").value.trim(),
        telefone:            document.getElementById("telefone").value.trim(),
        pressao,
        pressao_sistolica:   sist,
        frequencia_cardiaca: document.getElementById("frequencia_cardiaca").value,
        temperatura:         document.getElementById("temperatura").value,
        saturacao:           document.getElementById("saturacao").value,
        freq_respiratoria:   document.getElementById("freq_respiratoria").value,
        glicemia:            document.getElementById("glicemia").value,
        sintomas_checkboxes: coletarCheckboxes(),
        sintoma: coletarCheckboxes().join(", "),
        descricao:           document.getElementById("descricao").value,
        escala_dor:          document.getElementById("escalaDor").value,
        especialidade:       document.getElementById("especialidade").value,
        descricao_protocolo: document.getElementById("descricao_protocolo").value,
    };

    try {
        const resposta = await fetch(`${API_URL}/triagem`, {
            method: "POST",
            headers: {
                "Content-Type":  "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(dados)
        });

        const res = await resposta.json();

        // ── CPF já cadastrado ──
        if (resposta.status === 409) {
            const confirmar = confirm(
                `⚠️ Este CPF já possui uma triagem cadastrada.\n\nDeseja cadastrar mesmo assim?`
            );
            if (!confirmar) return;

            // Reenvia ignorando checagem de CPF
            dados.ignorar_cpf_duplicado = true;
            const r2 = await fetch(`${API_URL}/triagem`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
                body: JSON.stringify(dados)
            });
            const res2 = await r2.json();
            if (!r2.ok) { alert("Erro: " + (res2.erro || "Falha ao cadastrar.")); return; }
            alert(`✅ Triagem cadastrada!\nClassificação: ${res2.classificacao}`);
            window.location.href = "home.html";
            return;
        }

        if (!resposta.ok) {
            alert("Erro: " + (res.erro || "Falha ao cadastrar triagem."));
            return;
        }

        const proto = res.protocolo ? ` | Protocolo: ${res.protocolo}` : "";
        alert(`✅ Triagem cadastrada!\nClassificação: ${res.classificacao}${proto}`);
        window.location.href = "home.html";

    } catch (e) {
        console.error(e);
        alert("Erro de conexão com o servidor.");
    }
}