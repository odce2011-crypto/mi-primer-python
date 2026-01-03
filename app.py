from flask import Flask, render_template_string, request
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Función para conectar a PostgreSQL usando las variables de EasyPanel
def get_db_connection():
    # Usamos valores por defecto directos por si EasyPanel no lee las variables
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'n8n_postgres'),
        database=os.environ.get('DB_NAME', 'n8n'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'f98df37c825893961024'),
        port=5432
    )
    return conn

# Crear la tabla si no existe al arrancar
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS favoritos (
            id SERIAL PRIMARY KEY,
            serie_eq TEXT NOT NULL,
            serie_cz TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

def generar_melate():
    eq = sorted(random.sample(range(1, 57), 6))
    cz = sorted(random.sample(range(1, 57), 6))
    return eq, cz

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Cloud - Hostinger</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #eef2f3; padding-bottom: 50px; }
        .card { border-radius: 15px; border: none; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .ball { display: inline-block; width: 35px; height: 35px; line-height: 35px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; font-size: 0.8rem; border: 1px solid #d4ac0d; }
        .badge-num { background: #6c5ce7; color: white; padding: 5px 10px; border-radius: 5px; margin-right: 2px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container mt-5" style="max-width: 600px;">
        <div class="card p-4 mb-4 text-center">
            <h3>🎰 Melate con PostgreSQL</h3>
            <form method="POST">
                <button type="submit" name="accion" value="generar" class="btn btn-primary w-100 mb-3">Generar Números</button>
            </form>

            {% if eq %}
            <div class="bg-light p-3 rounded mb-3">
                <div class="mb-2"><strong>Equilibrio:</strong><br>
                    {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}
                </div>
                <div><strong>Cazadora:</strong><br>
                    {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}
                </div>
                <form method="POST" class="mt-3">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" name="accion" value="guardar" class="btn btn-success btn-sm">⭐ Guardar en Base de Datos</button>
                </form>
            </div>
            {% endif %}
        </div>

        <div class="card p-4">
            <h5 class="mb-3">⭐ Favoritos Guardados en la Nube</h5>
            {% for f in favs %}
            <div class="border-bottom py-2">
                <div class="mb-1">
                    <span class="text-muted small">Eq:</span>
                    {% for n in f.serie_eq.split(',') %}<span class="badge-num">{{n}}</span>{% endfor %}
                </div>
                <div>
                    <span class="text-muted small">Cz:</span>
                    {% for n in f.serie_cz.split(',') %}<span class="badge-num" style="background:#a29bfe;">{{n}}</span>{% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    eq, cz = None, None
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'generar':
            eq, cz = generar_melate()
        elif accion == 'guardar':
            cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', 
                        (request.form.get('num_eq'), request.form.get('num_cz')))
            conn.commit()

    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 10')
    favs = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, eq=eq, cz=cz, favs=favs)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

