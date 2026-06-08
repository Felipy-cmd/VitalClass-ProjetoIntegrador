from flask import Blueprint, request, jsonify
from db import get_connection
from utils.cpf import validar_cpf, limpar_cpf
from utils.auth import token_obrigatorio

pacientes_bp = Blueprint("pacientes", __name__)

@pacientes_bp.route("/pacientes", methods=["POST"])
@token_obrigatorio(["ADMIN", "RECEPCAO"])
def criar_paciente():
    dados = request.json

    nome = dados.get("nome")
    cpf = limpar_cpf(dados.get("cpf"))
    data_nascimento = dados.get("data_nascimento")
    sexo = dados.get("sexo")
    telefone = dados.get("telefone")

    if not nome or not cpf or not data_nascimento or not sexo:
        return jsonify({"erro": "Campos obrigatórios não preenchidos"}), 400

    if not validar_cpf(cpf):
        return jsonify({"erro": "CPF inválido"}), 400

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pacientes (nome, cpf, data_nascimento, sexo, telefone)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome, cpf, data_nascimento, sexo, telefone))

        conn.commit()
        return jsonify({"mensagem": "Paciente cadastrado com sucesso"}), 201

    except Exception:
        return jsonify({"erro": "CPF já cadastrado ou dados inválidos"}), 400

    finally:
        conn.close()


@pacientes_bp.route("/pacientes", methods=["GET"])
@token_obrigatorio(["ADMIN", "RECEPCAO", "ENFERMEIRO", "MEDICO"])
def listar_pacientes():
    busca = request.args.get("busca", "")

    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, nome, cpf, data_nascimento, sexo, telefone
            FROM pacientes
            WHERE nome LIKE %s OR cpf LIKE %s
            ORDER BY nome
        """, (f"%{busca}%", f"%{busca}%"))

        pacientes = cursor.fetchall()

    conn.close()

    return jsonify(pacientes)


@pacientes_bp.route("/pacientes/<int:id>", methods=["GET"])
@token_obrigatorio(["ADMIN", "RECEPCAO", "ENFERMEIRO", "MEDICO"])
def buscar_paciente(id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, nome, cpf, data_nascimento, sexo, telefone
            FROM pacientes
            WHERE id = %s
        """, (id,))

        paciente = cursor.fetchone()

    conn.close()

    if not paciente:
        return jsonify({"erro": "Paciente não encontrado"}), 404

    return jsonify(paciente)