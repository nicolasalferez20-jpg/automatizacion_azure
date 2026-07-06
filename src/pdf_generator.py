from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from bs4 import BeautifulSoup
from src.html_utils import clean_html
from src.security_analyzer import analizar_seguridad
from datetime import datetime
from pathlib import Path

COLOR_GSE = colors.HexColor("#18E0C4")

def obtener_prototipos(html):

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    prototipos = []

    for link in soup.find_all("a"):

        descripcion = link.parent.get_text(
            " ",
            strip=True
        )

        url = link.get("href")

        prototipos.append(
            {
                "descripcion": descripcion,
                "url": url
            }
        )

    return prototipos

def organizar_criterios(html):
    soup = BeautifulSoup(html, "html.parser")

    resultado = []

    titulos = soup.find_all("b")

    if titulos:
        contador = 1

        for titulo in titulos:

            resultado.append(
                f"{contador}. {titulo.get_text(strip=True)}"
            )

            ul = titulo.find_parent().find_next("ul")

            if ul:
                for li in ul.find_all("li", recursive=False):
                    resultado.append(
                        f"&nbsp;&nbsp;&nbsp;• {li.get_text(strip=True)}"
                    )

            resultado.append("<br/>")
            contador += 1

    else:
        lis = soup.find_all("li")

        for i, li in enumerate(lis, start=1):
            resultado.append(
                f"{i}. {li.get_text(strip=True)}"
            )

    return "<br/>".join(resultado)

def organizar_requerimientos(html):
    soup = BeautifulSoup(html, "html.parser")
    resultado = []
    contador = 1
    
    # Buscamos todos los bloques que potencialmente contienen texto
    elementos = soup.find_all(["div", "li"])
    
    procesados = set()

    for elemento in elementos:
        if elemento in procesados:
            continue
            
        # 1. Averiguar si es una sublista (si tiene un 'ul' o 'ol' entre sus ancestros)
        es_sublista = elemento.find_parent(["ul", "ol"]) is not None
        
        # 2. Limpiar el texto del elemento actual sin los textos de sus hijos anidados
        # para evitar duplicación de texto en el mismo nodo
        elemento_copia = BeautifulSoup(str(elemento), "html.parser").find(elemento.name)
        
        # Quitamos sublistas e hijos grandes de la copia para extraer solo el texto de este nivel
        for hijo_molesto in elemento_copia.find_all(["ul", "ol", "div", "li"]):
            hijo_molesto.decompose()
            
        texto_limpio = elemento_copia.get_text(" ", strip=True)
        
        if not texto_limpio:
            continue
            
        # 3. Clasificar y agregar al resultado
        if es_sublista:
            resultado.append(f"&nbsp;&nbsp;&nbsp;• {texto_limpio}")
            # Marcamos este elemento como procesado
            procesados.add(elemento)
        else:
            resultado.append(f"{contador}. {texto_limpio}")
            contador += 1
            # Marcamos este elemento como procesado
            procesados.add(elemento)
            
            # Si este requerimiento principal tenía una lista interna, 
            # procesamos sus 'li' de una vez para mantener el orden visual impecable
            lista_interna = elemento.find(["ul", "ol"])
            if lista_interna:
                for sub_li in lista_interna.find_all("li"):
                    if sub_li not in procesados:
                        txt_sub = sub_li.get_text(" ", strip=True)
                        if txt_sub:
                            resultado.append(f"&nbsp;&nbsp;&nbsp;• {txt_sub}")
                        procesados.add(sub_li)

    return "<br/>".join(resultado)

def p(texto, style):
    return Paragraph(
        texto,
        style["BodyText"]
    )

def titulo_seccion(texto):
    tabla = Table(
        [[texto]],
        colWidths=[18 * cm]
    )

    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold")
        ])
    )

    return tabla

