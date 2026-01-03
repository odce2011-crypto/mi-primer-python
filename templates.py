from flask import session

def get_navbar():
    admin_link = ""
    if session.get('es_admin'):
        admin_link = '<li class="nav-item"><a class="nav-link text-warning" href="/usuarios">⚙️ Usuarios</a></li>'
    
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <a class="navbar-brand" href="/">🎰 Melate Pro</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Generador</a></li>
                    <li class="nav-item"><a class="nav-link" href="/resultados">Historial</a></li>
                    <li class="nav-item"><a class="nav-link" href="/analitica">Analítica</a></li>
                    {admin_link}
                </ul>
                <span class="navbar-text me-3 small text-info">👤 {session.get('user', '')}</span>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
            </div>
        </div>
    </nav>
    """

LAYOUT_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Melate Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>.ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; background: #ffcc00; border-radius: 50%; text-align: center; font-weight: bold; margin: 2px; border: 1px solid #d4ac0d; font-size: 0.75rem; }</style>
</head>
<body class="bg-light">
    {{ navbar | safe }}
    <div class="container">{{ content | safe }}</div>
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
