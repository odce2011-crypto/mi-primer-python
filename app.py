from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pandas as pd
import io

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
                    <li class="nav-item"><a class="nav-link" href="/estadisticas">Estadísticas</a></li>
                </ul>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
            </div>
        </div>
    </nav>
    """

# --- (Las plantillas GEN_HTML, LOGIN_HTML y STATS_HTML se mantienen igual) ---
# Solo actualizaremos RESULTADOS_HTML para incluir el botón de descarga

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
                <i class="bi bi-file-earmark-excel"></i> Descargar Excel (.xlsx)
            </a>
        </div>

        <div class="card p-4 shadow mb-4">
            <form method="GET" action="/resultados" class="row g-3">
                <div class="col-8"><input type="date" name="fecha_busqueda" class="form-control" value="{{ fecha_filtro }}"></div>
                <div class="col-4"><button type="submit" class="btn btn-dark w-100">Filtrar</button></div>
            </form>
        </div>

        <div class="card p-4 shadow text-center">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr><th>Fecha</th><th>Equilibrio</th><th>Cazadora</th></tr>
                </thead>
                <tbody>
                    {% for f in favs %}
                    <tr>
                        <td>{{ f.fecha.strftime('%d/%m/%y %H:%M') }}</td>
                        <td><span class="badge bg-warning text-dark">{{ f.serie_eq }}</span></td>
                        <td><span class="badge bg-info text-dark">{{ f.serie_cz }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# --- NUEVA RUTA PARA DESCARGAR EXCEL ---
@app.route('/descargar')
def descargar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Leemos la tabla completa usando Pandas
    df = pd.read_sql_query('SELECT fecha, serie_eq, serie_cz FROM favoritos ORDER BY fecha DESC', conn)
    conn.close()

    # Crear un buffer en memoria para el archivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Mis Jugadas')
    
    output.seek(0)
    
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, 
        download_name=f"Melate_Historial_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )

# --- (Mantén las rutas de home, generar, guardar, resultados y estadísticas del código anterior) ---

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(GEN_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (Mismo código de login) ...
    return render_template_string(LOGIN_HTML) # Asegúrate de definir LOGIN_HTML

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    fecha_filtro = request.args.get('fecha_busqueda')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if fecha_filtro:
        cur.execute("SELECT * FROM favoritos WHERE DATE(fecha) = %s ORDER BY fecha DESC", (fecha_filtro,))
    else:
        cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC')
    favs = cur.fetchall()
    cur.close(); conn.close()
    return render_template_string(RESULTADOS_HTML, favs=favs, fecha_filtro=fecha_filtro)

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
