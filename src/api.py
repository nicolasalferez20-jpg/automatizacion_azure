import os  # Importamos os para limpiar el archivo local
from fastapi import FastAPI, HTTPException
from src.azure_client import get_work_item, get_child_tasks
from src.pdf_generator import generate_pdf
from src.supabase_client import subir_pdf_supabase, supabase_client, BUCKET_NAME  # <-- Asegúrate de que BUCKET_NAME y supabase_client se exporten desde allí
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://frontend-azure-inky.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "status": "ok",
        "mensaje": "API generadora de PDFs funcionando con Supabase"
    }

@app.get("/generar-pdf/{id_hu}")
def crear_pdf(id_hu: int):
    try:
        # 1. Obtener HU desde Azure DevOps
        work_item = get_work_item(id_hu)

        # 2. Obtener tareas relacionadas
        tareas = get_child_tasks(work_item)

        # 3. Crear PDF localmente
        ruta_pdf = generate_pdf(work_item, tareas)
        
        # 4. Subir PDF a Supabase Storage y obtener la URL pública
        nombre_archivo = f"HU_{id_hu}.pdf"
        url_pdf = subir_pdf_supabase(ruta_pdf, nombre_archivo)
        
        # 5. Limpieza opcional: Borrar el PDF temporal del servidor de Render
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)
            
        return {
            "mensaje": "PDF generado correctamente y guardado en Supabase Storage",
            "archivo": nombre_archivo,
            "url_archivo": url_pdf
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {str(e)}")

# 🚀 NUEVO: Endpoint para solucionar el error 404 de /historial
@app.get("/historial")
def obtener_historial():
    try:
        # 1. Listar los archivos dentro del bucket de Supabase
        archivos = supabase_client.storage.from_(BUCKET_NAME).list()
        
        historial = []
        for i, archivo in enumerate(archivos):
            nombre = archivo.get("name")
            
            # Filtramos para ignorar archivos ocultos del sistema como '.emptyFolderPlaceholder'
            if nombre and nombre.endswith(".pdf"):
                # 2. Obtener la URL pública para cada PDF encontrado
                url_publica = supabase_client.storage.from_(BUCKET_NAME).get_public_url(nombre)
                
                # Extraer el ID de la HU desde el nombre del archivo (ej: "HU_30270.pdf" -> 30270)
                try:
                    id_hu = int(nombre.replace("HU_", "").replace(".pdf", ""))
                except ValueError:
                    id_hu = 0

                historial.append({
                    "id": i + 1,
                    "idHu": id_hu,
                    "nombre": nombre,
                    "fecha": archivo.get("created_at", "Fecha desconocida")[:10],  # Recorta a formato AAAA-MM-DD
                    "url_archivo": url_publica
                })
                
        # Invertimos la lista para que los últimos PDFs generados aparezcan primero
        return historial[::-1]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el historial de Supabase: {str(e)}")