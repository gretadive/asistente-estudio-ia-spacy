import streamlit as st
import fitz  # PyMuPDF
import io
import base64
import os
from datetime import datetime

# NLP
import spacy
try:
    nlp = spacy.load("es_core_news_md")
except:
    from spacy.cli import download
    download("es_core_news_md")
    nlp = spacy.load("es_core_news_md")

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from transformers import pipeline

# Cargar modelo de spaCy español
nlp = spacy.load("es_core_news_md")

# Cargar pipeline de generación de preguntas
qg_pipeline = pipeline("text2text-generation", model="iarfmoose/t5-base-question-generator")

# Configuración inicial
st.set_page_config(page_title="Asistente de Estudio IA", page_icon="📘")
st.title("📘 Asistente de Estudio con IA Automático")
os.makedirs("resultados", exist_ok=True)

# Entrada del usuario
nombre = st.text_input("👤 Ingresa tu nombre:")
pdf_file = st.file_uploader("📎 Sube tu archivo PDF aquí", type=["pdf"])

# Funciones
def extraer_texto_pdf(file):
    texto = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()
    return texto

def detectar_temas_spacy(texto):
    doc = nlp(texto)
    temas = [ent.text for ent in doc.ents if ent.label_ in ["MISC", "ORG", "EVENT", "PRODUCT", "WORK_OF_ART"]]
    return list(set(temas))[:5]

def resumir_sumy(texto, n=5):
    parser = PlaintextParser.from_string(texto, Tokenizer("spanish"))
    resumen = LsaSummarizer()(parser.document, n)
    return "\n".join(str(oracion) for oracion in resumen)

def generar_preguntas(texto):
    chunks = texto.split(".")[:5]
    prompt = " ".join(chunks)
    preguntas_generadas = qg_pipeline(f"generate questions: {prompt}")
    return [p['generated_text'] for p in preguntas_generadas]

def guardar_resultado(nombre, temas, resumen, preguntas):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre_archivo = f"resultado_{nombre.strip().replace(' ', '_')}.txt"
    ruta = os.path.join("resultados", nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"👤 Nombre: {nombre}\n")
        f.write(f"📅 Fecha: {fecha}\n")
        f.write(f"🔍 Temas detectados: {', '.join(temas)}\n\n")
        f.write("📄 Resumen:\n")
        f.write(resumen + "\n\n")
        f.write("❓ Preguntas generadas:\n")
        for i, preg in enumerate(preguntas, 1):
            f.write(f"{i}. {preg}\n")
    return ruta

# Procesamiento principal
if pdf_file and nombre.strip():
    texto = extraer_texto_pdf(pdf_file)

    with st.spinner("Analizando contenido con IA..."):
        temas_detectados = detectar_temas_spacy(texto)
        resumen = resumir_sumy(texto)
        preguntas = generar_preguntas(texto)

    st.success("✅ Análisis completado")

    if temas_detectados:
        st.subheader("🔍 Temas detectados")
        st.markdown(", ".join(temas_detectados))

    st.subheader("📄 Resumen generado automáticamente")
    st.markdown(resumen)

    st.subheader("❓ Preguntas generadas automáticamente")
    for i, q in enumerate(preguntas, 1):
        st.markdown(f"**{i}.** {q}")

    # Guardar y preparar descarga
    ruta_txt = guardar_resultado(nombre.strip(), temas_detectados, resumen, preguntas)
    with open(ruta_txt, "r", encoding="utf-8") as f:
        contenido = f.read()
    b64 = base64.b64encode(contenido.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(ruta_txt)}">📥 Descargar resultado</a>'
    st.markdown(href, unsafe_allow_html=True)

