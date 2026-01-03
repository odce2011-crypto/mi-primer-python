from flask import Flask, render_template_string, request, redirect, url_for, session
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-provisional-123')

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'melate2026')

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=5432
    )

# --- DISEÑO HTML ---
APP_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historial Melate - Privado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body { background: #f8f9fa; padding-bottom: 50px; }
        .card { border-radius: 15px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; font-size: 0.75rem; border: 1px solid #d4ac0d; }
        .badge-num { background: #6c5ce7; color: white; padding: 2px 6px; border-radius: 4px; margin-right: 2px; font-size: 0.8rem; }
        .ganador-row { background-color: #d1e7dd !important; border-left: 5px solid #198754 !important; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-primary mb-4 shadow-sm">
        <div class="container">
            <span class="navbar-brand">🎰 Melate Pro Historial</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Cerrar Sesión</a>
        </div>
    </nav>

    <div class="container" style="max-width: 650px;">
        <div class="card p-4 mb-4 text-center">
            <form method="POST">
                <button type="submit" name="accion" value="generar" class="btn btn-primary w-100 py-2">Generar Sorteo del Día</button>
            </form>
            {% if eq %}
            <div class="bg-light p-3 rounded mt-3 shadow-sm text-start">
                <div class="mb-2"><strong>Eq:</strong> {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <div><strong>Cz:</strong> {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <form method="POST" class="mt-3">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" name="accion" value="guardar" class="btn btn-success w-100">⭐ Guardar en Historial</button>
                </form>
            </div>
            {% endif %}
        </div>

        <div class="card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="m-0"><i class="bi bi-clock-history"></i> Historial de Jugadas</h5>
                <form action="/limpiar" method="POST" onsubmit="return confirm('¿Borrar todo el historial?')">
                    <button class="btn btn-sm text-danger"><i class="bi bi-trash"></i> Vaciar</button>
                </form>
            </div>

            {% for f in favs %}
            <div class="p-3 mb-2 rounded border shadow-sm {% if f.ganador %}ganador-row{% else %}bg-white{% endif %}">
                <div class="d-flex justify-content-between align-items-start">
                    <small class="text-muted">{{ f.fecha.strftime('%d %b, %H:%M') }}</small>
                    <form method="POST" action="/marcar_ganador">
                        <input type="hidden" name="id" value="{{ f.id }}">
                        <button type="submit" class="btn btn-sm {% if f.ganador %}btn-success{% else %}btn-outline-secondary{% endif %}">
                            <i class="bi bi-trophy"></i>
                        </button>
                    </form>
                </div>
                <div class="mt-2">
                    {% for n in f.serie_eq.split(',') %}<span class="badge-num">{{n}}</span>{% endfor %}
                    <span class="mx-1">|</span>
                    {% for n in f.serie_cz.split(',') %}<span class="badge-num" style="background:#a29bfe;">{{n}}</span>{% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

# LOGIN_HTML omitido por brevedad (usa el mismo que tenías)
# [Aquí pega el LOGIN_HTML del paso anterior]

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (mismo código de login que tenías) ...
    # Asegúrate de incluir el código de login que ya te funcionaba
    error = None
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        error = 'Credenciales inválidas'
    # Define LOGIN_HTML aquí o arriba
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
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

    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 20')
    favs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(APP_HTML, eq=eq, cz=cz, favs=favs)

@app.route('/marcar_ganador', methods=['POST'])
def marcar_ganador():
    if not session.get('logged_in'): return redirect(url_for('login'))
    id_fav = request.form.get('id')
    conn = get_db_connection()
    cur = conn.cursor()
    # Alternar entre ganador y no ganador
    cur.execute('UPDATE favoritos SET ganador = NOT ganador WHERE id = %s', (id_fav,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

@app.route('/limpiar', methods=['POST'])
def limpiar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM favoritos')
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
