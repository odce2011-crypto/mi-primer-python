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
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-multi-2026')

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=5432
    )

# --- NAVBAR DINÁMICA ---
def render_navbar():
    admin_link = ""
    if session.get('es_admin'):
        admin_link = '<li class="nav-item"><a class="nav-link text-warning" href="/usuarios">⚙️ Usuarios</a></li>'
    
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <a class="navbar-brand" href="/">🎰 Melate Pro</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Generador</a></li>
                    <li class="nav-item"><a class="nav-link" href="/resultados">Historial</a></li>
                    <li class="nav-item"><a class="nav-link" href="/analitica">Analítica</a></li>
                    {admin_link}
                </ul>
                <span class="navbar-text me-3 small text-info">👤 {session.get('user', '')}</span>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
            </div>
        </div>
    </nav>
    """

# --- PLANTILLAS ---
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
        <form method="POST">
            <div class="mb-3"><label class="form-label">Usuario</label><input type="text" name="user" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Contraseña</label><input type="password" name="pass" class="form-control" required></div>
            <button type="submit" class="btn btn-primary w-100">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

LAYOUT_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>.ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; border: 1px solid #d4ac0d; font-size: 0.75rem; }</style>
</head>
<body class="bg-light">
    {{ navbar | safe }}
    <div class="container">
        {{ content | safe }}
    </div>
</body>
</html>
"""

# --- RUTAS DE USUARIO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, pw = request.form['user'], request.form['pass']
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (user, pw))
        acc = cur.fetchone()
        cur.close(); conn.close()
        if acc:
            session.update({'logged_in': True, 'user': acc['username'], 'es_admin': acc['es_admin']})
            return redirect(url_for('home'))
        return render_template_string(LOGIN_HTML, error="Datos incorrectos")
    return render_template_string(LOGIN_HTML)

