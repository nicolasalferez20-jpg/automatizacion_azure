import os
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from src.azure_client import (
    get_work_item,
    get_predecessor_data,
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
        # 1. Obtener la Historia de Usuario (ahora incluye relations internamente)
        work_item = get_work_item(id_hu)

        # 2. Obtener el Sprint al que pertenece la HU
        iteration_path = work_item["fields"]["System.IterationPath"]

        # 3. Obtener el total de HU del Sprint
        total_hu = get_total_user_stories_by_sprint(iteration_path)

        # === NUEVO PASO: Obtener datos del predecesor (Requerimiento) ===
        datos_requerimiento = get_predecessor_data(work_item)
        # ===============================================================

        # 4. Generar el PDF pasándole los datos del predecesor
        ruta_pdf = generate_pdf(
            work_item,
            total_hu,
            datos_requerimiento  # <-- Envías el diccionario con id, nombre y descripción limpia
        )

        # 5. Subir el PDF a Supabase
        nombre_archivo = f"HU_{id_hu}.pdf"

        url_pdf = subir_pdf_supabase(
            ruta_pdf,
            nombre_archivo
        )

        # 6. Eliminar el archivo temporal
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)

        return {
            "mensaje": "PDF generado correctamente y guardado en Supabase Storage",
            "archivo": nombre_archivo,
            "url_archivo": url_pdf,
            "total_historias_sprint": total_hu
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