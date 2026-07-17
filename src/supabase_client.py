import os
from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "pdfs"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY"
    )

supabase_client: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

def subir_pdf_supabase(ruta_pdf: str, nombre_archivo: str) -> str:
    """
    Sube un PDF a Supabase Storage.

    Si el archivo ya existe, intenta reemplazarlo utilizando upsert.
    Retorna la URL pública del archivo.
    """

    try:

        with open(ruta_pdf, "rb") as f:
            file_data = f.read()

        respuesta = supabase_client.storage.from_(BUCKET_NAME).upload(
            path=nombre_archivo,
            file=file_data,
            file_options={
                "content-type": "application/pdf",
                "upsert": True
            }
        )

        print("Respuesta Supabase:")
        print(respuesta)

        return (
            supabase_client.storage
            .from_(BUCKET_NAME)
            .get_public_url(nombre_archivo)
        )

    except Exception as e:

        print("===================================")
        print("ERROR SUBIENDO PDF A SUPABASE")
        print(type(e))
        print(e)
        print("===================================")

        raise


def eliminar_pdf_supabase(nombre_archivo: str):

    try:

        supabase_client.storage.from_(BUCKET_NAME).remove(
            [nombre_archivo]
        )

        return True

    except Exception as e:

        print(e)

        return False