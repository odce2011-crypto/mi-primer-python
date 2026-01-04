# --- templates.py ---

from flask import session

def get_navbar():
    admin_link = ""
    if session.get('es_admin'):
        admin_link = '<li class="nav-item"><a class="nav-link text-warning" href="/usuarios">⚙️ Usuarios</a></li>'
    
    # Añadimos el botón "navbar-toggler" para móviles
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <a class="navbar-brand" href="/">🎰 Melate Pro</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Generador</a></li>
                    <li class="nav-item"><a class="nav-link" href="/resultados">Historial</a></li>
                    <li class="nav-item"><a class="nav-link" href="/analitica">Analítica</a></li>
                    {admin_link}
                </ul>
                <div class="d-flex align-items-center">
                    <span class="navbar-text me-3 small text-info">👤 {session.get('user', '')}</span>
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
                </div>
            </div>
        </div>
    </nav>
    """

LAYOUT_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        .balls-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 5px;
            margin-bottom: 15px;
        }
        .ball { 
            width: 38px; height: 38px; line-height: 38px; 
            background: #ffcc00; border-radius: 50%; 
            text-align: center; font-weight: bold; 
            border: 1px solid #d4ac0d; font-size: 0.9rem; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: inline-block;
        }
        .card { border-radius: 15px; border: none; }
        /* Ajuste para que el menú no tape el contenido al abrirse en móvil */
        .navbar-collapse { justify-content: flex-end; }

        /* Estilo para la Tarjeta de Perfil */
        .profile-card {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            border: none;
            transition: transform 0.3s;
        }
        .profile-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100px;
        }
        .profile-avatar {
            width: 80px;
            height: 80px;
            background: #f8f9fa;
            border-radius: 50%;
            margin: -40px auto 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            border: 4px solid white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
    </style>
</head>
<body class="bg-light">
    {{ navbar | safe }}
    <div class="container">
        {{ content | safe }}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

LOGIN_HTML = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<body class="bg-light d-flex align-items-center" style="height: 100vh;">
    <div class="card shadow p-4 mx-auto" style="max-width: 350px; width:100%;">
        <h3 class="text-center mb-4">🔐 Login</h3>
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="POST"><div class="mb-3"><input name="user" class="form-control" placeholder="Usuario"></div>
        <div class="mb-3"><input type="password" name="pass" class="form-control" placeholder="Clave"></div>
        <button class="btn btn-primary w-100">Entrar</button></form>
    </div>
</body>
"""