@app.route('/usuarios')
def usuarios():
    if not session.get('es_admin'): return redirect(url_for('home'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios ORDER BY es_admin DESC, username ASC")
    users = cur.fetchall()
    cur.close(); conn.close()
    
    user_rows = ""
    for u in users:
        # No permitir que el admin se borre a sí mismo desde la UI
        btn_delete = ""
        if u['username'] != session['user']:
            btn_delete = f"""
            <form method="POST" action="/usuarios/borrar" style="display:inline;">
                <input type="hidden" name="user_id" value="{u['id']}">
                <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
            </form>
            """
        
        user_rows += f"""
        <tr>
            <td>{u['username']}</td>
            <td>{'<span class="badge bg-danger">Admin</span>' if u['es_admin'] else '<span class="badge bg-secondary">Usuario</span>'}</td>
            <td class="text-end">{btn_delete}</td>
        </tr>
        """
    
    content = f"""
    <div class="row">
        <div class="col-md-5">
            <div class="card p-4 shadow mb-4">
                <h5>➕ Nuevo Usuario</h5>
                <form method="POST" action="/usuarios/crear">
                    <div class="mb-3"><input type="text" name="new_user" class="form-control" placeholder="Nombre de usuario" required></div>
                    <div class="mb-3"><input type="password" name="new_pass" class="form-control" placeholder="Contraseña" required></div>
                    <button type="submit" class="btn btn-primary w-100">Crear Acceso</button>
                </form>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card p-4 shadow">
                <h5>👥 Lista de Usuarios</h5>
                <table class="table align-middle">
                    <thead><tr><th>Usuario</th><th>Rango</th><th class="text-end">Acción</th></tr></thead>
                    <tbody>{user_rows}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/usuarios/crear', methods=['POST'])
def crear_usuario():
    if not session.get('es_admin'): return redirect(url_for('home'))
    u, p = request.form['new_user'], request.form['new_pass']
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (username, password, es_admin) VALUES (%s, %s, FALSE)", (u, p))
        conn.commit()
    except:
        pass # Aquí podrías manejar si el usuario ya existe
    cur.close(); conn.close()
    return redirect(url_for('usuarios'))

@app.route('/usuarios/borrar', methods=['POST'])
def borrar_usuario():
    if not session.get('es_admin'): return redirect(url_for('home'))
    uid = request.form['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Seguridad: Un admin no puede borrar a otro admin (opcional) o al menos no a sí mismo
    cur.execute("DELETE FROM usuarios WHERE id = %s AND username != %s", (uid, session['user']))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('usuarios'))

# --- RUTAS DE LA APP ---

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    content = """
    <div class="card p-5 shadow text-center mx-auto" style="max-width: 500px;">
        <h2 class="mb-4">🎰 Bienvenido</h2>
        <p class="text-muted">Genera tus series basadas en algoritmos de equilibrio y cazadora.</p>
        <form method="POST" action="/generar"><button class="btn btn-primary btn-lg w-100">Generar Nueva Jugada</button></form>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/generar', methods=['POST'])
def generar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    eq = sorted(random.sample(range(1, 57), 6))
    cz = sorted(random.sample(range(1, 57), 6))
    
    eq_balls = "".join([f'<div class="ball">{n:02d}</div>' for n in eq])
    cz_balls = "".join([f'<div class="ball" style="background:#a29bfe;">{n:02d}</div>' for n in cz])
    
    content = f"""
    <div class="card p-4 shadow mx-auto text-center" style="max-width: 500px;">
        <h4 class="mb-4">Series Generadas</h4>
        <div class="mb-3 p-3 bg-light rounded text-start">
            <h6>⚖️ Equilibrio Estadístico</h6> {eq_balls}
        </div>
        <div class="mb-4 p-3 bg-light rounded text-start">
            <h6>🏹 Serie Cazadora</h6> {cz_balls}
        </div>
        <form method="POST" action="/guardar">
            <input type="hidden" name="num_eq" value="{','.join(map(str, eq))}">
            <input type="hidden" name="num_cz" value="{','.join(map(str, cz))}">
            <button class="btn btn-success btn-lg w-100">⭐ Guardar en Historial</button>
        </form>
        <a href="/" class="btn btn-link mt-2">Cancelar</a>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 50")
    favs = cur.fetchall(); cur.close(); conn.close()
    
    rows = ""
    for f in favs:
        rows += f"""
        <tr>
            <td class="small">{f['fecha'].strftime('%d/%m %H:%M')}</td>
            <td><span class="badge bg-warning text-dark">{f['serie_eq'].replace(',', ' ')}</span></td>
            <td><span class="badge bg-info text-dark">{f['serie_cz'].replace(',', ' ')}</span></td>
        </tr>"""
    
    content = f"""
    <div class="card p-4 shadow">
        <div class="d-flex justify-content-between mb-3">
            <h5>📋 Últimos Registros</h5>
            <a href="/descargar" class="btn btn-sm btn-success">Excel</a>
        </div>
        <div class="table-responsive">
            <table class="table table-sm text-center">
                <thead><tr><th>Fecha</th><th>Equilibrio</th><th>Cazadora</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/analitica')
def analitica():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT serie_eq, serie_cz FROM favoritos', conn)
    conn.close()
    
    if df.empty:
        content = "<div class='alert alert-info'>Aún no hay datos para analizar.</div>"
    else:
        nums = []
        for _, r in df.iterrows():
            nums.extend(r['serie_eq'].split(','))
            nums.extend(r['serie_cz'].split(','))
        
        top_10 = Counter(nums).most_common(10)
        list_items = "".join([f"<li class='list-group-item d-flex justify-content-between'>Número {n} <b>{c} veces</b></li>" for n, c in top_10])
        
        content = f"""
        <div class="card p-4 shadow mx-auto" style="max-width: 500px;">
            <h5 class="text-center mb-4">🔥 Números más Frecuentes</h5>
            <ul class="list-group">{list_items}</ul>
        </div>
        """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/guardar', methods=['POST'])
def guardar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', (request.form.get('num_eq'), request.form.get('num_cz')))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('resultados'))

@app.route('/descargar')
def descargar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT fecha, serie_eq, serie_cz FROM favoritos ORDER BY fecha DESC', conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name="Melate_Pro_Data.xlsx")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
