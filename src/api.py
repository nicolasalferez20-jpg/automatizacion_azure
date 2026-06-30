from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.azure_client import (
    get_work_item,
    get_child_tasks
)

from src.pdf_generator import generate_pdf
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
# Endpoint de prueba
@app.get("/")
def home():

    return {
        "status": "ok",
        "mensaje": "API generadora de PDFs funcionando"
    }

@app.get("/generar-pdf/{id_hu}")
def crear_pdf(id_hu:int):

    work_item = get_work_item(id_hu)
    tareas = get_child_tasks(work_item)


    ruta_pdf = generate_pdf(
        work_item,
        tareas
    )


    return FileResponse(
        ruta_pdf,
        media_type="application/pdf",
        filename=f"HU_{id_hu}.pdf"
    )