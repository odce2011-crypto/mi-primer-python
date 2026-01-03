from flask import Flask, render_template_string, request, redirect, url_for, session
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
# Clave para cifrar las sesiones (usamos la de EasyPanel o una por defecto)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-provisional-123')

# Credenciales de acceso
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

# --- DISEÑO HTML (LOGIN) ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso Privado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .card { border-radius: 20px; border: none; width: 100%; max-width: 380px; }
    </style>
</head>
<body>
    <div class="card shadow p-4">
        <h3 class="text-center mb-4">🔐 Melate Pro</h3>
        {% if error %}<div class="alert alert-danger p-2 small text-center">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Usuario</label>
                <input type="text" name="user" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Contraseña</label>
                <input type="password" name="pass" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Iniciar Sesión</button>
        </form>
    </div>
</body>
</html>
"""

# --- DISEÑO HTML (APP PRINCIPAL) ---
APP_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Cloud - Privado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #eef2f3; padding-bottom: 50px; }
        .card { border-radius: 15px; border: none; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .ball { display: inline-block; width: 32px; height: 32px; line-height: 32px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; font-size: 0.8rem; border: 1px solid #d4ac0d; }
        .badge-num { background: #6c5ce7; color: white; padding: 3px 8px; border-radius: 4px; margin-right: 2px; font-size: 0.85rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand">🎰 Melate Manager</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Cerrar Sesión</a>
        </div>
    </nav>
    <div class="container" style="max-width: 600px;">
        <div class="card p-4 mb-4 text-center">
            <form method="POST">
                <button type="submit" name="accion" value="generar" class="btn btn-primary w-100 mb-3">Generar Números</button>
            </form>

            {% if eq %}
            <div class="bg-light p-3 rounded">
                <div class="mb-2 text-start"><strong>Eq:</strong> {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <div class="text-start"><strong>Cz:</strong> {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <form method="POST" class="mt-3">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" name="accion" value="guardar" class="btn btn-success btn-sm w-100">⭐ Guardar Favorito</button>
                </form>
            </div>
            {% endif %}
        </div>

        <div class="card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="m-0">⭐ Mis Favoritos</h5>
                {% if favs %}<form action="/limpiar" method="POST"><button class="btn btn-outline-danger btn-sm">Limpiar</button></form>{% endif %}
            </div>
            {% for f in favs %}
            <div class="border-bottom py-2">
                <small class="text-muted d-block mb-1">{{ f.fecha.strftime('%d/%m %H:%M') }}</small>
                {% for n in f.serie_eq.split(',') %}<span class="badge-num">{{n}}</span>{% endfor %}
                <span class="mx-1">|</span>
                {% for n in f.serie_cz.split(',') %}<span class="badge-num" style="background:#a29bfe;">{{n}}</span>{% endfor %}
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        error = 'Credenciales inválidas'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
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
    return render_template_string(APP_HTML, eq=eq, cz=cz, favs=favs)

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
    # Importante: No llamamos a init_db aquí para evitar bloqueos en el arranque
    # si la conexión tarda. Pero asegúrate de que la tabla ya existe.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
