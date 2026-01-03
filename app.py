from flask import Flask, render_template_string, request, redirect, url_for
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Conexión profesional con Variables de Entorno
def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=5432
    )

# Inicializar tabla
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Pro - Hostinger</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #eef2f3; padding: 30px 0; }
        .card { border-radius: 15px; border: none; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .ball { display: inline-block; width: 32px; height: 32px; line-height: 32px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; font-size: 0.8rem; border: 1px solid #d4ac0d; }
        .badge-num { background: #6c5ce7; color: white; padding: 3px 8px; border-radius: 4px; margin-right: 2px; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="container" style="max-width: 600px;">
        <div class="card p-4 mb-4 text-center">
            <h3>🎰 Generador de Sorteos</h3>
            <form method="POST" action="/">
                <button type="submit" name="accion" value="generar" class="btn btn-primary w-100 mb-3">Generar Números</button>
            </form>

            {% if eq %}
            <div class="bg-light p-3 rounded">
                <div class="mb-2"><strong>Eq:</strong> {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <div><strong>Cz:</strong> {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <form method="POST" action="/" class="mt-3">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" name="accion" value="guardar" class="btn btn-success btn-sm">⭐ Guardar Favorito</button>
                </form>
            </div>
            {% endif %}
        </div>

        <div class="card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="m-0">⭐ Mis Favoritos (DB)</h5>
                {% if favs %}
                <form method="POST" action="/limpiar">
                    <button type="submit" class="btn btn-outline-danger btn-sm">Limpiar Todo</button>
                </form>
                {% endif %}
            </div>

            {% if not favs %}
                <p class="text-muted text-center">No hay series guardadas en PostgreSQL.</p>
            {% else %}
                {% for f in favs %}
                <div class="border-bottom py-2">
                    <small class="text-muted">{{ f.fecha.strftime('%d/%m %H:%M') }}</small><br>
                    {% for n in f.serie_eq.split(',') %}<span class="badge-num">{{n}}</span>{% endfor %}
                    <span class="mx-1">|</span>
                    {% for n in f.serie_cz.split(',') %}<span class="badge-num" style="background:#a29bfe;">{{n}}</span>{% endfor %}
                </div>
                {% endfor %}
            {% endif %}
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
            eq = sorted(random.sample(range(1, 57), 6))
            cz = sorted(random.sample(range(1, 57), 6))
        elif accion == 'guardar':
            cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', 
                        (request.form.get('num_eq'), request.form.get('num_cz')))
            conn.commit()

    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 10')
    favs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(HTML_TEMPLATE, eq=eq, cz=cz, favs=favs)

@app.route('/limpiar', methods=['POST'])
def limpiar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM favoritos')
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
