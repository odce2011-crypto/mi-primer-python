import psycopg2
import os
from psycopg2.extras import RealDictCursor

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=5432
    )
    # Configuramos la zona horaria para esta conexión específica
    cur = conn.cursor()
    cur.execute("SET TIME ZONE 'America/Chicago';")
    cur.close()
    
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        es_admin BOOLEAN DEFAULT FALSE
    );''')
    
    # Hemos ajustado la columna fecha para que use TIMESTAMPTZ (con zona horaria)
    # Esto ayuda a que PostgreSQL sea más preciso
    cur.execute('''CREATE TABLE IF NOT EXISTS favoritos (
        id SERIAL PRIMARY KEY,
        serie_eq TEXT NOT NULL,
        serie_cz TEXT NOT NULL,
        fecha TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        ganador BOOLEAN DEFAULT FALSE
    );''')
    conn.commit()
    cur.close(); conn.close()
