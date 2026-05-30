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

    cursor.execute("SELECT * FROM usuarios WHERE email = %s AND ativo = TRUE", (email,))
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

    temperatura = float(dados.get("temperatura") or 0)
    saturacao = int(dados.get("saturacao") or 100)
    frequencia = int(dados.get("frequencia_cardiaca") or 0)
    dor = int(dados.get("escala_dor") or 0)

    # 🔴 VERMELHO
    if (
        sintoma == "convulsão"
        or sintoma == "desmaio"
        or saturacao < 90
    ):
        return "VERMELHO"

    # 🟠 LARANJA
    if (
        sintoma == "dor no peito"
        or sintoma == "falta de ar"
        or temperatura >= 39
        or frequencia >= 130
        or dor >= 5
    ):
        return "LARANJA"

    # 🟡 AMARELO
    if (
        sintoma == "febre"
        or sintoma == "vômito"
        or sintoma == "tontura"
        or temperatura >= 38
        or dor >= 3
    ):
        return "AMARELO"

    # 🟢 VERDE
    if (
        sintoma == "dor abdominal"
        or sintoma == "trauma"
        or dor >= 1
    ):
        return "VERDE"

    # 🔵 AZUL
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
                status,
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

        return jsonify({
            "erro": "Erro ao listar fila"
        }), 500

    finally:

        cursor.close()
        conexao.close()
@app.route("/triagem/status/<int:id>", methods=["PUT"])
def atualizar_status(id):

    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    dados = request.get_json()

    status = dados.get("status")

    if not status:
        return jsonify({
            "erro": "Status obrigatório"
        }), 400

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            UPDATE triagens
            SET status = %s
            WHERE id = %s
        """, (status, id))

        conexao.commit()

        return jsonify({
            "mensagem": "Status atualizado"
        }), 200

    except Exception as e:

        conexao.rollback()

        print("ERRO AO ATUALIZAR STATUS:", e)

        return jsonify({
            "erro": "Erro ao atualizar status"
        }), 500

    finally:

        cursor.close()
        conexao.close()
@app.route("/triagens/buscar", methods=["GET"])
def buscar_triagens():
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    termo = request.args.get("q", "")

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                nome,
                sexo,
                idade,
                numero_atendimento,
                sintoma,
                classificacao,
                status,
                data_hora
            FROM triagens
            WHERE 
                nome ILIKE %s
                OR CAST(numero_atendimento AS TEXT) ILIKE %s
            ORDER BY data_hora DESC
        """, (f"%{termo}%", f"%{termo}%"))

        triagens = cursor.fetchall()

        return jsonify(triagens), 200

    except Exception as e:
        print("ERRO AO BUSCAR TRIAGENS:", e)
        return jsonify({"erro": "Erro ao buscar triagens"}), 500

    finally:
        cursor.close()
        conexao.close()


@app.route("/paciente/<nome>/historico", methods=["GET"])
def historico_paciente(nome):
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM triagens
            WHERE nome = %s
            ORDER BY data_hora DESC
        """, (nome,))

        historico = cursor.fetchall()

        return jsonify(historico), 200

    except Exception as e:
        print("ERRO AO BUSCAR HISTÓRICO:", e)
        return jsonify({"erro": "Erro ao buscar histórico"}), 500

    finally:
        cursor.close()
        conexao.close()


@app.route("/triagem/<int:id>", methods=["GET"])
def buscar_triagem(id):
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM triagens
            WHERE id = %s
        """, (id,))

        triagem = cursor.fetchone()

        if not triagem:
            return jsonify({"erro": "Triagem não encontrada"}), 404

        return jsonify(triagem), 200

    except Exception as e:
        print("ERRO AO BUSCAR TRIAGEM:", e)
        return jsonify({"erro": "Erro ao buscar triagem"}), 500

    finally:
        cursor.close()
        conexao.close()


