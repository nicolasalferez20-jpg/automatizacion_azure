from src.azure_client import (
    get_work_item,
    get_total_user_stories_by_sprint
)

from src.html_utils import clean_html
from src.pdf_generator import generate_pdf

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
    print(
        clean_html(work_item["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "")))

    # Obtener el Sprint de la HU
    iteration_path = work_item["fields"]["System.IterationPath"]

    print("\nSprint:")
    print(iteration_path)

    # Obtener total de HU del Sprint
    total_hu = get_total_user_stories_by_sprint(iteration_path)

    print(f"\nTotal de Historias de Usuario del Sprint: {total_hu}")

    # Generar PDF
    generate_pdf(
        work_item,
        total_hu,
        f"output/HU_{work_item_id}.pdf"
    )

except Exception as e:
    print(f"\nError: {e}")