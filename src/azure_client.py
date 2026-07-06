import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
from bs4 import BeautifulSoup

from src.config import PAT, ORG, PROJECT



def get_work_item(work_item_id):
    """
    Obtiene un Work Item de Azure DevOps incluyendo todas sus relaciones.
    """

    project_encoded = quote(PROJECT)


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


def get_related_work_item(work_item_data, relation_type):
    """
    Busca una relación por su tipo y devuelve el Work Item relacionado.
    Ejemplos de relation_type:

    - System.LinkTypes.Related
    - System.LinkTypes.Dependency-Reverse
    - System.LinkTypes.Hierarchy-Reverse
    - System.LinkTypes.Hierarchy-Forward
    """

    relations = work_item_data.get("relations", [])

    for relation in relations:

        if relation.get("rel") == relation_type:

            url = relation.get("url")

            if not url:
                continue

            if "api-version" not in url:
                url += "?api-version=7.1"

            response = requests.get(
                url,
                auth=HTTPBasicAuth("", PAT)
            )

            response.raise_for_status()

            return response.json()

    return None


def get_related_work_items(work_item_data, relation_type):
    """
    Devuelve una lista con TODOS los Work Items relacionados
    del tipo indicado.
    """

    relations = work_item_data.get("relations", [])

    work_items = []

    for relation in relations:

        if relation.get("rel") != relation_type:
            continue

        url = relation.get("url")

        if not url:
            continue

        if "api-version" not in url:
            url += "?api-version=7.1"

        try:

            response = requests.get(
                url,
                auth=HTTPBasicAuth("", PAT)
            )

            response.raise_for_status()

            work_items.append(
                response.json()
            )

        except requests.RequestException as e:
            print(f"Error obteniendo relación: {e}")

    return work_items

def get_predecessor_data(work_item_data):
    """
    Obtiene la información del requerimiento predecesor.
    """

    predecessor = get_related_work_item(
        work_item_data,
        "System.LinkTypes.Dependency-Reverse"
    )

    if predecessor is None:
        return None

    fields = predecessor.get("fields", {})

    titulo = fields.get("System.Title", "")

    partes = titulo.split(":", 1)

    if len(partes) == 2:
        id_requerimiento = partes[0].strip()
        nombre_requerimiento = partes[1].strip()
    else:
        id_requerimiento = str(predecessor.get("id", ""))
        nombre_requerimiento = titulo
        descripcion_html = fields.get("System.Description", "")

    descripcion = BeautifulSoup(
        descripcion_html,
        "html.parser"
    ).get_text().strip()


    return {
        "id_requerimiento": id_requerimiento,
        "nombre_requerimiento": nombre_requerimiento,
        "descripcion": descripcion
    }
def get_total_user_stories_by_sprint(iteration_path):
    """
    Retorna el número total de Historias de Usuario
    pertenecientes a un Sprint.
    """

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

    return len(response.json().get("workItems", []))


def get_related_user_story_titles(work_item_data):
    """
    Obtiene todas las Historias de Usuario relacionadas.

    Retorna una lista de textos como:

    HU-30026: Inicio de sesión
    HU-30110: Gestión de wallets
    """

    related_items = get_related_work_items(
        work_item_data,
        "System.LinkTypes.Related"
    )

    if not related_items:
        return ["N/A."]

    historias = []

    for item in related_items:

        work_item_id = item.get("id", "")

        titulo = item.get(
            "fields",
            {}
        ).get(
            "System.Title",
            "Sin título"
        )

        historias.append(
            f"HU-{work_item_id}: {titulo}"
        )

    return historias