@app.route("/triagem/<int:id>", methods=["PUT"])
def editar_triagem(id):
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    if usuario["perfil"] not in ["ADMIN", "ENFERMEIRO"]:
        return jsonify({"erro": "Você não tem permissão para editar triagem"}), 403

    dados = request.get_json()

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE triagens
            SET
                nome = %s,
                sexo = %s,
                idade = %s,
                pressao = %s,
                frequencia_cardiaca = %s,
                temperatura = %s,
                saturacao = %s,
                freq_respiratoria = %s,
                glicemia = %s,
                sintoma = %s,
                descricao = %s,
                escala_dor = %s,
                especialidade = %s,
                protocolo = %s,
                descricao_protocolo = %s
            WHERE id = %s
        """, (
            dados.get("nome"),
            dados.get("sexo"),
            dados.get("idade"),
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
            id
        ))

        conexao.commit()

        return jsonify({"mensagem": "Triagem atualizada com sucesso"}), 200

    except Exception as e:
        conexao.rollback()
        print("ERRO AO EDITAR TRIAGEM:", e)
        return jsonify({"erro": "Erro ao editar triagem"}), 500

    finally:
        cursor.close()
        conexao.close()    

@app.route("/dashboard", methods=["GET"])
def dashboard():
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM triagens
        """)
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM triagens
            WHERE status = 'FINALIZADO'
        """)
        atendidos = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM triagens
            WHERE status != 'FINALIZADO'
        """)
        em_espera = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM triagens
            WHERE classificacao IN ('VERMELHO', 'LARANJA')
            AND status != 'FINALIZADO'
        """)
        graves = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT classificacao, COUNT(*) AS total
            FROM triagens
            GROUP BY classificacao
            ORDER BY
                CASE classificacao
                    WHEN 'VERMELHO' THEN 1
                    WHEN 'LARANJA' THEN 2
                    WHEN 'AMARELO' THEN 3
                    WHEN 'VERDE' THEN 4
                    WHEN 'AZUL' THEN 5
                    ELSE 6
                END
        """)
        por_classificacao = cursor.fetchall()

        cursor.execute("""
            SELECT
                id,
                nome,
                numero_atendimento,
                classificacao,
                status,
                sintoma,
                data_hora
            FROM triagens
            WHERE status != 'FINALIZADO'
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
            LIMIT 5
        """)
        proximos = cursor.fetchall()

        return jsonify({
            "total": total,
            "atendidos": atendidos,
            "em_espera": em_espera,
            "graves": graves,
            "por_classificacao": por_classificacao,
            "proximos": proximos
        }), 200

    except Exception as e:
        print("ERRO DASHBOARD:", e)
        return jsonify({"erro": "Erro ao carregar dashboard"}), 500

    finally:
        cursor.close()
        conexao.close()


@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    if usuario["perfil"] != "ADMIN":
        return jsonify({"erro": "Acesso negado"}), 403

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SELECT id, nome, email, perfil, ativo
            FROM usuarios
            ORDER BY nome
        """)

        return jsonify(cursor.fetchall()), 200

    finally:
        cursor.close()
        conexao.close()


@app.route("/usuarios/<int:id>", methods=["PUT"])
def editar_usuario(id):
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    if usuario["perfil"] != "ADMIN":
        return jsonify({"erro": "Acesso negado"}), 403

    dados = request.get_json()

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE usuarios
            SET nome = %s, email = %s, perfil = %s
            WHERE id = %s
        """, (
            dados.get("nome"),
            dados.get("email"),
            dados.get("perfil"),
            id
        ))

        conexao.commit()

        return jsonify({"mensagem": "Usuário atualizado"}), 200

    except Exception as e:
        conexao.rollback()
        print("ERRO EDITAR USUÁRIO:", e)
        return jsonify({"erro": "Erro ao editar usuário"}), 500

    finally:
        cursor.close()
        conexao.close()


@app.route("/usuarios/<int:id>/status", methods=["PUT"])
def alterar_status_usuario(id):
    usuario = verificar_token()

    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401

    if usuario["perfil"] != "ADMIN":
        return jsonify({"erro": "Acesso negado"}), 403

    dados = request.get_json()
    ativo = dados.get("ativo")

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE usuarios
            SET ativo = %s
            WHERE id = %s
        """, (ativo, id))

        conexao.commit()

        return jsonify({"mensagem": "Status alterado"}), 200

    finally:
        cursor.close()
        conexao.close()
if __name__ == "__main__":
    app.run(debug=True, port=5005)