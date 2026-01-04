import gspread
from google.oauth2.service_account import Credentials
import os
import json

def exportar_a_sheets(datos):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Leemos el contenido del JSON desde una variable de entorno
        info_json = os.environ.get('GOOGLE_JSON')
        
        if not info_json:
            print("Error: La variable GOOGLE_JSON no está configurada")
            return False

        # Cargamos las credenciales desde el texto
        info_dict = json.loads(info_json)
        creds = Credentials.from_service_account_info(info_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrir la hoja
        sheet = client.open("Melate_Registros").sheet1
        sheet.append_row(datos)
        return True
    except Exception as e:
        print(f"Error en Google Sheets: {e}")
        return False
