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


def get_work_item_relations_data(work_item_data):
    """
    Busca las relaciones de tipo Predecesor y Relacionado en el JSON del Work Item,
    hace las peticiones a Azure y extrae la información limpia de ambos.
    """
    relations = work_item_data.get("relations", [])
    
    url_predecesor = None
    url_relacionado = None

    # 1. Recorrer las relaciones para identificar ambas URLs
    for rel in relations:
        tipo_relacion = rel.get("rel")
        if tipo_relacion == "System.LinkTypes.Dependency-Reverse":
            url_predecesor = rel.get("url")
        elif tipo_relacion == "System.LinkTypes.Related":
            url_relacionado = rel.get("url")

    # Inicializamos el diccionario de resultados con valores por defecto
    resultado = {
        "predecesor": None,
        "relacionado": None
    }

    # --- PROCESAR PREDECESOR ---
    if url_predecesor:
        if "api-version" not in url_predecesor:
            url_predecesor += "?api-version=7.1"
            
        try:
            res_pred = requests.get(url_predecesor, auth=HTTPBasicAuth("", PAT))
            res_pred.raise_for_status()
            pred_fields = res_pred.json().get("fields", {})

            # Procesar Título (ID y Nombre)
            titulo_completo = pred_fields.get("System.Title", "")
            partes = titulo_completo.split(":", 1)
            id_req, nom_req = (partes[0].strip(), partes[1].strip()) if len(partes) == 2 else ("No encontrado", titulo_completo)

            # Limpiar HTML
            desc_html = pred_fields.get("System.Description", "")
            desc_limpia = BeautifulSoup(desc_html, "html.parser").get_text().strip()

            resultado["predecesor"] = {
                "id_requerimiento": id_req,
                "nombre_requerimiento": nom_req,
                "descripcion": desc_limpia
            }
        except Exception as e:
            print(f"Error al consultar el predecesor: {e}")
    else:
        print(f"El Work Item {work_item_data.get('id')} no tiene una tarea predecesora vinculada.")


    # --- PROCESAR RELACIONADO (Historia de Usuario) ---
    if url_relacionado:
        if "api-version" not in url_relacionado:
            url_relacionado += "?api-version=7.1"
            
        try:
            res_rel = requests.get(url_relacionado, auth=HTTPBasicAuth("", PAT))
            res_rel.raise_for_status()
            rel_fields = res_rel.json().get("fields", {})

            # Extraemos el título de la historia de usuario relacionada
            titulo_relacionado = rel_fields.get("System.Title", "").strip()

            resultado["relacionado"] = {
                "id_relacionado": url_relacionado.split("/")[-1], # Extrae el ID (ej: 30026) desde la URL
                "titulo": titulo_relacionado
            }
        except Exception as e:
            print(f"Error al consultar el ítem relacionado: {e}")
    else:
        print(f"El Work Item {work_item_data.get('id')} no tiene un elemento relacionado (`System.LinkTypes.Related`).")

    return resultado


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
