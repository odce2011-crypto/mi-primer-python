from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
import os, io, random
import pandas as pd
from datetime import datetime
import pytz
from psycopg2.extras import RealDictCursor

# Importamos nuestros módulos locales
from database import get_db_connection, init_db
from templates import LAYOUT_HTML, LOGIN_HTML, get_navbar
from logic import generar_melate, procesar_analitica
from google_sheets import exportar_a_sheets # Agrega esto al inicio de app.py
from test_google import probar_conexion
probar_conexion()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'multi-2026-safe-key')

# Configuración de zona horaria
def get_local_time():
    tz = pytz.timezone('America/Chicago')
    return datetime.now(tz)

# Iniciar base de datos al arrancar
with app.app_context():
    init_db()

# --- RUTAS DE ACCESO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, pw = request.form['user'], request.form['pass']
        conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE username=%s AND password=%s", (user, pw))
        acc = cur.fetchone(); cur.close(); conn.close()
        if acc:
            session.update({'logged_in': True, 'user': acc['username'], 'es_admin': acc['es_admin']})
            return redirect(url_for('home'))
        return render_template_string(LOGIN_HTML, error="Usuario o clave incorrectos")
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- RUTAS PRINCIPALES ---

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    content = """
    <div class="card p-5 shadow text-center mx-auto" style="max-width: 500px; border-radius: 20px;">
        <h2 class="mb-4">🎰 Melate Pro</h2>
        <p class="text-muted">Genera jugadas basadas en algoritmos de Equilibrio y Cazadora.</p>
        <form method="POST" action="/generar">
            <button class="btn btn-primary btn-lg w-100 py-3 shadow">Generar Nueva Jugada</button>
        </form>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/generar', methods=['POST'])
def generar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    eq, cz = generar_melate()
    
    # Construcción de bolitas visuales
    balls_eq = "".join([f'<div class="ball">{n:02d}</div>' for n in eq])
    balls_cz = "".join([f'<div class="ball" style="background:#a29bfe; border-color:#6c5ce7;">{n:02d}</div>' for n in cz])
    
    content = f'''
    <div class="card p-4 shadow mx-auto text-center" style="max-width: 550px;">
        <h4 class="mb-4">Resultados del Algoritmo</h4>
        <div class="mb-4">
            <h6 class="text-muted small text-start">⚖️ Serie de Equilibrio:</h6>
            <div class="balls-container">{balls_eq}</div>
        </div>
        <div class="mb-4">
            <h6 class="text-muted small text-start">🏹 Serie Cazadora:</h6>
            <div class="balls-container">{balls_cz}</div>
        </div>
        <form method="POST" action="/guardar">
            <input type="hidden" name="num_eq" value="{",".join(map(str,eq))}">
            <input type="hidden" name="num_cz" value="{",".join(map(str,cz))}">
            <button class="btn btn-success w-100 py-3 shadow-sm">⭐ Guardar en Historial</button>
        </form>
        <a href="/" class="btn btn-link mt-3 text-decoration-none text-muted">Intentar de nuevo</a>
    </div>
    '''
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/guardar', methods=['POST'])
def guardar():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    fecha_chicago = get_local_time()
    eq = request.form.get('num_eq')
    cz = request.form.get('num_cz')
    user = session.get('user', 'desconocido')
    
    # 1. GUARDAR EN POSTGRES (Tu historial actual)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('INSERT INTO favoritos (serie_eq, serie_cz, fecha) VALUES (%s, %s, %s)', 
                (eq, cz, fecha_chicago))
    conn.commit(); cur.close(); conn.close()
    
    # 2. ENVIAR A GOOGLE SHEETS (Nuevo)
    # Formateamos la fila: Fecha | Usuario | Serie Eq | Serie Cz
    fila = [fecha_chicago.strftime('%Y-%m-%d %I:%M %p'), user, eq, cz]
    exportar_a_sheets(fila)
    
    return redirect(url_for('resultados'))
@app.route('/resultados')
def resultados():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 50")
    favs = cur.fetchall(); cur.close(); conn.close()
    
    rows = ""
    for f in favs:
        f_str = f['fecha'].strftime('%d/%m %I:%M %p')
        # Botón de borrar individual (ícono de basura)
        btn_borrar = f'<td><a href="/borrar/{f["id"]}" class="text-danger" onclick="return confirm(\'¿Borrar?\')"><i class="bi bi-trash"></i></a></td>'
        rows += f"<tr><td>{f_str}</td><td>{f['serie_eq']}</td><td>{f['serie_cz']}</td>{btn_borrar}</tr>"
    
    # Formulario de limpieza por día (solo para admin)
    limpieza_html = ""
    if session.get('es_admin'):
        limpieza_html = '''
        <form method="POST" action="/limpiar_errores" class="mb-3 d-flex gap-2">
            <input type="date" name="fecha_error" class="form-control form-control-sm" style="width:150px">
            <button class="btn btn-danger btn-sm">Borrar por día</button>
        </form>
        '''

    content = f"""
    <div class="card p-4 shadow">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5>📋 Historial</h5>
            <a href="/descargar" class="btn btn-sm btn-outline-success">Excel</a>
        </div>
        {limpieza_html}
        <div class="table-responsive">
            <table class="table table-hover text-center table-sm">
                <thead><tr><th>Fecha</th><th>Eq</th><th>Cz</th><th></th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    # ESTA ES LA LÍNEA 154: Asegúrate que esté alineada con el "if" inicial
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/perfil')
def perfil():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM favoritos")
    total = cur.fetchone()[0]; cur.close(); conn.close()

    hora_actual = get_local_time().strftime('%d/%m/%Y %I:%M %p')
    rango = "Administrador" if session.get('es_admin') else "Usuario"
    color = "danger" if session.get('es_admin') else "info"
    
    content = f"""
    <div class="profile-card shadow mx-auto mt-2" style="max-width: 400px; border-radius: 20px; background: white; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 80px;"></div>
        <div style="width: 80px; height: 80px; background: white; border-radius: 50%; margin: -40px auto 10px; display: flex; align-items: center; justify-content: center; font-size: 2rem; border: 4px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <i class="bi bi-person-circle text-primary"></i>
        </div>
        <div class="p-4 text-center">
            <h4 class="mb-1">{session.get('user', '').capitalize()}</h4>
            <span class="badge bg-{color} mb-3">{rango}</span>
            <p class="text-muted small">🕒 Zona Horaria: Chicago<br><strong>{hora_actual}</strong></p>
            <hr>
            <h5 class="fw-bold mb-0">{total}</h5>
            <p class="text-muted small">Series Totales Registradas</p>
        </div>
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
        content = "<div class='alert alert-light text-center shadow-sm'>No hay datos suficientes para el análisis.</div>"
    else:
        top_10 = procesar_analitica(df)
        items = "".join([f"<li class='list-group-item d-flex justify-content-between align-items-center'>Número {n} <span class='badge bg-primary rounded-pill'>{c} veces</span></li>" for n, c in top_10])
        content = f"<div class='card p-4 shadow mx-auto' style='max-width: 450px;'><h5>🔥 Números más Frecuentes</h5><ul class='list-group mt-3'>{items}</ul></div>"
    
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

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
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"Melate_Export_{get_local_time().strftime('%Y%m%d')}.xlsx")

@app.route('/usuarios')
def usuarios():
    if not session.get('es_admin'): return redirect(url_for('home'))
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios ORDER BY es_admin DESC")
    users = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{u['username']}</td><td>{'<span class="badge bg-danger">Admin</span>' if u['es_admin'] else 'Usuario'}</td></tr>" for u in users])
    content = f"""
    <div class="card p-4 shadow">
        <h5>👥 Gestión de Accesos</h5>
        <div class="table-responsive mt-3">
            <table class="table align-middle"><thead><tr><th>Usuario</th><th>Rango</th></tr></thead><tbody>{rows}</tbody></table>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_HTML, navbar=get_navbar(), content=content)

@app.route('/borrar/<int:id>')
def borrar_registro(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM favoritos WHERE id = %s", (id,))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('resultados'))

# RUTA ESPECIAL: Borrar todos los registros de un día específico (para limpiar lo que salió mal)
@app.route('/limpiar_errores', methods=['POST'])
def limpiar_errores():
    if not session.get('es_admin'): return redirect(url_for('home'))
    fecha_mal = request.form.get('fecha_error') # Formato YYYY-MM-DD
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Borra los registros de esa fecha que se cargaron antes de arreglar el horario
    cur.execute("DELETE FROM favoritos WHERE DATE(fecha) = %s", (fecha_mal,))
    conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('resultados'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))







