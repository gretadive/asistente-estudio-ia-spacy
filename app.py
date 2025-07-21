import streamlit as st
import fitz  # PyMuPDF
import spacy
import os
import csv
from datetime import datetime
import subprocess
from collections import Counter

# ------------------ Configuración ------------------
st.set_page_config(page_title="Asistente de Estudio IA", page_icon="📘")
st.title("📘 Asistente de Estudio con IA")

os.makedirs("resultados", exist_ok=True)

# ------------------ spaCy automático ------------------
@st.cache_resource
def cargar_spacy():
    return spacy.load("es_core_news_sm")


nlp = cargar_spacy()

# ------------------ Entrada ------------------
nombre_estudiante = st.text_input("👤 Ingresa tu nombre:")
pdf_file = st.file_uploader("📎 Sube tu archivo PDF", type=["pdf"])

# ------------------ Funciones ------------------
def extraer_texto_pdf(file):
    texto = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def generar_resumen(texto, num_oraciones=5):
    doc = nlp(texto)
    oraciones = list(doc.sents)
    palabras = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    frecuencias = Counter(palabras)

    puntuaciones = {}
    for sent in oraciones:
        score = sum(frecuencias.get(token.text.lower(), 0) for token in sent if token.is_alpha)
        puntuaciones[sent] = score

    oraciones_resumen = sorted(puntuaciones, key=puntuaciones.get, reverse=True)[:num_oraciones]
    return " ".join([str(oracion) for oracion in oraciones_resumen])

def generar_flashcards(texto, num_tarjetas=5):
    doc = nlp(texto)
    flashcards = []
    for sent in doc.sents:
        if ":" in sent.text:
            partes = sent.text.split(":")
            if len(partes) >= 2:
                concepto = partes[0].strip()
                definicion = partes[1].strip()
                flashcards.append({"concepto": concepto, "definicion": definicion})
        if len(flashcards) >= num_tarjetas:
            break
    return flashcards

def generar_preguntas(texto, num_preguntas=5):
    doc = nlp(texto)
    preguntas = []
    for sent in doc.sents:
        if len(sent) > 25 and len(preguntas) < num_preguntas:
            oracion = sent.text.strip()
            palabras = [token.text for token in sent if token.pos_ == "NOUN" or token.pos_ == "PROPN"]
            if palabras:
                respuesta = palabras[0]
                pregunta = oracion.replace(respuesta, "______", 1)
                distractores = ["Velocidad", "Tiempo", "Fuerza", "Energía"]
                opciones = [respuesta] + [d for d in distractores if d != respuesta]
                opciones = opciones[:4]  # máximo 4 opciones
                preguntas.append({
                    "pregunta": pregunta,
                    "opciones": sorted(opciones),
                    "respuesta": respuesta
                })
    return preguntas

def guardar_resultado(nombre, puntaje, total):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fila = [nombre, puntaje, total, fecha]
    with open("resultados/resultados.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fila)

# ------------------ Estado ------------------
for k in ["mostrar", "indice", "puntaje", "respondido", "preguntas"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ------------------ Procesamiento ------------------
if pdf_file and nombre_estudiante.strip():
    texto = extraer_texto_pdf(pdf_file)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Ver Resumen"):
            st.subheader("📄 Resumen")
            st.write(generar_resumen(texto))

    with col2:
        if st.button("💡 Ver Flashcards"):
            st.subheader("💡 Flashcards")
            tarjetas = generar_flashcards(texto)
            if tarjetas:
                for fc in tarjetas:
                    with st.expander(fc["concepto"]):
                        st.write(fc["definicion"])
            else:
                st.info("No se detectaron flashcards automáticamente.")

    with col3:
        if st.button("❓ Empezar Preguntas"):
            st.session_state["mostrar"] = True
            st.session_state["preguntas"] = generar_preguntas(texto)
            st.session_state["indice"] = 0
            st.session_state["puntaje"] = 0
            st.session_state["respondido"] = False

# ------------------ Preguntas ------------------
if st.session_state["mostrar"]:
    preguntas = st.session_state["preguntas"]
    i = st.session_state["indice"]

    if preguntas and i < len(preguntas):
        p = preguntas[i]
        st.markdown(f"### Pregunta {i+1}: {p['pregunta']}")
        seleccion = st.radio("Selecciona una opción:", p["opciones"], key=f"preg{i}")

        if not st.session_state["respondido"]:
            if st.button("Responder"):
                if seleccion == p["respuesta"]:
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

    elif preguntas:
        total = len(preguntas)
        puntaje = st.session_state["puntaje"]
        st.success(f"🎉 Has terminado. Tu puntaje: **{puntaje} de {total}**")
        guardar_resultado(nombre_estudiante.strip(), puntaje, total)

        if st.button("🔁 Volver a intentar"):
            for k in ["mostrar", "indice", "puntaje", "respondido", "preguntas"]:
                st.session_state[k] = None
            st.rerun()


       
