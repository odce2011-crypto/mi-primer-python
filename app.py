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

# --- DISEÑO HTML ---
APP_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Analizador - Privado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body { background: #f0f4f8; padding-bottom: 50px; }
        .card { border-radius: 15px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .ball { display: inline-block; width: 32px; height: 32px; line-height: 32px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; font-size: 0.8rem; border: 1px solid #d4ac0d; }
        .match { background: #2ecc71 !important; color: white !important; border-color: #27ae60 !important; transform: scale(1.1); transition: 0.3s; }
        .badge-aciertos { font-size: 0.7rem; padding: 4px 8px; border-radius: 10px; background: #34495e; color: white; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <span class="navbar-brand">🎰 Melate Inteligente</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Salir</a>
        </div>
    </nav>

    <div class="container" style="max-width: 700px;">
        <div class="card p-4 mb-4 border-primary border-top border-4">
            <h5>🔍 Comprobar Resultados Oficiales</h5>
            <p class="text-muted small">Ingresa los 6 números del sorteo oficial para buscar aciertos en tu historial.</p>
            <form method="POST" class="row g-2">
                {% for i in range(6) %}
                <div class="col-2">
                    <input type="number" name="ganador_{{i}}" class="form-control text-center" min="1" max="56" required>
                </div>
                {% endfor %}
                <div class="col-12 mt-3">
                    <button type="submit" name="accion" value="comprobar" class="btn btn-primary w-100">Analizar mi Historial</button>
                </div>
            </form>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card p-4 mb-4 text-center">
                    <form method="POST">
                        <button type="submit" name="accion" value="generar" class="btn btn-success w-100">Generar Nuevas Series</button>
                    </form>
                    {% if eq %}
                    <div class="bg-light p-3 rounded mt-3 border text-start">
                        <div class="mb-2"><strong>Eq:</strong> {% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                        <div><strong>Cz:</strong> {% for n in cz %}<div class="ball" style="background:#a29bfe;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                        <form method="POST" class="mt-3">
                            <input type="hidden" name="num_eq" value="{{ eq|join(',') }}">
                            <input type="hidden" name="num_cz" value="{{ cz|join(',') }}">
                            <button type="submit" name="accion" value="guardar" class="btn btn-outline-dark btn-sm w-100">⭐ Guardar para Seguimiento</button>
                        </form>
                    </div>
                    {% endif %}
                </div>

                <div class="card p-4 shadow">
                    <h5 class="mb-3"><i class="bi bi-list-check"></i> Historial de Seguimiento</h5>
                    {% for f in favs %}
                    <div class="p-3 mb-3 border rounded bg-white">
                        <div class="d-flex justify-content-between">
                            <small class="text-muted">{{ f.fecha.strftime('%d/%m/%Y %H:%M') }}</small>
                            {% if f.aciertos > 0 %}
                            <span class="badge-aciertos">✨ {{ f.aciertos }} Aciertos</span>
                            {% endif %}
                        </div>
                        <div class="mt-2">
                            {% for n in f.serie_eq.split(',') %}
                                <div class="ball {% if n|int in oficiales %}match{% endif %}">{{n}}</div>
                            {% endfor %}
                            <span class="mx-2">|</span>
                            {% for n in f.serie_cz.split(',') %}
                                <div class="ball {% if n|int in oficiales %}match{% endif %}" style="background:#a29bfe;">{{n}}</div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# [Aquí va el mismo LOGIN_HTML que ya te funcionó perfectamente]

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (Usa el mismo código de login que ya tienes)
    error = None
    if request.method == 'POST':
        if request.form['user'] == ADMIN_USER and request.form['pass'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        error = 'Acceso denegado'
    # Asegúrate de que la variable LOGIN_HTML esté definida arriba
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    eq, cz = None, None
    oficiales = session.get('oficiales', []) # Recuperamos de la sesión si ya comprobamos
    
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
        elif accion == 'comprobar':
            oficiales = [int(request.form.get(f'ganador_{i}')) for i in range(6)]
            session['oficiales'] = oficiales # Guardar para resaltar

    cur.execute('SELECT * FROM favoritos ORDER BY fecha DESC LIMIT 15')
    favs = cur.fetchall()
    
    # Lógica de cálculo de aciertos en tiempo real
    for f in favs:
        nums_f = [int(x) for x in (f['serie_eq'] + "," + f['serie_cz']).split(',')]
        f['aciertos'] = len(set(nums_f) & set(oficiales))

    cur.close()
    conn.close()
    return render_template_string(APP_HTML, eq=eq, cz=cz, favs=favs, oficiales=oficiales)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
