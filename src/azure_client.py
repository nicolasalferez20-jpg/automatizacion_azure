import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote

from src.config import PAT, ORG, PROJECT



def get_work_item(work_item_id):


    project_encoded = quote(PROJECT)


    url = (
        f"https://dev.azure.com/{ORG}/{project_encoded}"
        f"/_apis/wit/workitems/{work_item_id}"
        f"?api-version=7.1"
    )


    response = requests.get(
        url,
        auth=HTTPBasicAuth("", PAT)
    )
    

    response.raise_for_status()


    return response.json()


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
