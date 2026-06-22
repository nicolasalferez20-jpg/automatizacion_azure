from azure_client import (
    get_work_item,
    get_child_tasks,
    get_comments
)

from html_utils import clean_html
from pdf_generator import generate_pdf

import sys

try:

    if len(sys.argv) < 2:
        print("Uso: python src/main.py <ID_HU>")
        sys.exit(1)
    # Obtener ID de la HU desde la línea de comandos
    work_item_id = int(sys.argv[1])

    # Obtener Historia de Usuario
    work_item = get_work_item(work_item_id)

    print("\n" + "=" * 60)
    print("HISTORIA DE USUARIO")
    print("=" * 60)

    print(f"ID: {work_item['id']}")
    print(f"Título: {work_item['fields']['System.Title']}")
    print(f"Estado: {work_item['fields'].get('System.State', 'N/A')}")

    print("\n" + "=" * 60)
    print("DATOS DE LA HU")
    print("=" * 60)

    print("\nCOMO:")
    print(clean_html(work_item["fields"].get("Custom.Como", "")))
    
    print("\nQUIERO:")
    print(clean_html(work_item["fields"].get("System.Description", "")))

    print("\nPARA:")
    print(clean_html(work_item["fields"].get("Custom.Para", "")))

    print("\nCONTEXTO:")
    print(clean_html(work_item["fields"].get("Custom.Contexto", "")))

    print("\nREQUERIMIENTOS:")
    print(clean_html(work_item["fields"].get("Custom.Requerimientos", "")))

    print("\nCRITERIOS DE ACEPTACIÓN:")
    print( clean_html(work_item["fields"].get( "Microsoft.VSTS.Common.AcceptanceCriteria", "")))

    # Obtener tareas hijas
    tasks = get_child_tasks(work_item)

    # Diccionario para almacenar comentarios por tarea
    comments_by_task = {}

    print("\n" + "=" * 60)
    print("TAREAS HIJAS")
    print("=" * 60)

    if not tasks:
        print("No se encontraron tareas hijas")

    for task in tasks:

        print(f"\nID Tarea: {task['id']}")
        print(f"Título: {task['fields']['System.Title']}")
        print(f"Estado: {task['fields'].get('System.State', 'N/A')}")

        comments = get_comments(task["id"])

        comments_by_task[task["id"]] = []

        print("\nCOMENTARIOS")

        if comments["count"] == 0:

            print("Sin comentarios")

        else:

            for index, comment in enumerate(
                comments["comments"],
                start=1
            ):

                print("\n" + "-" * 50)
                print(f"Comentario #{index}")
                print("-" * 50)

                clean_text = clean_html(
                    comment["text"]
                )

                comments_by_task[task["id"]].append(
                    clean_text
                )

                print(clean_text)

    # Generar PDF
    generate_pdf(
        work_item,
        tasks,
        comments_by_task,
        f"output/HU_{work_item_id}.pdf"
    )

except Exception as e: print(f"\nError: {e}")