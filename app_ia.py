import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
import tempfile

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="IA Auditor Técnico", page_icon="📡", layout="wide")
st.title("📡 Sistema de Auditoría Inteligente")

# 2. INICIALIZAR MEMORIA (Si no existe, la creamos)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# 3. BARRA LATERAL
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Groq API Key", type="password")
    if st.button("Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()

# 4. CARGA DE ARCHIVO
archivo_subido = st.file_uploader("Subir pliego o contrato (PDF)", type="pdf")

if archivo_subido and api_key:
    if not st.session_state.pdf_text:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(archivo_subido.getvalue())
            tmp_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_path)
        paginas = loader.load()
        st.session_state.pdf_text = " ".join([p.page_content for p in paginas[:10]])
        os.remove(tmp_path)
        st.success("📄 PDF analizado correctamente.")

    # 5. MOSTRAR HISTORIAL DE CHAT
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 6. ENTRADA DEL CHAT
    if prompt := st.chat_input("Hacéle una pregunta al documento..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            os.environ["GROQ_API_KEY"] = api_key
            llm = ChatGroq(model="llama-3.3-70b-versatile")
            # Enviamos contexto + historial para que tenga memoria
            contexto = f"Contexto del PDF: {st.session_state.pdf_text}\n\n"
            respuesta = llm.invoke(contexto + prompt)
            st.markdown(respuesta.content)
            st.session_state.messages.append({"role": "assistant", "content": respuesta.content})

    # 7. BOTÓN DE DESCARGA (Solo si hay chat)
    if st.session_state.messages:
        chat_export = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        st.download_button(
            label="📥 Descargar Resumen del Análisis",
            data=chat_export,
            file_name="auditoria_reporte.txt",
            mime="text/plain"
        )

else:
    st.info("Ingresá tu API Key y subí un PDF para habilitar el Auditor.")