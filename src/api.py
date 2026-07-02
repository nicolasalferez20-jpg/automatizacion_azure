import os  # Importamos os para limpiar el archivo local
from fastapi import FastAPI
from src.azure_client import get_work_item, get_child_tasks
from src.pdf_generator import generate_pdf
from src.supabase_client import subir_pdf_supabase  # <-- Cambiamos el import
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
        "url_archivo": url_pdf  # <-- Ahora devolvemos la URL directa en vez de un ID enredado
    }