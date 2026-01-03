from flask import Flask
import os

app = Flask(__name__)

@app.get("/")
def home():
    return "<h1>¡Hola Mundo!</h1><p>Mi Python está corriendo en Hostinger con EasyPanel.</p>"

if __name__ == "__main__":
    # Importante usar el puerto que EasyPanel espera o definir uno
    port = int(os.environ.get("PORT", 5000))
    app.run(host="62.72.3.162", port=port)

