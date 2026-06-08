from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection
from utils.auth import gerar_token, token_obrigatorio

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/login", methods=["POST"])
def login():
    dados = request.json

    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM usuarios
            WHERE email = %s AND ativo = TRUE
        """, (email,))
        usuario = cursor.fetchone()

    conn.close()

    if not usuario or not check_password_hash(usuario["senha_hash"], senha):
        return jsonify({"erro": "Credenciais inválidas"}), 401

    token = gerar_token(usuario)

    return jsonify({
        "mensagem": "Login realizado com sucesso",
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"]
        }
    })


@usuarios_bp.route("/setup/primeiro-admin", methods=["POST"])
def criar_primeiro_admin():
    dados = request.json

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
            total = cursor.fetchone()["total"]

            if total > 0:
                return jsonify({"erro": "O primeiro administrador já foi criado"}), 403

            senha_hash = generate_password_hash(senha)

            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha_hash, perfil, ativo)
                VALUES (%s, %s, %s, 'ADMIN', TRUE)
            """, (nome, email, senha_hash))

        conn.commit()

        return jsonify({"mensagem": "Primeiro administrador criado com sucesso"}), 201

    finally:
        conn.close()


@usuarios_bp.route("/usuarios", methods=["POST"])
@token_obrigatorio(["ADMIN"])
def criar_usuario():
    dados = request.json

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")
    perfil = dados.get("perfil")

    if not nome or not email or not senha or not perfil:
        return jsonify({"erro": "Todos os campos são obrigatórios"}), 400

    if perfil not in ["ADMIN", "RECEPCAO", "ENFERMEIRO", "MEDICO"]:
        return jsonify({"erro": "Perfil inválido"}), 400

    senha_hash = generate_password_hash(senha)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha_hash, perfil, ativo)
                VALUES (%s, %s, %s, %s, TRUE)
            """, (nome, email, senha_hash, perfil))

        conn.commit()

        return jsonify({"mensagem": "Usuário criado com sucesso"}), 201

    except Exception as e:
        print(e)
        return jsonify({"erro": "Não foi possível criar usuário"}), 400

    finally:
        conn.close()