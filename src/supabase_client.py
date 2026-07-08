import os
from supabase import create_client, Client

# 1. Inicializar el cliente usando las variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "pdfs"  # El nombre que le diste a tu bucket en Supabase

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_pdf_supabase(ruta_pdf: str, nombre_archivo: str) -> str:
    """
    Sube un archivo PDF a Supabase Storage y retorna su URL pública.
    """
    # 2. Leer el archivo binario local
    with open(ruta_pdf, "rb") as f:
        file_data = f.read()
    
    # 3. Subir el archivo (content_type asegura que el navegador lo abra como PDF y no lo descargue)
    res = supabase_client.storage.from_(BUCKET_NAME).upload(
        path=nombre_archivo,
        file=file_data,
        file_options={"content-type": "application/pdf", "upsert": "true"}
    )
    
    # 4. Obtener y retornar la URL pública del archivo
    url_publica = supabase_client.storage.from_(BUCKET_NAME).get_public_url(nombre_archivo)
    return url_publica

def eliminar_pdf_supabase(nombre_archivo: str):
    try:
        supabase_client.storage.from_(BUCKET_NAME).remove([nombre_archivo])
        return True
    except Exception as e:
        print(e)
        return False