import spacy
import subprocess

@st.cache_resource
def cargar_spacy():
    try:
        return spacy.load("es_core_news_sm")
    except:
        subprocess.run(["python", "-m", "spacy", "download", "es_core_news_sm"])
        return spacy.load("es_core_news_sm")

nlp = cargar_spacy()


# ------------------- Diccionario de temas -------------------
temas = {
    "MRU": {
        "resumen": """
        - Movimiento con velocidad constante.
        - Aceleración igual a cero.
        - Fórmula: x(t) = x₀ + vt.
        """,
        "flashcards": [
            {"concepto": "Velocidad constante", "definicion": "La velocidad no cambia con el tiempo."},
            {"concepto": "Aceleración nula", "definicion": "No hay cambio en la velocidad del cuerpo."}
        ],
        "preguntas": [
            {
                "pregunta": "¿Qué característica tiene el MRU?",
                "opciones": ["Aceleración constante", "Velocidad constante", "Movimiento circular", "Aceleración variable"],
                "respuesta": "Velocidad constante"
            },
            {
                "pregunta": "¿Cuál es la aceleración en MRU?",
                "opciones": ["9.8 m/s²", "0 m/s²", "10 m/s²", "Depende de la masa"],
                "respuesta": "0 m/s²"
            }
        ]
    },
    "MRUV": {
        "resumen": """
        - Movimiento con aceleración constante.
        - Fórmulas: v = v₀ + at, x = x₀ + v₀t + ½at².
        """,
        "flashcards": [
            {"concepto": "Aceleración constante", "definicion": "El cambio de velocidad por unidad de tiempo es constante."},
            {"concepto": "Velocidad inicial", "definicion": "La velocidad al comenzar el movimiento."}
        ],
        "preguntas": [
            {
                "pregunta": "¿Qué representa la 'a' en MRUV?",
                "opciones": ["Área", "Aceleración", "Altura", "Amplitud"],
                "respuesta": "Aceleración"
            }
        ]
    },
    "Caída Libre": {
        "resumen": """
        - Movimiento vertical bajo gravedad.
        - Aceleración constante: g = 9.8 m/s².
        """,
        "flashcards": [
            {"concepto": "Gravedad", "definicion": "Fuerza que atrae objetos hacia el centro de la Tierra."}
        ],
        "preguntas": [
            {
                "pregunta": "¿Cuál es el valor de la gravedad?",
                "opciones": ["10 m/s²", "9.8 m/s²", "0 m/s²", "1 g"],
                "respuesta": "9.8 m/s²"
            }
        ]
    }
}

# ------------------- Configuración Inicial -------------------
st.set_page_config(page_title="Asistente de Estudio IA", page_icon="📘")
st.title("📘 Asistente de Estudio con IA")

os.makedirs("resultados", exist_ok=True)

nombre_estudiante = st.text_input("👤 Ingresa tu nombre:")
pdf_file = st.file_uploader("📎 Sube tu archivo PDF", type=["pdf"])

# ------------------- Funciones -------------------
def extraer_texto_pdf(file):
    texto = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

import spacy
from collections import Counter

# Cargar modelo spaCy en español
nlp = spacy.load("es_core_news_sm")

# Palabras clave por tema
palabras_clave = {
    "MRU": ["velocidad constante", "aceleración cero", "x(t) = x₀ + vt", "mru"],
    "MRUV": ["aceleración constante", "v = v₀ + at", "x = x₀ + v₀t + ½at²", "mruv"],
    "Caída Libre": ["gravedad", "9.8", "v = gt", "y = ½gt²", "caída libre"]
}

def detectar_tema(texto):
    texto = texto.lower()
    doc = nlp(texto)

    # Unir palabras clave encontradas
    tokens = [token.text for token in doc]
    texto_procesado = " ".join(tokens)

    conteo = {}

    for tema, palabras in palabras_clave.items():
        count = sum(texto_procesado.count(p.lower()) for p in palabras)
        conteo[tema] = count

    # Seleccionamos el tema con más coincidencias
    tema_detectado = max(conteo, key=conteo.get)

    if conteo[tema_detectado] > 0:
        return tema_detectado
    else:
        return None


def guardar_resultado(nombre, tema, puntaje, total):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("resultados/resultados.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([nombre, tema, puntaje, total, fecha])

# ------------------- Estado -------------------
for key in ["mostrar_preguntas", "indice", "puntaje", "respondido", "tema"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ------------------- Procesamiento PDF -------------------
if pdf_file and nombre_estudiante.strip():
    texto = extraer_texto_pdf(pdf_file)
    tema = detectar_tema(texto)

    if tema:
        st.success(f"✅ Tema detectado: {tema}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Ver Resumen"):
                st.markdown(temas[tema]["resumen"])

        with col2:
            if st.button("💡 Ver Flashcards"):
                for fc in temas[tema]["flashcards"]:
                    with st.expander(fc["concepto"]):
                        st.write(fc["definicion"])

        with col3:
            if st.button("❓ Empezar Preguntas"):
                st.session_state["mostrar_preguntas"] = True
                st.session_state["indice"] = 0
                st.session_state["puntaje"] = 0
                st.session_state["respondido"] = False
                st.session_state["tema"] = tema
    else:
        st.warning("⚠ No se pudo detectar el tema del PDF.")

# ------------------- Preguntas -------------------
if st.session_state["mostrar_preguntas"]:
    preguntas = temas[st.session_state["tema"]]["preguntas"]
    i = st.session_state["indice"]

    if i < len(preguntas):
        p = preguntas[i]
        st.markdown(f"### Pregunta {i+1}: {p['pregunta']}")
        respuesta = st.radio("Selecciona una opción:", p["opciones"], key=f"preg{i}")

        if not st.session_state["respondido"]:
            if st.button("Responder"):
                if respuesta == p["respuesta"]:
                    st.success("✅ ¡Correcto!")
                    st.session_state["puntaje"] += 1
                else:
                    st.error(f"❌ Incorrecto. Respuesta correcta: {p['respuesta']}")
                st.session_state["respondido"] = True
        else:
            if st.button("➡️ Siguiente"):
                st.session_state["indice"] += 1
                st.session_state["respondido"] = False
                st.rerun()
    else:
        total = len(preguntas)
        puntaje = st.session_state["puntaje"]
        st.success(f"🎉 Puntaje final: **{puntaje} de {total}**")
        guardar_resultado(nombre_estudiante.strip(), st.session_state["tema"], puntaje, total)

        if st.button("🔁 Volver a intentar"):
            for k in ["mostrar_preguntas", "indice", "puntaje", "respondido", "tema"]:
                st.session_state[k] = None
            st.rerun()