def dibujar_encabezado(canvas, doc):

    styles = getSampleStyleSheet()

    logo = Image(
        "src/assets/gse.png",
        width=3.5 * cm,
        height=2.5 * cm
    )

    titulo = Paragraph(
        """
        <para align="center">
        <font size="14">
        <b>HISTORIAS DE USUARIO</b>
        </font>
        <br/><br/>
        <font size="11">
        Desarrollo
        </font>
        </para>
        """,
        styles["BodyText"]
    )

    # TABLA DERECHA
    tabla_info = Table(
        [
            ["Código", "PTI-DS-FR-84"],
            ["Versión", "6"],
            ["Implementación", "01/08/2025"],
            ["Clasificación de\nla información", "Uso Interno"]
        ],
        colWidths=[3 * cm, 2.5 * cm],
        rowHeights=[0.8 * cm, 0.8 * cm, 0.8 * cm, 0.8 * cm]
        )

    tabla_info.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2"))
        ])
    )

    # TABLA PRINCIPAL
    encabezado = Table(
        [
            [logo, titulo, tabla_info]
        ],
        colWidths=[4 * cm, 8.5 * cm, 5.5 * cm]
    )

    encabezado.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    ancho, alto = encabezado.wrap(
        doc.width,
        doc.topMargin
    )

    encabezado.drawOn(
        canvas,
        doc.leftMargin +15,
        doc.height + doc.topMargin - alto
    )

