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

# --- app.py (Ruta /generar) ---
@app.route('/generar', methods=['POST'])
def generar():
    eq, cz = generar_melate()
    balls_eq = "".join([f'<div class="ball">{n:02d}</div>' for n in eq])
    balls_cz = "".join([f'<div class="ball" style="background:#a29bfe; border-color:#6c5ce7;">{n:02d}</div>' for n in cz])
    
    content = f'''
    <div class="card p-4 shadow-sm mx-auto" style="max-width: 100%; width: 550px;">
        <h4 class="mb-4 text-center">Series Generadas</h4>
        
        <div class="mb-4">
            <h6 class="text-muted small">⚖️ Equilibrio:</h6>
            <div class="balls-container">{balls_eq}</div> </div>
        
        <div class="mb-4">
            <h6 class="text-muted small">🏹 Cazadora:</h6>
            <div class="balls-container">{balls_cz}</div> </div>
        
        <form method="POST" action="/guardar">
            <input type="hidden" name="num_eq" value="{",".join(map(str,eq))}">
            <input type="hidden" name="num_cz" value="{",".join(map(str,cz))}">
            <button class="btn btn-success w-100 py-3">⭐ Guardar Jugada</button>
        </form>
    </div>
    '''
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 50")
    favs = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{f['fecha'].strftime('%d/%m %H:%M')}</td><td>{f['serie_eq']}</td><td>{f['serie_cz']}</td></tr>" for f in favs])
    content = f"""
    <div class="card p-4 shadow">
        <div class="d-flex justify-content-between mb-3">
            <h5>📋 Historial</h5>
            <a href="/descargar" class="btn btn-sm btn-success">Excel</a>
        </div>
        <table class="table table-sm text-center"><thead><tr><th>Fecha</th><th>Eq</th><th>Cz</th></tr></thead><tbody>{rows}</tbody></table>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/analitica')
def analitica():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT serie_eq, serie_cz FROM favoritos', conn)
    conn.close()
    
    if df.empty:
        content = "<div class='alert alert-info'>Sin datos para analizar.</div>"
    else:
        top_10 = procesar_analitica(df) # Llamamos a la lógica del archivo logic.py
        list_items = "".join([f"<li class='list-group-item d-flex justify-content-between'>Número {n} <b>{c} veces</b></li>" for n, c in top_10])
        content = f"<div class='card p-4 shadow mx-auto' style='max-width: 400px;'><h5>🔥 Top 10 Números</h5><ul class='list-group'>{list_items}</ul></div>"
    
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/guardar', methods=['POST'])
def guardar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', 
                (request.form.get('num_eq'), request.form.get('num_cz')))
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
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                     as_attachment=True, download_name="Melate_Export.xlsx")

@app.route('/usuarios')
def usuarios():
    if not session.get('es_admin'): return redirect(url_for('home'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios ORDER BY es_admin DESC")
    users = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{u['username']}</td><td>{'Admin' if u['es_admin'] else 'User'}</td></tr>" for u in users])
    content = f"""
    <div class="card p-4 shadow">
        <h5>👥 Usuarios</h5>
        <table class="table"><thead><tr><th>User</th><th>Rango</th></tr></thead><tbody>{rows}</tbody></table>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/perfil')
def perfil():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    # Consultamos cuántas series hay en total para darle una estadística al usuario
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM favoritos")
    total_series = cur.fetchone()[0]
    cur.close(); conn.close()

    # Usamos iconos de Bootstrap para el avatar y el rango
    rango = "Administrador" if session.get('es_admin') else "Usuario Estándar"
    badge_color = "danger" if session.get('es_admin') else "info"
    
    content = f"""
    <div class="profile-card shadow mx-auto" style="max-width: 400px;">
        <div class="profile-header"></div>
        <div class="profile-avatar">
            <i class="bi bi-person-fill text-primary"></i>
        </div>
        <div class="card-body text-center pb-4">
            <h4 class="mb-1">{session.get('user').capitalize()}</h4>
            <span class="badge bg-{badge_color} mb-3">{rango}</span>
            <hr>
            <div class="row">
                <div class="col-12">
                    <p class="text-muted small mb-1">Series Guardadas en el Sistema</p>
                    <h5 class="fw-bold">{total_series}</h5>
                </div>
            </div>
            <div class="mt-4">
                <a href="/logout" class="btn btn-outline-danger btn-sm w-100">Cerrar Sesión</a>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)



# ... El resto de tus rutas (/resultados, /analitica, /guardar) irían aquí siguiendo este estilo
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))




