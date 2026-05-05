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
    cursor = conexao.cursor(dictionary=True)

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


@app.route("/triagem", methods=["POST"])
def cadastrar_triagem():
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    dados = request.get_json()

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT MAX(numero_atendimento) AS max_num FROM triagens")
    resultado = cursor.fetchone()

    numero_atendimento = 1

    if resultado["max_num"]:
        numero_atendimento = resultado["max_num"] + 1

    sql = """
    INSERT INTO triagens (
        nome, sexo, idade, data_hora, numero_atendimento,
        pressao, frequencia_cardiaca, temperatura, saturacao,
        freq_respiratoria, glicemia, sintoma, descricao,
        escala_dor, especialidade, protocolo, descricao_protocolo
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    valores = (
        dados.get("nome"),
        dados.get("sexo"),
        dados.get("idade"),
        datetime.datetime.now(),
        numero_atendimento,
        dados.get("pressao"),
        dados.get("frequencia_cardiaca"),
        dados.get("temperatura"),
        dados.get("saturacao"),
        dados.get("freq_respiratoria"),
        dados.get("glicemia"),
        dados.get("sintoma"),
        dados.get("descricao"),
        dados.get("escala_dor"),
        dados.get("especialidade"),
        dados.get("protocolo"),
        dados.get("descricao_protocolo"),
    )

    cursor.execute(sql, valores)
    conexao.commit()

    cursor.close()
    conexao.close()

    return jsonify({"mensagem": "Triagem cadastrada!"}), 201
if __name__ == "__main__":
    app.run(debug=True, port=5005)