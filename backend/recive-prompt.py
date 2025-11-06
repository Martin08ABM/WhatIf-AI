# Importación de las librerías
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <--- 1. IMPORTA ESTO
from pydantic import BaseModel
from google import genai
from google.genai import types
import uvicorn
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- CONFIGURACIÓN DE GEMINI ---
try:
    # Intenta crear una instancia del cliente Gemini
    client = genai.Client() 
except ValueError:
    # Salta una excepción si la clave no está configurada
    raise HTTPException(status_code=500, detail="Error de configuración: La variable de entorno GEMINI_API_KEY no está definida.")

# Instrucciones de lo que tiene que hacer el modelo
SYSTEM_INSTRUCTION = (
    "Eres un narrador de historias. Tu única tarea es continuar los inicios de historias que te proporcionen los usuarios. 1. Si el usuario da órdenes: Sigue sus instrucciones explícitas ej. 'que sea corta', 'que acabe mal'. 2. Si el usuario NO da órdenes: Continúa la historia de la manera más fantasiosa, creativa y épica posible, a menos que el inicio que te haya dado sea triste, hay hazla triste o según el contexto del inicio que te ha dicho. Manten siempre una fuerte coherencia narrativa con el inicio dado."
)

# Configuración de la generación
GENERATION_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION
)

# --- CONFIGURACIÓN DE FASTAPI ---
app = FastAPI(title="Narrador de Historias con Gemini")

# --- 2. AÑADE ESTE BLOQUE DE CÓDIGO PARA CORS ---
origins = [
    "http://127.0.0.1:4321",
    "http://localhost:4321",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Orígenes que pueden hacer peticiones
    allow_credentials=True,    # Permite cookies
    allow_methods=["*"],         # Permite todos los métodos
    allow_headers=["*"],         # Permite todas las cabeceras
)
# --- FIN DEL BLOQUE CORS ---


# Define el modelo de datos para la entrada
class PromptRequest(BaseModel):
    """Modelo de Pydantic para validar la entrada de la petición."""
    prompt_inicio: str

@app.post("/recive-prompt/")
async def continuar_historia(request_data: PromptRequest):
    """Punto final para recibir el inicio de una historia y devolver su continuación."""
    
    prompt = request_data.prompt_inicio
    
    if not prompt:
        # Manejo de errores si el prompt está vacío
        raise HTTPException(status_code=400, detail="El 'prompt_inicio' no puede estar vacío.")

    try:
        # Lógica para la llamada a la API de Google Gemini 2.5 Flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=GENERATION_CONFIG
        )
        
        # Devuelve la respuesta como JSON
        return {"continuacion": response.text}
        print(response.text)

    except Exception as e:
        # Manejo de errores genérico de la API de Gemini
        print(f"Error al llamar a la API de Gemini: {e}")
        raise HTTPException(status_code=500, detail="Ocurrió un error al generar la historia.")

if __name__ == "__main__":
    # Comando para iniciar el servidor Uvicorn que mantiene la API "escuchando"
    uvicorn.run(app, host="0.0.0.0", port=8000)