from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pandas as pd
import io
from collections import Counter

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

def get_navbar():
    return """
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <a class="navbar-brand" href="/">🎰 Melate Pro</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Generador</a></li>
                    <li class="nav-item"><a class="nav-link" href="/resultados">Historial</a></li>
                    <li class="nav-item"><a class="nav-link" href="/analitica">Analítica</a></li>
                    <li class="nav-item"><a class="nav-link" href="/estadisticas">Status</a></li>
                </ul>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
            </div>
        </div>
    </nav>
    """

# --- PLANTILLAS HTML ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center" style="height: 100vh;">
    <div class="card shadow p-4 mx-auto" style="max-width: 350px; width: 100%;">
        <h3 class="text-center mb-4">🔐 Melate Login</h3>
        {% if error %}<div class="alert alert-danger p-2 small text-center">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="mb-3"><label class="form-label">Usuario</label><input type="text" name="user" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Contraseña</label><input type="password" name="pass" class="form-control" required></div>
            <button type="submit" class="btn btn-primary w-100">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

GEN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>.ball { display: inline-block; width: 32px; height: 32px; line-height: 32px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; border: 1px solid #d4ac0d; font-size: 0.8rem; }</style>
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container" style="max-width: 600px;">
        <div class="card p-4 shadow mb-4 text-center">
            <h3>🎰 Generar Jugada</h3>
            <p class="text-muted small">Basado en Equilibrio y Cazadora</p>
            <form method="POST" action="/generar">
                <button type="submit" class="btn btn-primary btn-lg w-100 mb-3">Generar Números</button>
            </form>
            {% if eq %}
            <div class="bg-white p-3 rounded border text-start shadow-sm">
                <div class="mb-2"><strong>Equilibrio:</strong> {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <div class="mb-3"><strong>Cazadora:</strong> {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <form method="POST" action="/guardar">
                    <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                    <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                    <button type="submit" class="btn btn-success w-100">⭐ Guardar en mi Historial</button>
                </form>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

RESULTADOS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historial - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4>📋 Historial de Series</h4>
            <a href="/descargar" class="btn btn-success btn-sm">
                <i class="bi bi-file-earmark-excel"></i> Descargar Excel
            </a>
        </div>
        <div class="card p-4 shadow mb-4 text-center">
            <table class="table table-hover">
                <thead class="table-light"><tr><th>Fecha</th><th>Equilibrio</th><th>Cazadora</th></tr></thead>
                <tbody>
                    {% for f in favs %}
                    <tr>
                        <td>{{ f.fecha.strftime('%d/%m/%y %H:%M') }}</td>
                        <td><span class="badge bg-warning text-dark">{{ f.serie_eq.replace(',', ' - ') }}</span></td>
                        <td><span class="badge bg-info text-dark">{{ f.serie_cz.replace(',', ' - ') }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

ANALITICA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analítica - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container">
        <h4 class="mb-4 text-center">🔥 Análisis de Números Frecuentes</h4>
        <div class="row">
            <div class="col-md-6">
                <div class="card p-4 shadow mb-4">
                    <h5 class="text-danger">Más Frecuentes (Calientes)</h5>
                    <ul class="list-group list-group-flush">
                        {% for num, count in hot %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            Número <strong>{{ "%02d"|format(num|int) }}</strong>
                            <span class="badge bg-danger rounded-pill">{{ count }} veces</span>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card p-4 shadow mb-4 text-center">
                    <h5>Resumen General</h5>
                    <p>Has analizado <strong>{{ total_series }}</strong> series guardadas.</p>
                    <hr>
                    <p class="small text-muted">Este análisis combina tanto las series de 'Equilibrio' como las 'Cazadoras' para detectar tus tendencias de generación.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

STATS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Status - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container text-center">
        <div class="card p-5 shadow mx-auto" style="max-width: 500px;">
            <h1 class="display-1 text-primary">{{ total }}</h1>
            <p class="lead">Series totales en PostgreSQL</p>
        </div>
    </div>
</body>
</html>
"""

# --- RUTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        error = 'Acceso denegado'
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
    cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', (request.form.get('num_eq'), request.form.get('num_cz')))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('resultados'))

@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC')
    favs = cur.fetchall()
    cur.close(); conn.close()
    return render_template_string(RESULTADOS_HTML, favs=favs)

@app.route('/analitica')
def analitica():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    # Traemos todas las series
    df = pd.read_sql_query('SELECT serie_eq, serie_cz FROM favoritos', conn)
    conn.close()
    
    total_series = len(df)
    todos_los_numeros = []
    
    # Procesamos las columnas para extraer cada número individual
    for _, row in df.iterrows():
        todos_los_numeros.extend(row['serie_eq'].split(','))
        todos_los_numeros.extend(row['serie_cz'].split(','))
    
    # Contamos frecuencias
    conteo = Counter(todos_los_numeros)
    hot_numbers = conteo.most_common(10) # Los 10 más repetidos
    
    return render_template_string(ANALITICA_HTML, hot=hot_numbers, total_series=total_series)

@app.route('/descargar')
def descargar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT fecha, serie_eq, serie_cz FROM favoritos ORDER BY fecha DESC', conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Mis Jugadas')
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name="Historial_Melate.xlsx")

@app.route('/estadisticas')
def estadisticas():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM favoritos')
    total = cur.fetchone()[0]
    cur.close(); conn.close()
    return render_template_string(STATS_HTML, total=total)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
