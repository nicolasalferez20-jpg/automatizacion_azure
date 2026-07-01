from fastapi import FastAPI


from src.azure_client import (
    get_work_item,
    get_child_tasks
)

from src.pdf_generator import generate_pdf
from src.google_drive import subir_pdf_drive
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
        "mensaje": "API generadora de PDFs funcionando"
    }


@app.get("/generar-pdf/{id_hu}")
def crear_pdf(id_hu:int):

    # 1. Obtener HU desde Azure DevOps
    work_item = get_work_item(id_hu)

    # 2. Obtener tareas relacionadas
    tareas = get_child_tasks(
        work_item
    )

    # 3. Crear PDF localmente
    ruta_pdf = generate_pdf(
        work_item,
        tareas
    )
    # 4. Subir PDF a Google Drive
    id_drive = subir_pdf_drive(
        ruta_pdf,
        f"HU_{id_hu}.pdf"

    )
    return {


        "mensaje":
        "PDF generado correctamente y guardado en Drive",

        "archivo":
        f"HU_{id_hu}.pdf",

        "drive_id":
        id_drive

    }