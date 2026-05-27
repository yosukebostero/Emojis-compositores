import streamlit as st
import json
from google import genai
from google.genai import types
from midiutil import MIDIFile

# Configuración de la página de Streamlit
st.set_page_config(page_title="Compositor de Emojis IA", page_icon="🎵", layout="centered")

st.title("🎵 Compositor de Música con Emojis")
st.write("¡Escribe una secuencia de emojis y Gemini la transformará en una melodía única!")

# --- MINI TUTORIAL PARA ENCONTRAR LA API KEY ---
with st.expander("🔑 ¿No tienes tu API Key de Gemini? Sigue estos 3 pasos rápidos"):
    st.markdown("""
    1. **Entra a la plataforma:** Ve a [Google AI Studio](https://ai.google.dev/) e inicia sesión con tu cuenta de Gmail.
    2. **Crea tu llave:** Dale clic al botón azul que dice **"Get API Key"** (Obtener clave de API) y luego a **"Create API Key"**.
    3. **Genera el código:** Elige la opción *"Create API key in new project"*. Te saldrá un código largo lleno de letras y números. ¡Cópialo y pégalo aquí abajo!
    
    *⚠️ **Nota de seguridad:** Tu clave no se guardará en ningún lado, solo se usa en el momento para que la IA componga tu música.*
    """)
# ------------------------------------------------

# 1. Entrada de la API Key de forma segura en la interfaz
api_key = st.text_input("Introduce tu Gemini API Key:", type="password")

# 2. Entrada de emojis del usuario
emojis_usuario = st.text_input("Escribe tus emojis aquí (Ej: 🔥🎸😎 o 🥀💔🌧️):", "🚀🌌🛸")

# Función blindada para generar el MIDI
def crear_archivo_midi(datos_musicales, nombre_archivo="melodia.mid"):
    midi = MIDIFile(1) 
    track = 0
    tiempo_canal = 0
    canal = 0
    volumen = 100 
    
    # Extraer el BPM de forma segura
    bpm_extraido = datos_musicales.get("bpm") or datos_musicales.get("BPM") or datos_musicales.get("ritmo") or 120
    try:
        bpm = int(bpm_extraido)
    except:
        bpm = 120
        
    midi.addTempo(track, tiempo_canal, bpm)
    
    # Extraer las notas de forma segura (soporta inglés y español)
    lista_notas = datos_musicales.get("notes") or datos_musicales.get("notas") or []
    
    for n in lista_notas:
        try:
            nota_midi = int(n.get("nota") or n.get("note") or 60)
            inicio = float(n.get("tiempo_inicio") or n.get("start_time") or n.get("tiempo") or 0.0)
            duracion = float(n.get("duracion") or n.get("duration") or 1.0)
            
            midi.addNote(track, canal, nota_midi, inicio, duracion, volumen)
        except:
            continue # Si una nota viene mal, la salta y no rompe todo
            
    with open(nombre_archivo, "wb") as archivo:
        midi.writeFile(archivo)
    return nombre_archivo

# Botón para componer
if st.button("✨ ¡Componer Melodía!"):
    if not api_key:
        st.error("🔑 Por favor, introduce una API Key válida de Gemini.")
    elif not emojis_usuario:
        st.warning("✍️ Escribe al menos un emoji para componer.")
    else:
        with st.spinner("🤖 Gemini está analizando tus emojis y componiendo la música..."):
            try:
                client = genai.Client(api_key=api_key)
                
                prompt = f"""
                Analiza esta secuencia de emojis: "{emojis_usuario}"
                Determina el ritmo (BPM) y traduce cada emoji en una secuencia de notas musicales.
                
                Debes responder EXCLUSIVAMENTE con un objeto JSON válido con esta estructura exacta:
                {{
                    "bpm": 120,
                    "notes": [
                        {{"nota": 60, "duracion": 1.0, "tiempo_inicio": 0.0}},
                        {{"nota": 64, "duracion": 1.0, "tiempo_inicio": 1.0}},
                        {{"nota": 67, "duracion": 2.0, "tiempo_inicio": 2.0}}
                    ]
                }}
                
                Reglas:
                - "nota": Números MIDI estándar (entre 45 y 85).
                - "duracion": Duración en pulsos (ej: 0.5, 1.0, 2.0).
                - "tiempo_inicio": El pulso en el que arranca la nota.
                - Responde SOLO el JSON, sin texto extra ni marcas ```json.
                """
                
                respuesta = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                datos_musicales = json.loads(respuesta.text)
                
                # Mostrar éxito
                st.success(f"🎼 ¡Composición lista! Ritmo estimado: {datos_musicales.get('bpm', 120)} BPM")
                
                # Generar el archivo físico
                nombre_archivo = crear_archivo_midi(datos_musicales, "cancion_emojis.mid")
                
                # --- SOLUCIÓN: Botón de descarga en vez de reproductor roto ---
                with open(nombre_archivo, "rb") as file:
                    st.download_button(
                        label="📥 Descargar archivo MIDI",
                        data=file,
                        file_name="mi_melodia_emoji.mid",
                        mime="audio/midi"
                    )
                st.info("💡 ¡Descarga el archivo y escúchalo en tu reproductor favorito (como VLC)!")
                
            except json.JSONDecodeError:
                st.error("❌ Gemini no respondió con un JSON válido. Intenta de nuevo.")
            except Exception as e:
                st.error(f"❌ Error al componer: {str(e)}")