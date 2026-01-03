from flask import Flask, render_template_string, request
import random
import os

app = Flask(__name__)

# Lógica para generar los números
def generar_melate():
    # Equilibrio Estadístico (Números repartidos en el rango 1-56)
    equilibrio = sorted(random.sample(range(1, 57), 6))
    
    # Cazadora (Simulación de números que "podrían salir" por azar)
    cazadora = sorted(random.sample(range(1, 57), 6))
    
    return equilibrio, cazadora

# Diseño Visual con Bootstrap
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador Melate - Mi VPS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .container { max-width: 600px; margin-top: 50px; }
        .ball { 
            display: inline-block; width: 45px; height: 45px; line-height: 45px; 
            background: #ffcc00; color: #333; border-radius: 50%; 
            text-align: center; font-weight: bold; margin: 5px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); border: 2px solid #e6b800;
        }
        .card { border-radius: 20px; border: none; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .btn-generate { background: #6c5ce7; color: white; border-radius: 12px; font-weight: bold; }
        .btn-generate:hover { background: #a29bfe; color: white; }
    </style>
</head>
<body>
    <div class="container text-center">
        <div class="card p-5">
            <h1 class="mb-4">🎰 Melate Generator</h1>
            <p class="text-muted">Genera tus series basadas en pakin.lat/melate</p>
            
            <form method="POST">
                <button type="submit" class="btn btn-generate btn-lg w-100 mb-4">¡Generar Números!</button>
            </form>

            {% if equilibrio %}
            <div class="mt-4 text-start">
                <h5>📊 Equilibrio Estadístico:</h5>
                <div class="mb-4">
                    {% for n in equilibrio %}
                    <div class="ball">{{ "%02d" | format(n) }}</div>
                    {% endfor %}
                </div>

                <h5>🎯 Serie Cazadora:</h5>
                <div>
                    {% for n in cazadora %}
                    <div class="ball" style="background: #a29bfe; border-color: #6c5ce7;">{{ "%02d" | format(n) }}</div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <hr>
            <p class="small text-muted">Corriendo en Python @ Hostinger VPS</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    equilibrio = None
    cazadora = None
    if request.method == 'POST':
        equilibrio, cazadora = generar_melate()
    
    return render_template_string(HTML_TEMPLATE, equilibrio=equilibrio, cazadora=cazadora)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
