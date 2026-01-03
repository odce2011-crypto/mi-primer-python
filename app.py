from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return "¡Hola oscarito! soy una pagina web."

if __name__ == "__main__":
    # Esto le pregunta al sistema: ¿Qué puerto tienes libre? Si no hay uno, usa el 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

