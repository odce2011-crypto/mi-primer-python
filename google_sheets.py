import gspread
from google.oauth2.service_account import Credentials
import os
import json

def exportar_a_sheets(datos):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # 1. Obtenemos el texto del JSON desde la variable de entorno
        info_json = os.environ.get('GOOGLE_JSON')
        
        if not info_json:
            print("Error: La variable GOOGLE_JSON no está configurada en el servidor")
            return False

        # 2. Convertimos el texto a un diccionario de Python
        info_dict = json.loads(info_json)
        
        # 3. Autenticamos usando el diccionario
        creds = Credentials.from_service_account_info(info_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # 4. Abrimos la hoja (asegúrate que el nombre coincida)
        # También puedes usar el ID que sale en la URL de tu hoja:
        # sheet = client.open_by_key("TU_ID_LARGO_DE_LA_URL").sheet1
        sheet = client.open_by_key("1_S13i4VvV31Ecv_4dv9CkaHtQklAxarQf6HR7EpBins").sheet1
        
        sheet.append_row(datos)
        return True
    except Exception as e:
        print(f"Error en Google Sheets: {e}")
        return False
