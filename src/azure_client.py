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
    Busca las relaciones de tipo Predecesor y todas las de tipo Relacionado 
    en el JSON del Work Item, hace las peticiones a Azure y extrae la información limpia.
    """
    relations = work_item_data.get("relations", [])
    
    url_predecesor = None
    urls_relacionados = []  # <-- CAMBIO: Ahora es una lista para guardar múltiples URLs

    # 1. Recorrer las relaciones e identificar TODAS las que existan
    for rel in relations:
        tipo_relacion = rel.get("rel")
        if tipo_relacion == "System.LinkTypes.Dependency-Reverse":
            url_predecesor = rel.get("url")
        elif tipo_relacion == "System.LinkTypes.Related":
            urls_relacionados.append(rel.get("url"))  # <-- CAMBIO: Añade cada URL encontrada a la lista

    # Inicializamos el diccionario de resultados (relacionado ahora es una lista de objetos)
    resultado = {
        "predecesor": None,
        "relacionado": []  # <-- CAMBIO: Ahora devolverá una lista de historias relacionadas
    }

    # --- PROCESAR PREDECESOR (Se mantiene igual) ---
    if url_predecesor:
        if "api-version" not in url_predecesor:
            url_predecesor += "?api-version=7.1"
            
        try:
            res_pred = requests.get(url_predecesor, auth=HTTPBasicAuth("", PAT))
            res_pred.raise_for_status()
            pred_fields = res_pred.json().get("fields", {})


            titulo_completo = pred_fields.get("System.Title", "")
            partes = titulo_completo.split(":", 1)
            id_req, nom_req = (partes[0].strip(), partes[1].strip()) if len(partes) == 2 else ("No encontrado", titulo_completo)


            desc_html = pred_fields.get("System.Description", "")
            desc_limpia = BeautifulSoup(desc_html, "html.parser").get_text().strip()

            resultado["predecesor"] = {
                "id_requerimiento": id_req,
                "nombre_requerimiento": nom_req,
                "descripcion": desc_limpia
            }
        except Exception as e:
            print(f"Error al consultar el predecesor: {e}")
            
    # --- PROCESAR ELEMENTOS RELACIONADOS (Múltiples Historias de Usuario) ---
    if urls_relacionados:  # Si la lista contiene al menos una URL
        for url_rel in urls_relacionados:
            if "api-version" not in url_rel:
                url_rel += "?api-version=7.1"
                
            try:
                res_rel = requests.get(url_rel, auth=HTTPBasicAuth("", PAT))
                res_rel.raise_for_status()
                
                rel_json = res_rel.json()
                id_limpio = str(rel_json.get("id", ""))
                rel_fields = rel_json.get("fields", {})
                titulo_relacionado = rel_fields.get("System.Title", "").strip()

                # Guardamos cada HU encontrada dentro de la lista de resultados
                resultado["relacionado"].append({
                    "id_relacionado": id_limpio,
                    "titulo": titulo_relacionado
                })
            except Exception as e:
                print(f"Error al consultar el ítem relacionado {url_rel}: {e}")
    else:
        print(f"El Work Item {work_item_data.get('id')} no tiene elementos relacionados.")

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

    work_items = response.json()["workItems"]

    # Si no hay historias
    if not work_items:
        return 0

    # Obtener los IDs
    ids = ",".join(str(item["id"]) for item in work_items)

    # Consultar los títulos de todas las HU en una sola petición
    details_url = (
        f"https://dev.azure.com/{ORG}/{project_encoded}"
        f"/_apis/wit/workitems?ids={ids}"
        f"&fields=System.Title"
        f"&api-version=7.1"
    )

    details_response = requests.get(
        details_url,
        auth=HTTPBasicAuth("", PAT)
    )

    details_response.raise_for_status()

    total_historias_sprint = [
        item
        for item in details_response.json()["value"]
        if not item["fields"].get("System.Title", "").strip().lower().startswith("spike")
        ]
    
    return len(total_historias_sprint)