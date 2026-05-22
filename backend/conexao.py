import psycopg2
from psycopg2.extras import RealDictCursor

def conectar():
    return psycopg2.connect(
        host="aws-1-us-west-2.pooler.supabase.com",
        database="postgres",
        user="postgres.omwbzyjknfqxzjsoimuq",
        password="Abc10203@30",
        port="5432",
        cursor_factory=RealDictCursor
    )