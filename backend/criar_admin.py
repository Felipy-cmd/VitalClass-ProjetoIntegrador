import bcrypt
from conexao import conectar

nome = "Admin"
email = "admin@email.com"
senha = "123456"
perfil = "ADMIN"

senha_hash = bcrypt.hashpw(
    senha.encode("utf-8"),
    bcrypt.gensalt()
).decode("utf-8")

conexao = conectar()
cursor = conexao.cursor()

sql = """
INSERT INTO usuarios (nome, email, senha, perfil)
VALUES (%s, %s, %s, %s)
"""

try:
    cursor.execute(sql, (nome, email, senha_hash, perfil))
    conexao.commit()
    print("Usuário admin criado com sucesso!")
    print("Email:", email)
    print("Senha:", senha)

except Exception as e:
    print("Erro ao criar admin:", e)

cursor.close()
conexao.close()