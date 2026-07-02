import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Alcance (Scope) para interactuar de forma completa con Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]

# El ID de tu carpeta personal compartida con la Service Account
FOLDER_ID = "1NrOes6hnpqvcZ6EY3u-fWGgl_nOyAo-U"

def subir_pdf_drive(ruta_pdf, nombre_archivo):
    # 1. Obtener las credenciales desde las variables de entorno
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    
    if not credentials_json:
        raise ValueError("La variable de entorno GOOGLE_CREDENTIALS no está configurada.")
    
    # 2. Cargar las credenciales de la Service Account
    info = json.loads(credentials_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    
    # 3. Construir el servicio de Google Drive
    drive_service = build('drive', 'v3', credentials=creds)
    
    # 4. Configurar los metadatos apuntando a tu FOLDER_ID
    file_metadata = {
        'name': nombre_archivo,
        'parents': [FOLDER_ID]  # <-- Esto fuerza el archivo a tu carpeta y usa tu espacio personal
    }
    
    # 5. Preparar el archivo binario (PDF)
    media = MediaFileUpload(ruta_pdf, mimetype='application/pdf')
    
    # 6. Crear el archivo en Drive (añadiendo supportsAllDrives por seguridad)
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True  
    ).execute()
    
    # 7. Retornar el ID del archivo subido (Fin de la función)
    return file.get('id')