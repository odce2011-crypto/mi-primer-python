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

# --- FUNCIÓN PARA GENERAR LA NAVBAR DINÁMICAMENTE ---
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

# --- PLANTILLAS BASE (Sin la Navbar pegada al inicio) ---

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

# --- RUTAS ---

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
        return render_template_string(LOGIN_HTML, error="Error de acceso")
    return render_template_string(LOGIN_HTML)

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    content = """
    <div class="card p-4 shadow text-center mx-auto" style="max-width: 500px;">
        <h3>🎰 Generar Jugada</h3>
        <form method="POST" action="/generar"><button class="btn btn-primary w-100 mb-3">Generar</button></form>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/generar', methods=['POST'])
def generar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    eq = sorted(random.sample(range(1, 57), 6))
    cz = sorted(random.sample(range(1, 57), 6))
    content = f"""
    <div class="card p-4 shadow mx-auto" style="max-width: 500px;">
        <div class="mb-2"><b>Eq:</b> {" ".join([f'<div class="ball">{n:02d}</div>' for n in eq])}</div>
        <div class="mb-3"><b>Cz:</b> {" ".join([f'<div class="ball" style="background:#a29bfe;">{n:02d}</div>' for n in cz])}</div>
        <form method="POST" action="/guardar">
            <input type="hidden" name="num_eq" value="{','.join(map(str, eq))}">
            <input type="hidden" name="num_cz" value="{','.join(map(str, cz))}">
            <button class="btn btn-success w-100">Guardar</button>
        </form>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/usuarios')
def usuarios():
    if not session.get('es_admin'): return redirect(url_for('home'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios ORDER BY es_admin DESC")
    users = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{u['username']}</td><td>{'Admin' if u['es_admin'] else 'User'}</td></tr>" for u in users])
    content = f"""
    <div class="card p-4 shadow">
        <h5>👥 Gestión de Usuarios</h5>
        <table class="table"><thead><tr><th>User</th><th>Rango</th></tr></thead><tbody>{rows}</tbody></table>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 20")
    favs = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{f['fecha'].strftime('%H:%M')}</td><td>{f['serie_eq']}</td></tr>" for f in favs])
    content = f"<div class='card p-4 shadow'><h5>📋 Historial</h5><table class='table'>{rows}</table></div>"
    return render_template_string(LAYOUT_HTML, navbar=render_navbar(), content=content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/guardar', methods=['POST'])
def guardar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', (request.form.get('num_eq'), request.form.get('num_cz')))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('resultados'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
