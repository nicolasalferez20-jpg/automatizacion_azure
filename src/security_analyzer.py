import json
import google.generativeai as genai

from src.config import API_KEY

genai.configure(
    api_key=API_KEY
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

def analizar_seguridad(texto_hu):

    prompt = f"""
    Analiza la siguiente Historia de Usuario.
    
    Debes determinar si aplican estos criterios de seguridad:
    1. Mecanismo para validar proceso de Autenticación y Autorización
    2. Cifrado de datos sensibles
    3. Mecanismo de comprobación de integridad de los datos
    4. Inclusión de logs de trazabilidad

    Responde ÚNICAMENTE con JSON válido.

    Formato:

    {{
        "autenticacion": "Aplica o No aplica",
        "cifrado": "Aplica o No aplica",
        "integridad": "Aplica o No aplica",
        "logs": "Aplica o No aplica"
        }}
        Historia de Usuario:
        
        {texto_hu}
        """       
    try:

        response = model.generate_content(
            prompt
        )

        texto = response.text.strip()

        print("RESPUESTA GEMINI:")
        print(texto)

        texto = texto.replace("```json", "")
        texto = texto.replace("```", "")
        texto = texto.strip()

        return json.loads(texto)

    except Exception as e:

        print(f"Error Gemini: {e}")

        return {
            "autenticacion": "No aplica",
            "cifrado": "No aplica",
            "integridad": "No aplica",
            "logs": "No aplica"
        }