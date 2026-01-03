from flask import Flask, render_template_string, request, redirect, url_for, session
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

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

# --- COMPONENTE: MENÚ DE NAVEGACIÓN ---
def get_navbar():
    return """
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <a class="navbar-brand" href="/">🎰 Melate Pro</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Generador</a></li>
                    <li class="nav-item"><a class="nav-link" href="/resultados">Historial</a></li>
                    <li class="nav-item"><a class="nav-link" href="/estadisticas">Estadísticas</a></li>
                </ul>
                <div class="d-flex">
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
                </div>
            </div>
        </div>
    </nav>
    """

# --- DISEÑO HTML: LOGIN ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso Privado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #f0f2f5; height: 100vh; display: flex; align-items: center; justify-content: center; }</style>
</head>
<body>
    <div class="card shadow p-4" style="max-width: 350px; width: 100%;">
        <h3 class="text-center mb-4">🔐 Melate Login</h3>
        {% if error %}<div class="alert alert-danger p-2 small text-center">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="mb-3"><label class="form-label">Usuario</label><input type="text" name="user" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Contraseña</label><input type="password" name="pass" class="form-control" required></div>
            <button type="submit" class="btn btn-primary w-100">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

# --- PÁGINA 1: GENERADOR ---
GEN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <style>.ball { display: inline-block; width: 35px; height: 35px; line-height: 35px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; border: 1px solid #d4ac0d; }</style>
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container" style="max-width: 600px;">
        <div class="card p-4 shadow mb-4 text-center">
            <h3>🎰 Generador de Series</h3>
            <p class="text-muted">Basado en Equilibrio y Cazadora</p>
            <form method="POST" action="/generar">
                <button type="submit" class="btn btn-primary btn-lg w-100 mb-3">¡Generar Números!</button>
            </form>
            {% if eq %}
            <div class="bg-white p-3 rounded border text-start">
                <div class="mb-2"><strong>Eq:</strong> {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <div class="mb-3"><strong>Cz:</strong> {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <form method="POST" action="/guardar">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" class="btn btn-success w-100">Guardar esta jugada</button>
                </form>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- PÁGINA 2: HISTORIAL Y RESULTADOS ---
RESULTADOS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historial - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container">
        <div class="card p-4 shadow">
            <h4 class="mb-4">📋 Historial de Series Guardadas</h4>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Fecha</th>
                            <th>Serie Equilibrio</th>
                            <th>Serie Cazadora</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for f in favs %}
                        <tr>
                            <td>{{ f.fecha.strftime('%d/%m/%Y %H:%M') }}</td>
                            <td>{{ f.serie_eq.replace(',', ' - ') }}</td>
                            <td>{{ f.serie_cz.replace(',', ' - ') }}</td>
                            <td>
                                <form action="/limpiar" method="POST" style="display:inline;">
                                    <button class="btn btn-sm btn-outline-danger">Eliminar</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- PÁGINA 3: ESTADÍSTICAS ---
STATS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estadísticas - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container text-center">
        <div class="row">
            <div class="col-md-6 offset-md-3">
                <div class="card p-5 shadow">
                    <h1 class="display-4 text-primary">{{ total }}</h1>
                    <p class="lead">Series Guardadas en PostgreSQL</p>
                    <hr>
                    <p class="text-muted">Tu base de datos está conectada y funcionando.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- RUTAS DE LA APP ---

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

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(GEN_HTML)

@app.route('/generar', methods=['POST'])
def generar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    eq = sorted(random.sample(range(1, 57), 6))
    cz = sorted(random.sample(range(1, 57), 6))
    return render_template_string(GEN_HTML, eq=eq, cz=cz)

@app.route('/guardar', methods=['POST'])
def guardar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', 
                (request.form.get('num_eq'), request.form.get('num_cz')))
    conn.commit()
    cur.close() ; conn.close()
    return redirect(url_for('resultados'))

@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC')
    favs = cur.fetchall()
    cur.close() ; conn.close()
    return render_template_string(RESULTADOS_HTML, favs=favs)

@app.route('/estadisticas')
def estadisticas():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM favoritos')
    total = cur.fetchone()[0]
    cur.close() ; conn.close()
    return render_template_string(STATS_HTML, total=total)

@app.route('/limpiar', methods=['POST'])
def limpiar():
    # Aquí podrías poner lógica para borrar solo uno, pero por ahora limpia todo
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM favoritos')
    conn.commit()
    cur.close() ; conn.close()
    return redirect(url_for('resultados'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
