import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote

from src.config import PAT, ORG, PROJECT



def get_work_item(work_item_id):

    # Codifica espacios y caracteres especiales del proyecto
    project_encoded = quote(PROJECT)


    url = (
        f"https://dev.azure.com/{ORG}/{project_encoded}"
        f"/_apis/wit/workitems/{work_item_id}"
        f"?$expand=relations&api-version=7.1"
    )


    response = requests.get(
        url,
        auth=HTTPBasicAuth("", PAT)
    )
    

    response.raise_for_status()
    

    return response.json()


def get_child_tasks(work_item):

    tasks = []

    if "relations" not in work_item:
        return tasks

    for relation in work_item["relations"]:

        if relation["rel"] == "System.LinkTypes.Hierarchy-Forward":

            url = relation["url"]

            response = requests.get(
                f"{url}?api-version=7.1",
                auth=HTTPBasicAuth("", PAT)
            )
            

            response.raise_for_status()

            tasks.append(response.json())

    return tasks

