from flask import Flask, render_template_string, request
import random
import os

app = Flask(__name__)

# Esta lista guardará tus favoritos mientras la app esté corriendo
favoritos = []

def generar_melate():
    equilibrio = sorted(random.sample(range(1, 57), 6))
    cazadora = sorted(random.sample(range(1, 57), 6))
    return equilibrio, cazadora

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Pro - Mi VPS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; font-family: sans-serif; padding-bottom: 50px; }
        .card { border-radius: 20px; border: none; box-shadow: 0 10px 20px rgba(0,0,0,0.08); }
        .ball { 
            display: inline-block; width: 38px; height: 38px; line-height: 38px; 
            background: #ffcc00; color: #333; border-radius: 50%; 
            text-align: center; font-weight: bold; margin: 3px; border: 2px solid #e6b800; font-size: 0.9rem;
        }
        .btn-primary { background: #6c5ce7; border: none; border-radius: 10px; }
        .btn-success { border-radius: 10px; }
        .fav-item { background: white; border-radius: 12px; padding: 10px; margin-bottom: 10px; border-left: 5px solid #6c5ce7; }
    </style>
</head>
<body>
    <div class="container mt-5" style="max-width: 600px;">
        <div class="card p-4 mb-4 text-center">
            <h2 class="mb-4">🎰 Generador Melate</h2>
            <form method="POST">
                <button type="submit" name="accion" value="generar" class="btn btn-primary btn-lg w-100">Generar Nuevas Series</button>
            </form>

            {% if eq %}
            <div class="mt-4 p-3 bg-light rounded">
                <h6>Estadística:</h6>
                <div>{% for n in eq %}<div class="ball">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                <h6 class="mt-3">Cazadora:</h6>
                <div>{% for n in cz %}<div class="ball" style="background:#a29bfe; border-color:#6c5ce7;">{{ "%02d"|format(n) }}</div>{% endfor %}</div>
                
                <form method="POST" class="mt-3">
                    <input type="hidden" name="num_eq" value="{{ eq }}">
                    <input type="hidden" name="num_cz" value="{{ cz }}">
                    <button type="submit" name="accion" value="guardar" class="btn btn-success btn-sm">⭐ Guardar estas series</button>
                </form>
            </div>
            {% endif %}
        </div>

        <div class="card p-4">
            <h4 class="mb-3">⭐ Mis Favoritos</h4>
            {% if not favoritos %}
                <p class="text-muted">Aún no has guardado ninguna serie.</p>
            {% else %}
                {% for f in favoritos %}
                <div class="fav-item shadow-sm">
                    <small class="text-muted d-block mb-1">Guardado recientemente:</small>
                    <div>
                        {% for n in f['eq'] %}<span class="badge bg-warning text-dark me-1">{{ "%02d"|format(n) }}</span>{% endfor %}
                        <span class="mx-2">|</span>
                        {% for n in f['cz'] %}<span class="badge bg-info text-dark me-1">{{ "%02d"|format(n) }}</span>{% endfor %}
                    </div>
                </div>
                {% endfor %}
                <form method="POST" class="mt-3">
                    <button type="submit" name="accion" value="limpiar" class="btn btn-outline-danger btn-sm">Limpiar Lista</button>
                </form>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    eq, cz = None, None
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'generar':
            eq, cz = generar_melate()
        
        elif accion == 'guardar':
            # Convertimos el texto de vuelta a lista de números
            nuevo_eq = eval(request.form.get('num_eq'))
            nuevo_cz = eval(request.form.get('num_cz'))
            favoritos.insert(0, {'eq': nuevo_eq, 'cz': nuevo_cz}) # Insertar al inicio
            
        elif accion == 'limpiar':
            favoritos.clear()
            
    return render_template_string(HTML_TEMPLATE, eq=eq, cz=cz, favoritos=favoritos)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
