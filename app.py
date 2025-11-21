import os
import sys
import time
import re
import webbrowser 
from threading import Timer 
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# -------------------------------------------------------------
# CONFIGURACIÓN BASE
# -------------------------------------------------------------

# CAMBIO IMPORTANTE: 
# Al quitar "static_folder='.'", Flask buscará automáticamente:
# - HTMLs en la carpeta 'templates'
# - CSS/JS/IMG en la carpeta 'static'
app = Flask(__name__)

# --- GESTIÓN DE API KEY (HÍBRIDO: RENDER Y LOCAL) ---
# 1. Primero intentamos leer desde Variable de Entorno (Para Render)
API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. Si no existe, intentamos leer desde archivo local (Para tu PC)
if not API_KEY:
    try:
        with open("GEMINI_API_KEY.txt", "r") as f:
            API_KEY = f.read().strip()
            print("✅ API KEY cargada desde archivo local (Modo Desarrollo).")
    except FileNotFoundError:
        print("⚠️ ADVERTENCIA: No se encontró API KEY ni en variables de entorno ni en archivo local.")

# Configuración de Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("❌ ERROR: La aplicación iniciará pero el chat fallará sin la clave.")

# Nombre del modelo
MODEL_NAME = "gemini-2.5-flash-lite"

# -------------------------------------------------------------
# INSTRUCCIONES DEL SISTEMA (CEREBRO DE PATCHY)
# -------------------------------------------------------------
SYSTEM_INSTRUCTION = """
Eres "Patchy", el asistente virtual de bienestar natural del proyecto "BioPatch", creado por estudiantes en Nuevo Chimbote. 🌿
Tu tono es amable, educativo y ecológico. Usas emojis ocasionalmente.

--- 👥 EL EQUIPO DE CREADORES ---
El proyecto fue desarrollado por:
- Mera Ruiz, Valentino Eduardo
- Martínez León, Mia Luciana
- Espinoza Portilla, Gisell Fabiana
- López Tiburcio, Benjamín Antonio
- Reyna Cotos, Piero Exavier

--- 🩹 NUESTROS PRODUCTOS Y BENEFICIOS ---
1. BIOPATCH CALMANTE (Muscular):
   - Ingredientes: Eucalipto, Llantén [cite: 7], Romero y Menta[cite: 190].
   - Función: Alivia dolor muscular, reduce tensión, desinflama articulaciones (cuello, espalda) y refresca.

2. BIOPATCH FACIAL (Dermatológico):
   - Ingredientes: Gel de Aloe Vera[cite: 6].
   - Función: Hidrata profundamente, regenera la piel y ayuda a controlar el acné.

--- 🔬 CIENCIA Y MATERIALES (IMPORTANTE) ---
- El Soporte (Bioplástico): Hecho de almidón de maíz (maicena), glicerina, vinagre y agua destilada[cite: 5]. Es flexible y compostable.
- El Gel Activo (Innovación): A diferencia de otros, NO usa maicena en el gel para evitar hongos. Usamos gelatina sin sabor, glicerina y alcohol medicinal.
- Ciclo de Vida: Al terminar de usarlo, el parche sirve de abono para plantas[cite: 8]. ¡Cero residuos!

--- 📝 GUÍA DE USO Y SEGURIDAD (FAQ) ---
- ¿Cómo se aplica?: Limpia y seca la zona, aplica el parche y presiona suavemente [cite: 141-143].
- Tiempo de uso en piel: Déjalo actuar entre 4 y 8 horas[cite: 144].
- Duración del efecto: El alivio se siente por 4 a 6 horas[cite: 154].
- Caducidad (Almacenado): Dura de 12 a 24 meses en bolsa cerrada.
- Tamaños: Pequeño, mediano y grande[cite: 158].
- Niños: Sí, bajo supervisión adulta. No en piel muy sensible[cite: 146].
- Advertencias: No usar en heridas abiertas. Si hay irritación, suspender. No usar si eres alérgico al eucalipto/aloe[cite: 163].

--- 💬 TU PERSONALIDAD ---
- Saludo sugerido: "Hola 👋, soy Patchy, tu asistente de bienestar natural. ¿En qué puedo ayudarte hoy?"[cite: 112].
- Misión: Promover la salud y el cuidado del medio ambiente (reducir plásticos).
- Estilo: Respuestas claras, concisas y fundamentadas.
"""

# -------------------------------------------------------------
# FUNCIÓN PARA LIMPIAR RESPUESTA
# -------------------------------------------------------------
def clean_response(text):
    if not text:
        return ""
    text = re.sub(r"[`_]", "", text)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s*", "", text, flags=re.MULTILINE)
    return text.strip()

# -------------------------------------------------------------
# ENDPOINT: /api/chat
# -------------------------------------------------------------
@app.route('/api/chat', methods=['POST'])
def chat():
    if not API_KEY:
        return jsonify({"error": "Error de configuración: Falta API KEY"}), 500

    data = request.json
    history = data.get("history", [])

    gemini_messages = []
    for msg in history:
        parts = msg.get("parts")
        final_parts = []
        if parts:
            for p in parts:
                if isinstance(p, str):
                    final_parts.append(p)
                elif isinstance(p, dict) and "text" in p:
                    final_parts.append(p["text"])
        
        if final_parts:
            gemini_messages.append({
                "role": msg["role"],
                "parts": final_parts
            })

    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
            system_instruction=SYSTEM_INSTRUCTION
        )

        response = model.generate_content(gemini_messages)
        output_text = clean_response(response.text)
        return jsonify({"response": output_text})

    except google_exceptions.GoogleAPICallError as e:
        print(f"[Gemini API Error]: {e}")
        return jsonify({"error": "Error de comunicación con la IA. Intenta de nuevo."}), 503
    except Exception as e:
        print(f"[Server Error]: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

# -------------------------------------------------------------
# RUTAS FRONTEND
# -------------------------------------------------------------
@app.route('/')
def serve_index():
    # Ahora busca index.html dentro de la carpeta "templates"
    return render_template('index.html')

# -------------------------------------------------------------
# EJECUCIÓN
# -------------------------------------------------------------
def open_browser():
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    print("--- Servidor BioPatch Iniciado ---")
    
    # Detectar si estamos en Render para no intentar abrir navegador
    if not os.environ.get("RENDER"): 
        Timer(1.5, open_browser).start()
    
    # Render asigna un puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)