import psycopg2
import os
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=5432
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        es_admin BOOLEAN DEFAULT FALSE
    );''')
    cur.execute('''CREATE TABLE IF NOT EXISTS favoritos (
        id SERIAL PRIMARY KEY,
        serie_eq TEXT NOT NULL,
        serie_cz TEXT NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ganador BOOLEAN DEFAULT FALSE
    );''')
    conn.commit()
    cur.close(); conn.close()
