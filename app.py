from flask import Flask
import os

app = Flask(__name__)

# El código HTML con diseño profesional
html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mi App en Hostinger</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { border: none; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .btn-custom { background-color: #6c5ce7; color: white; border-radius: 10px; padding: 10px 20px; transition: 0.3s; text-decoration: none; }
        .btn-custom:hover { background-color: #a29bfe; color: white; transform: translateY(-3px); }
    </style>
</head>
<body>
    <div class="container text-center">
        <div class="card p-5 mx-auto" style="max-width: 500px;">
            <h1 class="text-primary mb-4">🚀 ¡Logro Desbloqueado!</h1>
            <p class="lead mb-4">Tu aplicación de Python ya no es solo texto plano. Ahora tiene diseño profesional corriendo en tu <strong>VPS de Hostinger</strong>.</p>
            <hr>
            <p class="text-muted">¿Qué quieres construir ahora?</p>
            <div class="d-grid gap-2">
                <a href="#" class="btn btn-custom">Explorar mi servidor</a>
                <button class="btn btn-outline-secondary" onclick="alert('¡El servidor responde perfectamente!')">Probar Botón</button>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def hello():
    return html_template

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
