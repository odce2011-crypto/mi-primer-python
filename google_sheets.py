import gspread
from google.oauth2.service_account import Credentials
import os
import json

def exportar_a_sheets(datos):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # BUSCA LAS CREDENCIALES: 
        # Intentará leer un archivo llamado 'google_creds.json' en tu carpeta principal
        path_creds = os.path.join(os.path.dirname(__file__), 'google_creds.json')
        
        if not os.path.exists(path_creds):
            print("Archivo google_creds.json no encontrado.")
            return False

        creds = Credentials.from_service_account_file(path_creds, scopes=scope)
        client = gspread.authorize(creds)
        
        # PON AQUÍ EL NOMBRE EXACTO DE TU HOJA (la que compartiste con el email de la API)
        # O usa el ID de la URL: client.open_by_key('ID_DE_LA_HOJA')
        sheet = client.open("Melate_Registros").sheet1
        
        # Inserta la fila al final
        sheet.append_row(datos)
        return True
    except Exception as e:
        print(f"Error detallado en Google Sheets: {e}")
        return False
