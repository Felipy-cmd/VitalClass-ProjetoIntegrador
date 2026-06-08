from flask import Blueprint, request, jsonify
from db import get_connection
from utils.auth import token_obrigatorio
from utils.risco import classificar_risco

triagens_bp = Blueprint("triagens", __name__)

@triagens_bp.route("/atendimentos", methods=["POST"])
@token_obrigatorio(["ADMIN", "RECEPCAO"])
def criar_atendimento():
    dados = request.json

    paciente_id = dados.get("paciente_id")
    motivo_consulta = dados.get("motivo_consulta")

    if not paciente_id or not motivo_consulta:
        return jsonify({"erro": "Paciente e motivo da consulta são obrigatórios"}), 400

    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO atendimentos (paciente_id, motivo_consulta)
            VALUES (%s, %s)
        """, (paciente_id, motivo_consulta))

        atendimento_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": "Atendimento criado com sucesso",
        "atendimento_id": atendimento_id
    }), 201


@triagens_bp.route("/triagens", methods=["POST"])
@token_obrigatorio(["ADMIN", "ENFERMEIRO"])
def criar_triagem():
    dados = request.json

    atendimento_id = dados.get("atendimento_id")

    if not atendimento_id:
        return jsonify({"erro": "Atendimento é obrigatório"}), 400

    if not dados.get("sintoma_principal"):
        return jsonify({"erro": "Sintoma principal é obrigatório"}), 400

    classificacao = classificar_risco(dados)
    enfermeiro_id = request.usuario["id"]

    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO triagens (
                atendimento_id, enfermeiro_id, pressao_arterial,
                frequencia_cardiaca, temperatura, saturacao_oxigenio,
                frequencia_respiratoria, glicemia_capilar, sintoma_principal,
                descricao_sintomas, alergias, escala_dor, especialidade,
                protocolo_assistencial, descricao_protocolo, classificacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            atendimento_id,
            enfermeiro_id,
            dados.get("pressao_arterial"),
            dados.get("frequencia_cardiaca"),
            dados.get("temperatura"),
            dados.get("saturacao_oxigenio"),
            dados.get("frequencia_respiratoria"),
            dados.get("glicemia_capilar"),
            dados.get("sintoma_principal"),
            dados.get("descricao_sintomas"),
            dados.get("alergias"),
            dados.get("escala_dor"),
            dados.get("especialidade"),
            dados.get("protocolo_assistencial"),
            dados.get("descricao_protocolo"),
            classificacao
        ))

        cursor.execute("""
            UPDATE atendimentos
            SET status = 'AGUARDANDO_ATENDIMENTO'
            WHERE id = %s
        """, (atendimento_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": "Triagem registrada com sucesso",
        "classificacao": classificacao
    }), 201


@triagens_bp.route("/fila", methods=["GET"])
@token_obrigatorio(["ADMIN", "ENFERMEIRO", "MEDICO", "RECEPCAO"])
def listar_fila():
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.id AS atendimento_id,
                p.nome,
                p.sexo,
                p.data_nascimento,
                a.status,
                a.chegada_em,
                t.classificacao,
                t.sintoma_principal,
                t.especialidade
            FROM atendimentos a
            JOIN pacientes p ON p.id = a.paciente_id
            LEFT JOIN triagens t ON t.atendimento_id = a.id
            WHERE a.status IN ('EM_ESPERA', 'AGUARDANDO_ATENDIMENTO', 'EM_TRIAGEM')
            ORDER BY 
                CASE t.classificacao
                    WHEN 'VERMELHO' THEN 1
                    WHEN 'LARANJA' THEN 2
                    WHEN 'AMARELO' THEN 3
                    WHEN 'VERDE' THEN 4
                    WHEN 'AZUL' THEN 5
                    ELSE 6
                END,
                a.chegada_em ASC
        """)

        fila = cursor.fetchall()

    conn.close()
    return jsonify(fila)


@triagens_bp.route("/pacientes/<int:id>/historico", methods=["GET"])
@token_obrigatorio(["ADMIN", "ENFERMEIRO", "MEDICO"])
def historico_paciente(id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.id AS atendimento_id,
                a.status,
                a.motivo_consulta,
                a.chegada_em,
                t.classificacao,
                t.sintoma_principal,
                t.descricao_sintomas,
                t.alergias,
                t.especialidade,
                t.criada_em
            FROM atendimentos a
            LEFT JOIN triagens t ON t.atendimento_id = a.id
            WHERE a.paciente_id = %s
            ORDER BY a.chegada_em DESC
        """, (id,))

        historico = cursor.fetchall()

    conn.close()
    return jsonify(historico)


@triagens_bp.route("/atendimentos/<int:id>/atendido", methods=["PUT"])
@token_obrigatorio(["ADMIN", "MEDICO"])
def marcar_atendido(id):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE atendimentos
            SET status = 'ATENDIDO'
            WHERE id = %s
        """, (id,))

    conn.commit()
    conn.close()

    return jsonify({"mensagem": "Paciente marcado como atendido"})