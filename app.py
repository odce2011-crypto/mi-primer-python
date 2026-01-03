from flask import Flask, render_template_string, request, redirect, url_for, session
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
# Esta clave es necesaria para que las sesiones sean seguras
app.secret_key = os.environ.get('SECRET_KEY', 'una_clave_muy_secreta_123')

# Configuración de acceso (Puedes cambiarlos aquí o en EasyPanel)
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

# --- PLANTILLAS HTML ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Login - Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center" style="height: 100vh;">
    <div class="container" style="max-width: 400px;">
        <div class="card p-4 shadow">
            <h3 class="text-center mb-4">🔐 Acceso Privado</h3>
            {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
            <form method="POST">
                <div class="mb-3">
                    <label>Usuario</label>
                    <input type="text" name="user" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Contraseña</label>
                    <input type="password" name="pass" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Entrar</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

# (Aquí va el resto de tu HTML_TEMPLATE anterior, pero le añadiremos un botón de "Cerrar Sesión")
# He recortado el HTML por espacio, pero asegúrate de incluir el botón de Logout.

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Credenciales incorrectas. Intenta de nuevo.'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    # SI NO ESTÁ LOGUEADO, MANDAR AL LOGIN
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    eq, cz = None, None
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'generar':
            eq = sorted(random.sample(range(1, 57), 6))
            cz = sorted(random.sample(range(1, 57), 6))
        elif accion == 'guardar':
            cur.execute('INSERT INTO favoritos (serie_eq, serie_cz) VALUES (%s, %s)', 
                        (request.form.get('num_eq'), request.form.get('num_cz')))
            conn.commit()

    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 10')
    favs = cur.fetchall()
    cur.close()
    conn.close()
    
    # Aquí usarías tu HTML_TEMPLATE de antes (asegúrate de que tenga el botón de logout)
    return render_template_string(TU_HTML_DE_MELATE_CON_BOTON_LOGOUT, eq=eq, cz=cz, favs=favs)
