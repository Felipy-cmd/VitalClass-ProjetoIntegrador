import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config


def gerar_token(usuario):
    payload = {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "perfil": usuario["perfil"],
        "exp": datetime.utcnow() + timedelta(hours=8)
    }

    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")


def token_obrigatorio(perfis_permitidos=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return jsonify({"erro": "Token não enviado"}), 401

            try:
                partes = auth_header.split(" ")

                if len(partes) != 2 or partes[0] != "Bearer":
                    return jsonify({"erro": "Formato do token inválido"}), 401

                token = partes[1]

                usuario = jwt.decode(
                    token,
                    Config.SECRET_KEY,
                    algorithms=["HS256"]
                )

                if perfis_permitidos and usuario["perfil"] not in perfis_permitidos:
                    return jsonify({"erro": "Acesso negado"}), 403

                request.usuario = usuario

            except jwt.ExpiredSignatureError:
                return jsonify({"erro": "Token expirado"}), 401

            except Exception:
                return jsonify({"erro": "Token inválido"}), 401

            return func(*args, **kwargs)

        return wrapper
    return decorator