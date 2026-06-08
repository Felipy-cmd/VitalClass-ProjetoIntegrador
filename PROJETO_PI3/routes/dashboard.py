from flask import Blueprint, jsonify
from db import get_connection
from utils.auth import token_obrigatorio

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET"])
@token_obrigatorio(["ADMIN", "ENFERMEIRO", "MEDICO", "RECEPCAO"])
def dashboard():
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM atendimentos WHERE status = 'ATENDIDO'")
        atendidos = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM atendimentos WHERE status IN ('EM_ESPERA', 'AGUARDANDO_ATENDIMENTO')")
        espera = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM triagens
            WHERE classificacao IN ('VERMELHO', 'LARANJA')
        """)
        graves = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT 
                a.id AS atendimento_id,
                p.nome,
                TIMESTAMPDIFF(MINUTE, a.chegada_em, NOW()) AS minutos_espera,
                t.classificacao
            FROM atendimentos a
            JOIN pacientes p ON p.id = a.paciente_id
            LEFT JOIN triagens t ON t.atendimento_id = a.id
            WHERE a.status IN ('EM_ESPERA', 'AGUARDANDO_ATENDIMENTO')
            HAVING minutos_espera >= 60
            ORDER BY minutos_espera DESC
        """)
        alertas = cursor.fetchall()

    conn.close()

    return jsonify({
        "pacientes_atendidos": atendidos,
        "pacientes_em_espera": espera,
        "pacientes_graves": graves,
        "alertas": alertas
    })