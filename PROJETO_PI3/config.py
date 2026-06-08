import os

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "vital_class")

    SECRET_KEY = os.getenv("SECRET_KEY", "troque_essa_chave_em_producao")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500")