from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
import jwt
import datetime
from conexao import conectar

app = Flask(__name__)
CORS(app)

CHAVE_SECRETA = "troque_essa_chave_por_uma_bem_segura"


def gerar_token(usuario):
    payload = {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "perfil": usuario["perfil"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }

    return jwt.encode(payload, CHAVE_SECRETA, algorithm="HS256")


def verificar_token():
    auth = request.headers.get("Authorization")

    if not auth:
        return None

    try:
        token = auth.replace("Bearer ", "")
        dados = jwt.decode(token, CHAVE_SECRETA, algorithms=["HS256"])
        return dados
    except:
        return None


@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json()

    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()

    cursor.close()
    conexao.close()

    if not usuario:
        return jsonify({"erro": "Usuário ou senha inválidos"}), 401

    senha_ok = bcrypt.checkpw(
        senha.encode("utf-8"),
        usuario["senha"].encode("utf-8")
    )

    if not senha_ok:
        return jsonify({"erro": "Usuário ou senha inválidos"}), 401

    token = gerar_token(usuario)

    return jsonify({
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"]
        }
    })


@app.route("/usuarios", methods=["POST"])
def cadastrar_usuario():
    usuario_logado = verificar_token()

    if not usuario_logado:
        return jsonify({"erro": "Token inválido ou não enviado"}), 401

    dados = request.get_json()

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")
    perfil = dados.get("perfil", "ADMIN")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    senha_hash = bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
        INSERT INTO usuarios (nome, email, senha, perfil)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (nome, email, senha_hash, perfil))
        conexao.commit()

        cursor.close()
        conexao.close()

        return jsonify({"mensagem": "Usuário cadastrado com sucesso"}), 201

    except Exception as e:
        return jsonify({"erro": "Erro ao cadastrar usuário"}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"mensagem": "Backend VitalClass rodando"})


def classificar_risco(dados):
    sintoma = (dados.get("sintoma") or "").lower()
    descricao = (dados.get("descricao") or "").lower()

    temperatura = float(dados.get("temperatura") or 0)
    saturacao = int(dados.get("saturacao") or 100)
    frequencia = int(dados.get("frequencia_cardiaca") or 0)
    dor = int(dados.get("escala_dor") or 0)

    texto = sintoma + " " + descricao

    if (
        "inconsciente" in texto
        or "parada" in texto
        or "convulsão" in texto
        or saturacao < 90
    ):
        return "VERMELHO"

    if (
        "falta de ar" in texto
        or "dor no peito" in texto
        or temperatura >= 39
        or dor >= 5
        or frequencia >= 130
    ):
        return "LARANJA"

    if (
        temperatura >= 38
        or "vômito" in texto
        or "tontura" in texto
        or dor >= 3
    ):
        return "AMARELO"

    if dor >= 1:
        return "VERDE"

    return "AZUL"

@app.route("/triagem", methods=["POST"])
def cadastrar_triagem():
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    dados = request.get_json()

    def vazio_para_none(valor):
        return None if valor == "" or valor is None else valor

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("SELECT MAX(numero_atendimento) AS max_num FROM triagens")
        resultado = cursor.fetchone()

        numero_atendimento = 1
        if resultado["max_num"]:
            numero_atendimento = resultado["max_num"] + 1
            classificacao = classificar_risco(dados)

        sql = """
INSERT INTO triagens (
    nome,
    sexo,
    idade,
    data_hora,
    numero_atendimento,
    pressao,
    frequencia_cardiaca,
    temperatura,
    saturacao,
    freq_respiratoria,
    glicemia,
    sintoma,
    descricao,
    escala_dor,
    especialidade,
    protocolo,
    descricao_protocolo,
    classificacao
)
VALUES (
    %s, %s, %s, NOW(), %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s
)
"""

        valores = (
    dados.get("nome"),
    dados.get("sexo"),
    vazio_para_none(dados.get("idade")),
    numero_atendimento,
    dados.get("pressao"),
    vazio_para_none(dados.get("frequencia_cardiaca")),
    vazio_para_none(dados.get("temperatura")),
    vazio_para_none(dados.get("saturacao")),
    vazio_para_none(dados.get("freq_respiratoria")),
    vazio_para_none(dados.get("glicemia")),
    dados.get("sintoma"),
    dados.get("descricao"),
    vazio_para_none(dados.get("escala_dor")),
    dados.get("especialidade"),
    dados.get("protocolo"),
    dados.get("descricao_protocolo"),
    classificacao
)

        cursor.execute(sql, valores)
        conexao.commit()

        return jsonify({
    "mensagem": "Triagem cadastrada!",
    "classificacao": classificacao
}), 201

    except Exception as e:
        conexao.rollback()
        print("ERRO AO CADASTRAR TRIAGEM:", e)
        return jsonify({"erro": "Erro ao cadastrar triagem"}), 500

    finally:
        cursor.close()
        conexao.close()
@app.route("/fila", methods=["GET"])
def listar_fila():
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT 
                id,
                nome,
                numero_atendimento,
                sintoma,
                classificacao,
                data_hora
            FROM triagens
            ORDER BY
                CASE classificacao
                    WHEN 'VERMELHO' THEN 1
                    WHEN 'LARANJA' THEN 2
                    WHEN 'AMARELO' THEN 3
                    WHEN 'VERDE' THEN 4
                    WHEN 'AZUL' THEN 5
                    ELSE 6
                END,
                data_hora ASC
        """)

        fila = cursor.fetchall()

        return jsonify(fila), 200

    except Exception as e:
        print("ERRO AO LISTAR FILA:", e)
        return jsonify({"erro": "Erro ao listar fila"}), 500

    finally:
        cursor.close()
        conexao.close()
if __name__ == "__main__":
    app.run(debug=True, port=5005)