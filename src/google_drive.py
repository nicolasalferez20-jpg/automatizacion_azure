import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload



SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


FOLDER_ID = "1NrOes6hnpqvcZ6EY3u-fWGgl_nOyAo-U"



def subir_pdf_drive(
    ruta_pdf,
    nombre_archivo
):


    credentials_json = os.getenv(
        "GOOGLE_CREDENTIALS"
    )


    info = json.loads(
        credentials_json
    )



    credentials = service_account.Credentials.from_service_account_info(

        info,

        scopes=SCOPES

    )



    service = build(
        "drive",
        "v3",
        credentials=credentials
    )



    metadata = {

        "name": nombre_archivo,

        "parents":[
            FOLDER_ID
        ]

    }



    media = MediaFileUpload(

        ruta_pdf,

        mimetype="application/pdf"

    )



    archivo = service.files().create(

        body=metadata,

        media_body=media,

        fields="id"

    ).execute()



    return archivo["id"]



    media = MediaFileUpload(

        ruta_pdf,

        mimetype="application/pdf"

    )



    archivo = service.files().create(

        body=metadata,

        media_body=media,

        fields="id"

    ).execute()



    return archivo.get("id")