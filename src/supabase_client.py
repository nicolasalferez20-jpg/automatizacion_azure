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

    Si el archivo ya existe, lo reemplaza automáticamente.
    """
    

    with open(ruta_pdf, "rb") as f:
        file_data = f.read()

    bucket = supabase_client.storage.from_(BUCKET_NAME)

    try:

        # Intentar subir normalmente
        bucket.upload(
            path=nombre_archivo,
            file=file_data,
            file_options={
                "content-type": "application/pdf"
            }
        )

        print(f"PDF subido correctamente: {nombre_archivo}")

    except Exception as e:

        print("El archivo ya existe. Intentando actualizar...")

        mensaje = str(e).lower()

        if (
            "already exists" in mensaje
            or "duplicate" in mensaje
            or "409" in mensaje
        ):

            # Si existe, actualizarlo
            bucket.update(
                path=nombre_archivo,
                file=file_data,
                file_options={
                    "content-type": "application/pdf"
                }
            )

            print(f"PDF actualizado correctamente: {nombre_archivo}")

        else:
            # Otro error distinto
            raise

    return bucket.get_public_url(nombre_archivo)


def eliminar_pdf_supabase(nombre_archivo: str):

    try:

        supabase_client.storage.from_(BUCKET_NAME).remove(
            [nombre_archivo]
        )

        return True

    except Exception as e:

        print(e)

        return False