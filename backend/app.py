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
    senha_ok = bcrypt.checkpw(senha.encode("utf-8"), usuario["senha"].encode("utf-8"))
    if not senha_ok:
        return jsonify({"erro": "Usuário ou senha inválidos"}), 401
    token = gerar_token(usuario)
    return jsonify({"token": token, "usuario": {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"], "perfil": usuario["perfil"]}})

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
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO usuarios (nome, email, senha, perfil) VALUES (%s, %s, %s, %s)", (nome, email, senha_hash, perfil))
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
    sintoma     = (dados.get("sintoma") or "").lower()
    temperatura = float(dados.get("temperatura") or 0)
    saturacao   = int(dados.get("saturacao") or 100)
    frequencia  = int(dados.get("frequencia_cardiaca") or 0)
    dor         = int(dados.get("escala_dor") or 0)
    if sintoma in ("convulsão", "desmaio") or saturacao < 90:
        return "VERMELHO"
    if sintoma in ("dor no peito", "falta de ar") or temperatura >= 39 or frequencia >= 130 or dor >= 5:
        return "LARANJA"
    if sintoma in ("febre", "vômito", "tontura") or temperatura >= 38 or dor >= 3:
        return "AMARELO"
    if sintoma in ("dor abdominal", "trauma") or dor >= 1:
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
    cursor  = conexao.cursor()

    try:
        cursor.execute("SELECT MAX(numero_atendimento) AS max_num FROM triagens")
        resultado = cursor.fetchone()
        numero_atendimento = (resultado["max_num"] or 0) + 1
        classificacao = classificar_risco(dados)

        sql = """
            INSERT INTO triagens (
                nome, sexo, idade, data_hora, numero_atendimento,
                pressao, frequencia_cardiaca, temperatura, saturacao,
                freq_respiratoria, glicemia, sintoma, descricao,
                escala_dor, especialidade, protocolo, descricao_protocolo,
                classificacao
            ) VALUES (
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
        return jsonify({"mensagem": "Triagem cadastrada!", "classificacao": classificacao}), 201

    except Exception as e:
        conexao.rollback()
        print("ERRO AO CADASTRAR TRIAGEM:", e)
        return jsonify({"erro": "Erro ao cadastrar triagem"}), 500

    finally:
        cursor.close()
        conexao.close()

@app.route("/triagem/<int:id>", methods=["DELETE"])
def deletar_triagem(id):
    usuario = verificar_token()
    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401
    conexao = conectar()
    cursor  = conexao.cursor()
    try:
        cursor.execute("DELETE FROM triagens WHERE id = %s", (id,))
        conexao.commit()
        return jsonify({"mensagem": "Triagem deletada"}), 200
    except Exception as e:
        conexao.rollback()
        print("ERRO AO DELETAR TRIAGEM:", e)
        return jsonify({"erro": "Erro ao deletar triagem"}), 500
    finally:
        cursor.close()
        conexao.close()

@app.route("/fila", methods=["GET"])
def listar_fila():
    usuario = verificar_token()
    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401
    conexao = conectar()
    cursor  = conexao.cursor()
    try:
        cursor.execute("""
            SELECT id, nome, numero_atendimento, sintoma,
                   classificacao, status, data_hora
            FROM triagens
            WHERE data_hora >= NOW() - INTERVAL '24 hours'
            ORDER BY
                CASE classificacao
                    WHEN 'VERMELHO' THEN 1
                    WHEN 'LARANJA'  THEN 2
                    WHEN 'AMARELO'  THEN 3
                    WHEN 'VERDE'    THEN 4
                    WHEN 'AZUL'     THEN 5
                    ELSE 6
                END,
                data_hora ASC
        """)
        fila = cursor.fetchall()
        for p in fila:
            if p.get("data_hora"):
                p["data_hora"] = p["data_hora"].isoformat()
        return jsonify(fila), 200
    except Exception as e:
        print("ERRO AO LISTAR FILA:", e)
        return jsonify({"erro": "Erro ao listar fila"}), 500
    finally:
        cursor.close()
        conexao.close()

@app.route("/triagem/status/<int:id>", methods=["PUT"])
def atualizar_status(id):
    usuario = verificar_token()
    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401
    dados  = request.get_json()
    status = dados.get("status")
    if not status:
        return jsonify({"erro": "Status obrigatório"}), 400
    conexao = conectar()
    cursor  = conexao.cursor()
    try:
        cursor.execute("UPDATE triagens SET status = %s WHERE id = %s", (status, id))
        conexao.commit()
        return jsonify({"mensagem": "Status atualizado"}), 200
    except Exception as e:
        conexao.rollback()
        print("ERRO AO ATUALIZAR STATUS:", e)
        return jsonify({"erro": "Erro ao atualizar status"}), 500
    finally:
        cursor.close()
        conexao.close()

@app.route("/pacientes", methods=["GET"])
def buscar_pacientes():
    usuario = verificar_token()
    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401
    nome = request.args.get("nome", "").strip()
    if not nome:
        return jsonify([]), 200
    conexao = conectar()
    cursor  = conexao.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT ON (nome)
                nome, sexo, idade, classificacao,
                data_hora AS ultima_triagem
            FROM triagens
            WHERE nome ILIKE %s
            ORDER BY nome, data_hora DESC
        """, (f"%{nome}%",))
        pacientes = cursor.fetchall()
        for p in pacientes:
            if p.get("ultima_triagem"):
                p["ultima_triagem"] = p["ultima_triagem"].isoformat()
        return jsonify(pacientes), 200
    except Exception as e:
        print("ERRO AO BUSCAR PACIENTES:", e)
        return jsonify({"erro": "Erro ao buscar pacientes"}), 500
    finally:
        cursor.close()
        conexao.close()

@app.route("/pacientes/<string:nome>/triagens", methods=["GET"])
def historico_paciente(nome):
    usuario = verificar_token()
    if not usuario:
        return jsonify({"erro": "Token inválido"}), 401
    conexao = conectar()
    cursor  = conexao.cursor()
    try:
        cursor.execute("""
            SELECT id, classificacao, protocolo, status, data_hora,
                   escala_dor, sintoma, descricao, especialidade
            FROM triagens
            WHERE nome ILIKE %s
            ORDER BY data_hora DESC
        """, (nome,))
        triagens = cursor.fetchall()
        for t in triagens:
            if t.get("data_hora"):
                t["data_hora"] = t["data_hora"].isoformat()
        return jsonify(triagens), 200
    except Exception as e:
        print("ERRO AO BUSCAR HISTÓRICO:", e)
        return jsonify({"erro": "Erro ao buscar histórico"}), 500
    finally:
        cursor.close()
        conexao.close()

if __name__ == "__main__":
    app.run(debug=True, port=5005)