from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
import os, io, pandas as pd
from database import get_db_connection, init_db
from templates import LAYOUT_HTML, LOGIN_HTML, get_navbar
from logic import generar_melate, procesar_analitica
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'multi-2026')

# Iniciar tablas al arrancar
with app.app_context():
    init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE username=%s AND password=%s", (request.form['user'], request.form['pass']))
        acc = cur.fetchone(); cur.close(); conn.close()
        if acc:
            session.update({'logged_in': True, 'user': acc['username'], 'es_admin': acc['es_admin']})
            return redirect(url_for('home'))
    return render_template_string(LOGIN_HTML)

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    content = '<div class="card p-5 text-center shadow"><h2>🎰 Bienvenido</h2><form method="POST" action="/generar"><button class="btn btn-primary btn-lg w-100">Generar</button></form></div>'
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/generar', methods=['POST'])
def generar():
    eq, cz = generar_melate()
    balls = "".join([f'<div class="ball">{n:02d}</div>' for n in eq])
    content = f'<div class="card p-4 shadow"><h4>Series</h4>{balls}<form method="POST" action="/guardar"><input type="hidden" name="num_eq" value="{",".join(map(str,eq))}"><input type="hidden" name="num_cz" value="{",".join(map(str,cz))}"><button class="btn btn-success w-100">Guardar</button></form></div>'
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

# ... El resto de tus rutas (/resultados, /analitica, /guardar) irían aquí siguiendo este estilo
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
