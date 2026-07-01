from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.azure_client import (
    get_work_item,
    get_child_tasks
)

from src.pdf_generator import generate_pdf
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

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


# Carpeta donde se guardan los PDFs
OUTPUT_FOLDER = Path("output")


# Endpoint prueba

@app.get("/")
def home():

    return {
        "status": "ok",
        "mensaje": "API generadora de PDFs funcionando"
    }

# Generar PDF y guardarlo en output
@app.get("/generar-pdf/{id_hu}")
def crear_pdf(id_hu:int):

    work_item = get_work_item(id_hu)

    tareas = get_child_tasks(
        work_item
    )
    ruta_pdf = generate_pdf(
        work_item,
        tareas

    )
    return {

        "mensaje": "PDF generado correctamente",

        "archivo": ruta_pdf

    }

# Historial de PDFs generados

@app.get("/historial")
def obtener_historial():

    documentos = []

    if not OUTPUT_FOLDER.exists():

        return documentos

    for archivo in OUTPUT_FOLDER.glob("*.pdf"):

        documentos.append({

            "id": archivo.stem,

            "nombre": archivo.name,

            "fecha": archivo.stat().st_mtime

        })

    return documentos
# Abrir PDF desde historial
@app.get("/pdf/{nombre}")
def ver_pdf(nombre:str):

    ruta = OUTPUT_FOLDER / nombre
    return FileResponse(
        ruta,
        media_type="application/pdf"
    )