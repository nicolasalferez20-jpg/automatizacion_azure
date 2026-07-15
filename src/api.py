import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


from src.azure_client import (
    get_work_item,
    get_work_item_relations_data,
    get_total_user_stories_by_sprint,
    get_user_stories_by_sprint,
    get_sprints
)
from src.pdf_generator import generate_pdf
from src.supabase_client import (
    eliminar_pdf_supabase,
    subir_pdf_supabase,
    supabase_client,
    BUCKET_NAME
)

app = FastAPI(
    title="Azure DevOps Automation API",
    description="API para procesar historias de usuario, resolver relaciones y exportar a PDF vía Supabase",
    version="1.1.0"
)

# Configuración de CORS para el entorno local y el despliegue en Vercel
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
    """Ruta base para verificar el estado de la API."""
    return {
        "status": "ok",
        "mensaje": "API generadora de PDFs funcionando con Supabase"
    }


@app.get("/generar-pdf/{id_hu}")
def crear_pdf(id_hu: int):
    """
    Endpoint principal:
    1. Consulta la HU en Azure DevOps.
    2. Identifica su Sprint y calcula el total de HUs del mismo.
    3. Extrae las relaciones (Predecesor y Relacionados) usando get_work_item_relations_data.
    4. Generar el PDF temporalmente y lo sube a Supabase Storage.
    """
    try:
        # 1. Obtener la Historia de Usuario (incluye el árbol de 'relations')
        work_item = get_work_item(id_hu)

        # 2. Obtener el Sprint (IterationPath) al que pertenece la HU
        iteration_path = work_item["fields"]["System.IterationPath"]

        # 3. Obtener el total de historias de usuario asociadas a ese Sprint
        total_historias_sprint = get_total_user_stories_by_sprint(iteration_path)

        # 4. Obtener el diccionario unificado de relaciones (Predecesor + Relacionado)
        datos_requerimiento = get_work_item_relations_data(work_item)

        # 5. Generar el PDF pasándole la metadata de las relaciones
        ruta_pdf = generate_pdf(
            work_item,
            total_historias_sprint,
            datos_requerimiento  # Enviamos el objeto con la estructura unificada de relaciones
        )

        # 6. Definir el nombre del archivo y subirlo a Supabase Storage
        nombre_archivo = f"HU_{id_hu}.pdf"
        
        url_pdf = subir_pdf_supabase(
            ruta_pdf,
            nombre_archivo
        )

        # 7. Limpieza: Eliminar el archivo PDF local temporal para liberar espacio en el entorno
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)

        return {
            "mensaje": "PDF generado correctamente y guardado en Supabase Storage",
            "archivo": nombre_archivo,
            "url_archivo": url_pdf,
            "total_historias_sprint": total_historias_sprint
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/sprints")
def obtener_sprints():
    return get_sprints()

@app.get("/generar-pdfs-sprint")
def generar_pdfs_sprint(iteration_path: str):
    """
    Genera un PDF para todas las Historias de Usuario de un Sprint.
    """

    try:

        # Obtener todas las HU del Sprint
        historias = get_user_stories_by_sprint(iteration_path)

        if not historias:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron Historias de Usuario para el Sprint indicado."
            )

        total_historias_sprint = len(historias)

        pdfs_generados = []
        errores = []

        # Recorrer todas las HU
        for id_hu in historias:

            try:

                # Obtener la HU
                work_item = get_work_item(id_hu)

                # Obtener las relaciones
                datos_requerimiento = get_work_item_relations_data(work_item)

                # Generar el PDF
                ruta_pdf = generate_pdf(
                    work_item,
                    total_historias_sprint,
                    datos_requerimiento
                )

                # Nombre del archivo
                nombre_archivo = f"HU_{id_hu}.pdf"

                # Subir a Supabase
                url_pdf = subir_pdf_supabase(
                    ruta_pdf,
                    nombre_archivo
                )

                # Eliminar el PDF temporal
                if os.path.exists(ruta_pdf):
                    os.remove(ruta_pdf)

                pdfs_generados.append({
                    "id_hu": id_hu,
                    "archivo": nombre_archivo,
                    "url_archivo": url_pdf
                })

            except Exception as e:

                errores.append({
                    "id_hu": id_hu,
                    "error": str(e)
                })

        return {
            "mensaje": f"Se generaron {len(pdfs_generados)} PDFs.",
            "sprint": iteration_path,
            "total_historias": total_historias_sprint,
            "pdfs_generados": pdfs_generados,
            "errores": errores
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/historial")
def obtener_historial():
    """Devuelve la lista de PDFs generados ordenados desde el más reciente."""
    try:
        # Listar todos los archivos dentro del bucket configurado
        archivos = supabase_client.storage.from_(BUCKET_NAME).list()
        
        historial = []

        for i, archivo in enumerate(archivos):
            
            nombre = archivo.get("name")

            # Procesar únicamente archivos con extensión .pdf
            if nombre and nombre.endswith(".pdf"):
                
                url_publica = (
                    supabase_client.storage
                    .from_(BUCKET_NAME)
                    .get_public_url(nombre)
                )

                # Intentar extraer el ID numérico de la HU basándose en el nombre del archivo
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
                    "fecha": archivo.get("created_at", "Fecha desconocida")[:10],  # Formato YYYY-MM-DD
                    "url_archivo": url_publica
                })

        # Retornamos la lista invertida [::-1] para mostrar primero los últimos creados
        return historial[::-1]

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el historial de Supabase: {str(e)}"
        )

from fastapi import HTTPException

@app.delete("/historial/{nombre_archivo}")
def eliminar_pdf(nombre_archivo: str):

    eliminado = eliminar_pdf_supabase(nombre_archivo)

    if not eliminado:
        raise HTTPException(
            status_code=404,
            detail="No fue posible eliminar el PDF"
        )

    return {
        "mensaje": "PDF eliminado correctamente"
    }