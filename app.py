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

# --- COMPONENTE: NAVBAR ---
def get_navbar():
    admin_link = ""
    if session.get('es_admin'):
        admin_link = '<li class="nav-item"><a class="nav-link text-warning" href="/usuarios">⚙️ Gestionar Usuarios</a></li>'
    
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
                <span class="navbar-text me-3 small">Hola, <b>{session.get('user')}</b></span>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
            </div>
        </div>
    </nav>
    """

# --- PLANTILLAS NUEVAS ---

USUARIOS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Usuarios</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    """ + get_navbar() + """
    <div class="container" style="max-width: 800px;">
        <div class="card p-4 shadow mb-4">
            <h5>➕ Agregar Nuevo Usuario</h5>
            <form method="POST" action="/usuarios/crear" class="row g-2">
                <div class="col-md-4"><input type="text" name="new_user" class="form-control" placeholder="Usuario" required></div>
                <div class="col-md-4"><input type="password" name="new_pass" class="form-control" placeholder="Contraseña" required></div>
                <div class="col-md-4"><button type="submit" class="btn btn-primary w-100">Crear Acceso</button></div>
            </form>
        </div>

        <div class="card p-4 shadow">
            <h5>👥 Usuarios en el Sistema</h5>
            <table class="table align-middle">
                <thead><tr><th>Usuario</th><th>Rango</th><th>Acción</th></tr></thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td>{{ u.username }}</td>
                        <td>{% if u.es_admin %}<span class="badge bg-danger">Admin</span>{% else %}<span class="badge bg-secondary">Usuario</span>{% endif %}</td>
                        <td>
                            {% if u.username != session['user'] %}
                            <form method="POST" action="/usuarios/borrar">
                                <input type="hidden" name="user_id" value="{{ u.id }}">
                                <button class="btn btn-sm btn-outline-danger">Eliminar</button>
                            </form>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# [Mantener LOGIN_HTML, GEN_HTML, etc. del paso anterior, solo agregando get_navbar()]

# --- RUTAS DE SEGURIDAD Y USUARIOS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pass']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (user, pw))
        account = cur.fetchone()
        cur.close(); conn.close()
        
        if account:
            session['logged_in'] = True
            session['user'] = account['username']
            session['es_admin'] = account['es_admin']
            return redirect(url_for('home'))
        return render_template_string(LOGIN_HTML, error="Usuario o clave incorrectos")
    return render_template_string(LOGIN_HTML)

@app.route('/usuarios')
def gestionar_usuarios():
    if not session.get('es_admin'): return redirect(url_for('home'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios ORDER BY es_admin DESC")
    users = cur.fetchall()
    cur.close(); conn.close()
    return render_template_string(USUARIOS_HTML, users=users)

@app.route('/usuarios/crear', methods=['POST'])
def crear_usuario():
    if not session.get('es_admin'): return redirect(url_for('home'))
    new_user = request.form['new_user']
    new_pass = request.form['new_pass']
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (new_user, new_pass))
        conn.commit()
    except: pass
    cur.close(); conn.close()
    return redirect(url_for('gestionar_usuarios'))

@app.route('/usuarios/borrar', methods=['POST'])
def borrar_usuario():
    if not session.get('es_admin'): return redirect(url_for('home'))
    user_id = request.form['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s AND es_admin = FALSE", (user_id,))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('gestionar_usuarios'))

# ... (Rutas de /home, /generar, /resultados, /analitica se mantienen igual) ...

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
