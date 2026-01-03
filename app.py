from flask import Flask, request
import os

app = Flask(__name__)

# Diseño con formulario
def get_html(mensaje_saludo=""):
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mi Primera App Interactiva</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f0f2f5; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: sans-serif; }}
            .card {{ border: none; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }}
            .btn-primary {{ background-color: #4834d4; border: none; }}
            .welcome-msg {{ color: #4834d4; font-weight: bold; font-size: 1.2rem; }}
        </style>
    </head>
    <body>
        <div class="card p-4">
            <h3 class="text-center mb-4">¿Cómo te llamas?</h3>
            
            <form method="POST" class="text-center">
                <div class="mb-3">
                    <input type="text" name="nombre_usuario" class="form-control" placeholder="Escribe tu nombre aquí" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Enviar a mi VPS</button>
            </form>

            <div class="mt-4 text-center">
                <p class="welcome-msg">{mensaje_saludo}</p>
            </div>
            
            <hr>
            <p class="text-muted small text-center">Esta respuesta la procesa Python en tiempo real.</p>
        </div>
    </body>
    </html>
    """

@app.route('/', methods=['GET', 'POST'])
def home():
    saludo = ""
    if request.method == 'POST':
        # Aquí capturamos lo que el usuario escribió en el cuadro de texto
        nombre = request.form.get('nombre_usuario')
        saludo = f"¡Hola, {nombre}! 👋 Tu servidor te reconoce."
    
    return get_html(saludo)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
