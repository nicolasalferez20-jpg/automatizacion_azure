import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
from bs4 import BeautifulSoup  # Asegúrate de tener instalado: pip install beautifulsoup4

from src.config import PAT, ORG, PROJECT



def get_work_item(work_item_id):
    
    project_encoded = quote(PROJECT)

    # Agregamos '&$expand=relations' al final para que Azure devuelva los enlaces (Predecesor, Parent, Child)
    url = (
        f"https://dev.azure.com/{ORG}/{project_encoded}"
        f"/_apis/wit/workitems/{work_item_id}"
        f"?api-version=7.1&$expand=relations"
    )
    

    response = requests.get(
        url,
        auth=HTTPBasicAuth("", PAT)
    )
    
    response.raise_for_status()
    
    return response.json()


def get_predecessor_data(work_item_data):
    """
    Busca la relación de tipo Predecesor en el JSON del Work Item original,
    hace la petición a Azure para traer sus datos y extrae los 3 campos limpios.
    """
    relations = work_item_data.get("relations", [])
    url_predecesor = None

    # 1. Buscar la relación exacta del predecesor
    for rel in relations:
        if rel.get("rel") == "System.LinkTypes.Dependency-Reverse":
            url_predecesor = rel.get("url")
            break

    if not url_predecesor:
        print(f"El Work Item {work_item_data.get('id')} no tiene una tarea predecesora vinculada.")
        return None

    # Opcional: Asegurar que tenga la versión de la API en la URL
    if "api-version" not in url_predecesor:
        url_predecesor += "?api-version=7.1"

    # 2. Consultar los datos específicos del requerimiento/predecesor
    response = requests.get(
        url_predecesor,
        auth=HTTPBasicAuth("", PAT)
    )
    response.raise_for_status()
    
    pred_data = response.json()
    fields = pred_data.get("fields", {})

    # 3. Procesar el Título para separar ID y Nombre usando split (SOL-RUM-014: Detalle...)
    titulo_completo = fields.get("System.Title", "")
    partes = titulo_completo.split(":", 1)

    if len(partes) == 2:
        id_requerimiento = partes[0].strip()
        nombre_requerimiento = partes[1].strip()
    else:
        id_requerimiento = "No encontrado"
        nombre_requerimiento = titulo_completo

    # 4. Limpiar el HTML de la Descripción
    descripcion_html = fields.get("System.Description", "")
    descripcion_limpia = BeautifulSoup(descripcion_html, "html.parser").get_text().strip()

    # Retornamos un diccionario listo con los tres campos que necesita tu formato
    return {
        "id_requerimiento": id_requerimiento,
        "nombre_requerimiento": nombre_requerimiento,
        "descripcion": descripcion_limpia
    }


def get_total_user_stories_by_sprint(iteration_path):
    
    project_encoded = quote(PROJECT)

    url = (
        f"https://dev.azure.com/{ORG}/{project_encoded}"
        f"/_apis/wit/wiql?api-version=7.1"
    )

    query = {
        "query": f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE
            [System.TeamProject] = '{PROJECT}'
            AND [System.WorkItemType] = 'User Story'
            AND [System.IterationPath] = '{iteration_path}'
        """
    }

    response = requests.post(
        url,
        json=query,
        auth=HTTPBasicAuth("", PAT)
    )

    response.raise_for_status()
    
    return len(response.json()["workItems"])