def generate_pdf(
    work_item,
    total_hu,
    datos_requerimiento
):

    output_folder = Path("output")

    output_folder.mkdir(
        exist_ok=True
    )


    output_file = str(
        output_folder /
        f"HU_{work_item['id']}.pdf"
    )

    doc = SimpleDocTemplate(
        output_file,
        rightMargin=20,
        leftMargin=20,
        topMargin=120,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    
    elementos = []
    
    # ==================================================
    # FECHA Y PROYECTO
    # ==================================================
    # Fecha de creación de la Historia de Usuario
    fecha = work_item["fields"].get(
    "System.CreatedDate",
    ""
    )
    dia = ""
    mes = ""
    año = ""
    
    if fecha:
        fecha_limpia = fecha[:10]   # Ejemplo: 2026-06-10
        año, mes, dia = fecha_limpia.split("-")
        
        fecha_proyecto = Table(
            [
                ["FECHA", "", "", "PROYECTO"],[
            "DIA",
            "MES",
            "AÑO",
            work_item["fields"].get(
                "System.TeamProject",
                ""
            )
        ],
        [
            dia,
            mes,
            año,
            ""
        ]
    ],
    colWidths=[2 * cm, 2 * cm, 3 * cm, 11 * cm]
    )

    fecha_proyecto.setStyle(
    TableStyle([
        ("SPAN", (0, 0), (2, 0)),
        ("SPAN", (3, 1), (3, 2)),

        ("BACKGROUND", (0, 0), (2, 0), COLOR_GSE),
        ("BACKGROUND", (3, 0), (3, 0), COLOR_GSE),
        ("BACKGROUND", (0, 1), (2, 1), colors.lightgrey),

        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),

        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    )
    
    elementos.append(fecha_proyecto)
    elementos.append(Spacer(1, 10))
    # ==================================================
    # SECCIÓN 1 Y 2
    # ==================================================

    # === ADAPTACIÓN PARA LA NUEVA ESTRUCTURA ANIDADA ===
    # 1. Intentamos extraer el nodo del predecesor de forma segura
    req_info = None
    if datos_requerimiento and isinstance(datos_requerimiento, dict):
        req_info = datos_requerimiento.get("predecesor")

    # 2. Validación por si no llegó requerimiento predecesor (Mantiene tus valores por defecto)
    if not req_info:
        req_info = {
            "id_requerimiento": "N/A",
            "nombre_requerimiento": "No asignado",
            "descripcion": "No se encontró un requerimiento predecesor vinculado."
        }

    # Extraemos el nombre e ID mapeados desde la respuesta del predecesor utilizando req_info
    nombre_requerimiento = req_info["nombre_requerimiento"]
    id_requerimiento = req_info["id_requerimiento"]
    # ==================================================

    tabla12 = Table(
        [
            [
                "1. Nombre del requerimiento",
                "2. ID requerimiento"
            ],
            [
                p(nombre_requerimiento, styles),
                p(id_requerimiento, styles) # Se envuelve en p() por seguridad contra desbordes
            ]
        ],
        colWidths=[13 * cm, 5 * cm]
    )

    tabla12.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    elementos.append(tabla12)
    elementos.append(Spacer(1, 8))

    # ==================================================
    # SECCIÓN 3 (TABLA INDEPENDIENTE)
    # ==================================================

    elementos.append(
        titulo_seccion(
            "3. DESCRIPCIÓN DEL REQUERIMIENTO"
        )
    )

    # Reemplazamos 'Custom.Contexto' de la HU por la descripción real extraída del requerimiento (usando req_info)
    descripcion = req_info["descripcion"]

    tabla3 = Table(
        [[p(descripcion, styles)]],
        colWidths=[18 * cm]
    )

    tabla3.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    elementos.append(tabla3)
    elementos.append(Spacer(1, 10))

    # ==================================================
    # SECCIÓN 4 Y 5
    # ==================================================

    tabla45 = Table(
        [
            [
                "4. Tipo de requerimiento (Negocio, Tecnico, Soporte)",
                "5. Total historias de usuario"
            ],
            [
                "Tecnico",
                str(total_hu)
            ]
        ],
        colWidths=[9 * cm, 9 * cm]
    )

    tabla45.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )

    elementos.append(tabla45)
    elementos.append(Spacer(1, 8))

    # ==================================================
    # SECCIÓN 6 Y 7
    # ==================================================
    
    prioridad = work_item["fields"].get(
        "Microsoft.VSTS.Common.Priority",
        ""
    )
    prioridad_texto = {
    1: "Baja",
    2: "Media",
    3: "Alta",
    4: "Alta"
    }.get(prioridad, "N/A")

    tabla67 = Table(
        [
            [
                "6. Prioridad (Alta, Media o Baja)",
                "7. ID Historia"
            ],
            [
                prioridad_texto,
                str(work_item["id"])
            ]
        ],
        colWidths=[9 * cm, 9 * cm]
    )

    tabla67.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )

    elementos.append(tabla67)
    elementos.append(Spacer(1, 8))

    # ==================================================
    # SECCIÓN 8 Y 9
    # ==================================================
    
    complejidad = work_item["fields"].get(
    "Microsoft.VSTS.Common.Risk",
    ""
    )
    complejidad_texto = {
    "1 - High": "Alta",
    "2 - Medium": "Media",
    "3 - Low": "Baja"
    }.get(complejidad, "N/A")

    estimacion = work_item["fields"].get(
        "Microsoft.VSTS.Scheduling.StoryPoints",
        ""
    )

    tabla89 = Table(
        [
            [
                "8. Complejidad (Alta, Media o Baja)",
                "9. Estimación"
            ],
            [
                complejidad_texto,
                str(estimacion)
            ]
        ],
        colWidths=[9 * cm, 9 * cm]
    )

    tabla89.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )

    elementos.append(tabla89)
    elementos.append(Spacer(1, 8))

    # ==================================================
    # SECCIÓN 10
    # ==================================================
    requerimiento = work_item["fields"].get(
        "System.Title",
        ""
    )

    tabla10 = Table(
        [
            ["10. Nombre Historia de Usuario"],
            [requerimiento]
        ],
        colWidths=[18 * cm]
    )

    tabla10.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )

    elementos.append(tabla10)
    elementos.append(Spacer(1, 8))

    # ==================================================
    # SECCIÓN 11
    # ==================================================

    elementos.append(
        titulo_seccion(
            "11. Descripción de la historia de usuario"
        )
    )
    como = clean_html(
    work_item["fields"].get(
        "Custom.Como",
        ""
    )
    )
    quiero = clean_html(
        work_item["fields"].get(
        "System.Description",
        ""
    )
    )
    para = clean_html(
    work_item["fields"].get(
        "Custom.Para",
        ""
    )
    )
    contexto = clean_html(
    work_item["fields"].get(
        "Custom.Contexto",
        ""
    ))
    requerimientos = (
        work_item["fields"].get(
        "Custom.Requerimientos",
        ""
    ))
    criterios = clean_html(
        work_item["fields"].get(
        "Microsoft.VSTS.Common.AcceptanceCriteria",
        ""
    )
    )
    # Enumerar requerimientos
    requerimientos_numerados = organizar_requerimientos(requerimientos)

    descripcion_hu = f"""
     <b>Como:</b><br/>
      {como}
     <br/><br/>
     
     <b>Quiero:</b><br/>
     {quiero}
     <br/><br/>

     <b>Con la finalidad de:</b><br/>
     {para}
     <br/><br/>

     <b>Cuando:</b><br/>
     {contexto}
     <br/><br/>

     <b>Requerimientos:</b><br/>
     {requerimientos_numerados}
    """

    descripcion_parrafo = Paragraph(
    descripcion_hu,
    styles["BodyText"]
    )

    tabla11 = Table(
    [[descripcion_parrafo]],
    colWidths=[18 * cm]
    )

    tabla11.setStyle(
    TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ])
    )

    tabla11._argW = [18 * cm]

    elementos.append(tabla11)
    elementos.append(Spacer(1, 10))

    # ==================================================
    # SECCIÓN 12
    # ==================================================

    elementos.append(
        titulo_seccion(
            "12. Fuera de alcance"
        )
    )
 # datos ficticios
    tabla12_fuera = Table(
        [[
            "N/A."
            ""
        ]],
        colWidths=[18 * cm],
        rowHeights=[3 * cm]
    )

    tabla12_fuera.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ])
    )

    elementos.append(tabla12_fuera)
    elementos.append(Spacer(1, 10))

    # ==================================================
    # SECCIÓN 13
    # ==================================================

    elementos.append(
        titulo_seccion(
            "13. Criterios de aceptación"
        )
    )

    criterios_html = (
        work_item["fields"].get(
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            ""
        )
    )
    # organizar criterios de aceptacion
    criterios_organizados = organizar_criterios(criterios_html)
    
    tabla13 = Table(
        [[
            Paragraph(criterios_organizados,styles["BodyText"])
        ]],
        colWidths=[18 * cm]
    )

    tabla13.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black)
        ])
    )

    elementos.append(tabla13)
    elementos.append(Spacer(1, 10))

    # ==================================================
    # SECCIÓN 14
    # ==================================================

    elementos.append(
        titulo_seccion(
            "14. Criterios de seguridad"
        )
    )
    texto_hu = f"""
      Como:
      {como}
    
      Quiero:
      {quiero}
    
      Con la finalidad de:
      {para}

      Cuando:
      {contexto}

      Requerimientos:
      {requerimientos}

      Criterios de aceptación:
      {criterios}
      """
    resultado_seguridad = analizar_seguridad(
    texto_hu)

    tabla14 = Table(
        [
           [
            p("Criterio", styles),
            p("Detalle", styles)
        ],
        [
            p("Mecanismo para validar proceso de Autenticación y Autorización", styles
            ),
            p(resultado_seguridad["autenticacion"], styles
            )
        ],
        [
            p("Cifrado de datos sensibles", styles
            ),
            p(resultado_seguridad["cifrado"], styles
            )
        ],
        [
            p("Mecanismo de comprobación de integridad de los datos", styles
            ),
            p(resultado_seguridad["integridad"], styles
            )
        ],
        [
            p("Inclusión de logs de trazabilidad", styles
            ),
            p(resultado_seguridad["logs"], styles
            )
        ]
        ],
        colWidths=[7 * cm, 11 * cm]
    )
    tabla14.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
        ])
    )

    elementos.append(tabla14)
    elementos.append(Spacer(1, 10))
    # ==================================================
    # SECCIÓN 15
    # ==================================================
    elementos.append(
        titulo_seccion(
            "15. Interfaz gráfica"
        )
    )
    prototipo_html = work_item["fields"].get(
      "Custom.PrototiposoWireframes",
      ""
      )
    prototipos = obtener_prototipos(
        prototipo_html
        )
    if not prototipos:
        texto_interfaz = "N/A"
    else:
        texto_interfaz = ""
        for index, prototipo in enumerate(prototipos, start=1):
            texto_interfaz += (
                f"<b>{index}. "
                f"{prototipo['descripcion']}</b><br/>"
                )
            texto_interfaz += (
                f'<link href="{prototipo["url"]}">'
                f'Ver prototipo en Figma'
                f'</link>'
                )
            texto_interfaz += "<br/><br/>"

    tabla15 = Table(
    [[
        Paragraph(
            texto_interfaz,
            styles["BodyText"]
        )
    ]],
    colWidths=[18 * cm],
    rowHeights=[4 * cm]
    )

    tabla15.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ])
    )

    elementos.append(tabla15)
    elementos.append(Spacer(1, 10))

    # ==================================================
    # SECCIÓN 16
    # ==================================================
    elementos.append(
        titulo_seccion(
            "16. ¿Depende de otras historias de usuario?"
        )
    )

    dependencia = "N/A."
    # Extraemos el ID y el Título de la HU relacionada desde el nuevo nodo
    if datos_requerimiento and isinstance(datos_requerimiento, dict):
        relacionado = datos_requerimiento.get("relacionado")
        if relacionado and relacionado.get("titulo"):
            id_rel = relacionado.get("id_relacionado", "").strip()
            titulo_rel = relacionado.get("titulo").strip()
            
            # Armamos la cadena solo con el ID y el Título (Ej: "30026 - Nombre de la HU")
            dependencia = f"{id_rel} - {titulo_rel}" if id_rel else titulo_rel

    tabla16 = Table(
        [[dependencia]],
        colWidths=[18 * cm],
        rowHeights=[3 * cm]
    )

    tabla16.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ])
    )

    elementos.append(tabla16)
    elementos.append(Spacer(1, 10))

    # ==================================================
    # SECCIÓN 17
    # ==================================================

    elementos.append(
        titulo_seccion(
            "17. Anexos"
        )
    )

    anexos_texto = (
        "N/A"
        ""
    )

    tabla17 = Table(
        [[anexos_texto]],
        colWidths=[18 * cm],
        rowHeights=[3 * cm]
    )

    tabla17.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ])
    )

    elementos.append(tabla17)

    elementos.append(Spacer(1, 15))

    # ==================================================
    # ELABORADO POR
    # ==================================================
    fecha = work_item["fields"].get(
        "System.CreatedDate",
        "")
    dia = ""
    mes = ""
    año = ""
    fecha_formateada = "N/A"
    if fecha:
        fecha_limpia = fecha[:10]
        
        año, mes, dia = fecha_limpia.split("-")
        # Formato DD/MM/AAAA
        
        fecha_formateada = f"{dia}/{mes}/{año}"
        
    tabla_elaborado = Table(
        [
            [
                "Elaborado por",
                "Fecha",
                "Creación/Modificación",
                "Versión"
            ],
            [
                "Linda Daniela Corchuelo Pachon",
                fecha_formateada,
                "Creacion",
                "1.0"
            ]
        ],
        colWidths=[7 * cm, 4 * cm, 4 * cm, 3 * cm]
    )

    tabla_elaborado.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GSE),
            ("GRID", (0, 0), (-1, -1), 1, colors.black)
        ])
    )

    elementos.append(tabla_elaborado)
    elementos.append(Spacer(1, 15))

    # ==================================================
    # APROBADO POR
    # ==================================================
    elementos.append(
        titulo_seccion(
        "Aprobado por"
    )
    )

    tabla_aprobado = Table(
        [
            [
                "Nombre",
                "Cargo",
                "Área/Empressa",
                "Firma",
                "Fecha"
            ],
            [
                p("Marcela Bociga Angulo", styles),
                p("Coordinador de Proyectos CMMI Nivel 1", styles),
                "Desarrollo",
                "",
                ""
            ],
            [
                p("Eduin Fabian Ordonez Parra", styles),
                p("Product Manager Specialist", styles),
                "Desarrollo",
                "",
                ""
            ],
            [
                p("Carlos Alberto Rodriguez Sanchez", styles),
                p("Líder Técnico Nivel 1", styles),
                "Desarrollo",
                "",
                ""
            ]
            
        ],
        colWidths=[4.3 * cm, 4.3 * cm, 3.2 * cm, 3.9 * cm, 2.3 * cm],
        rowHeights=[1.2 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm]
    )

    tabla_aprobado.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
        ])
    )

    elementos.append(tabla_aprobado)   
    
    # ==================================================
    # GENERAR PDF
    # ==================================================

    doc.build(elementos,
    onFirstPage=dibujar_encabezado,
    onLaterPages=dibujar_encabezado
    )
    print(f"\nPDF generado correctamente: {output_file}")

    return output_file