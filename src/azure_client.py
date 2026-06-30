import requests
from requests.auth import HTTPBasicAuth

from src.config import PAT, ORG, PROJECT


def get_work_item(work_item_id):

    url = (
        f"https://dev.azure.com/{ORG}/{PROJECT}"
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

def get_comments(work_item_id):

    url = (
        f"https://dev.azure.com/{ORG}/{PROJECT}"
        f"/_apis/wit/workItems/{work_item_id}"
        f"/comments?api-version=7.1-preview.4"
    )

    response = requests.get(
        url,
        auth=HTTPBasicAuth("", PAT)
    )

    response.raise_for_status()

    return response.json()