import os
import json
import gspread
from google.oauth2.service_account import Credentials

def probar_conexion():
    print("--- INICIANDO PRUEBA DE GOOGLE SHEETS ---")
    
    # 1. Verificar si la variable de entorno existe
    info_json = os.environ.get('GOOGLE_JSON')
    if not info_json:
        print("❌ ERROR: La variable GOOGLE_JSON no existe en EasyPanel.")
        return

    try:
        # 2. Intentar parsear el JSON
        info_dict = json.loads(info_json)
        print("✅ JSON cargado correctamente desde variable de entorno.")
        
        # 3. Intentar autenticar
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_dict, scopes=scope)
        client = gspread.authorize(creds)
        print("✅ Autenticación con Google exitosa.")

        # 4. Listar hojas disponibles
        # Esto nos dirá a qué archivos tiene acceso el robot
        files = client.openall()
        if not files:
            print("⚠️ ADVERTENCIA: El robot se conectó, pero NO TIENE ACCESO a ninguna hoja.")
            print(f"Asegúrate de compartir tu hoja con: {info_dict.get('client_email')}")
        else:
            print("✅ Hojas encontradas con acceso:")
            for f in files:
                print(f"   - {f.title} (ID: {f.id})")

    except json.JSONDecodeError:
        print("❌ ERROR: El contenido de GOOGLE_JSON no es un JSON válido. Revisa que no falten llaves {}")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {str(e)}")

if __name__ == "__main__":
    probar_conexion()
