import os
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from src.azure_client import (
    get_work_item,
    get_predecessor_data,
    get_related_user_story_titles,
    get_total_user_stories_by_sprint
)

from src.pdf_generator import generate_pdf
from src.supabase_client import (
    subir_pdf_supabase,
    supabase_client,
    BUCKET_NAME
)

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

        # 1. Obtener la Historia de Usuario
        work_item = get_work_item(id_hu)

        # 2. Obtener el Sprint
        iteration_path = work_item["fields"]["System.IterationPath"]

        # 3. Total de Historias del Sprint
        total_hu = get_total_user_stories_by_sprint(
            iteration_path
        )

        # 4. Obtener datos del requerimiento predecesor
        datos_requerimiento = get_predecessor_data(
            work_item
        )

        # 5. Obtener historias relacionadas
        historias_relacionadas = get_related_user_story_titles(
            work_item
        )

        # 6. Generar PDF
        ruta_pdf = generate_pdf(
            work_item,
            total_hu,
            datos_requerimiento,
            historias_relacionadas
        )

        # 7. Subir PDF a Supabase
        nombre_archivo = f"HU_{id_hu}.pdf"

        url_pdf = subir_pdf_supabase(
            ruta_pdf,
            nombre_archivo
        )

        # 8. Eliminar archivo temporal
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)

        return {
            "mensaje": "PDF generado correctamente y guardado en Supabase Storage",
            "archivo": nombre_archivo,
            "url_archivo": url_pdf,
            "total_historias_sprint": total_hu,
            "historias_relacionadas": historias_relacionadas
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el PDF: {str(e)}"
        )


@app.get("/historial")
def obtener_historial():

    try:

        archivos = supabase_client.storage.from_(BUCKET_NAME).list()

        historial = []

        for i, archivo in enumerate(archivos):

            nombre = archivo.get("name")

            if nombre and nombre.endswith(".pdf"):

                url_publica = (
                    supabase_client.storage
                    .from_(BUCKET_NAME)
                    .get_public_url(nombre)
                )

                try:
                    id_hu = int(
                        nombre.replace("HU_", "").replace(".pdf", "")
                    )
                except ValueError:
                    id_hu = 0

                historial.append({
                    "id": i + 1,
                    "idHu": id_hu,
                    "nombre": nombre,
                    "fecha": archivo.get(
                        "created_at",
                        "Fecha desconocida"
                    )[:10],
                    "url_archivo": url_publica
                })

        return historial[::-1]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el historial de Supabase: {str(e)}"
        )