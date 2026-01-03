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

# --- COMPONENTE: MENÚ (Para reutilizar en todas las páginas) ---
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
                    <li class="nav-item"><a class="nav-link" href="/estadisticas">Estadísticas</a></li>
                </ul>
                <div class="d-flex">
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Cerrar Sesión</a>
                </div>
            </div>
        </div>
    </nav>
    """

# --- PÁGINA 1: GENERADOR E HISTORIAL ---
APP_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container" style="max-width: 600px;">
        <div class="card p-4 shadow-sm mb-4">
            <h4 class="text-center">Generar Sorteo</h4>
            <form method="POST">
                <button type="submit" name="accion" value="generar" class="btn btn-primary w-100">Generar</button>
            </form>
            {% if eq %}
            <div class="mt-3 p-3 bg-white border rounded text-center">
                <p><strong>Series Generadas:</strong></p>
                <div class="mb-2">Eq: {{ eq|join(' - ') }}</div>
                <div class="mb-3">Cz: {{ cz|join(' - ') }}</div>
                <form method="POST">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" name="accion" value="guardar" class="btn btn-success btn-sm">Guardar en Historial</button>
                </form>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- PÁGINA 2: ESTADÍSTICAS ---
STATS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estadísticas - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container">
        <div class="card p-4 shadow-sm">
            <h3>📊 Resumen de tu Actividad</h3>
            <p class="lead">Aquí verás el conteo de tus jugadas guardadas en PostgreSQL.</p>
            <div class="alert alert-info">
                Tienes un total de <strong>{{ total }}</strong> jugadas registradas.
            </div>
            <a href="/" class="btn btn-secondary">Volver al Generador</a>
        </div>
    </div>
</body>
</html>
"""

# [Aquí debe ir tu LOGIN_HTML]

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(APP_HTML)

@app.route('/', methods=['POST'])
def handle_post():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    eq, cz = None, None
    accion = request.form.get('accion')
    
    if accion == 'generar':
        eq = sorted(random.sample(range(1, 57), 6))
        cz = sorted(random.sample(range(1, 57), 6))
        return render_template_string(APP_HTML, eq=eq, cz=cz)
    
    elif accion == 'guardar':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', 
                    (request.form.get('num_eq'), request.form.get('num_cz')))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('home'))

@app.route('/estadisticas')
def estadisticas():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM favoritos')
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    return render_template_string(STATS_HTML, total=total)

# ... (Mantén tus rutas de /login, /logout y /limpiar)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
