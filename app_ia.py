import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
import tempfile

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="IA Auditor Técnico", page_icon="📡", layout="wide")
st.title("📡 Sistema de Auditoría de Pliegos - Ing. Cristian Loyola")

# 2. MEMORIA Y ESTADO
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# 3. BARRA LATERAL CON GUÍA PARA EL CLIENTE
with st.sidebar:
    st.header("🔑 Acceso y Seguridad")
    api_key = st.text_input("Ingresá tu Groq API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 💡 ¿Cómo obtener tu llave?")
    st.markdown("""
    1. Registrate gratis en [Groq Console](https://console.groq.com).
    2. Hacé clic en **'Create API Key'**.
    3. Copiá el código y pegalo aquí arriba.
    *Tu llave es privada y solo se usa para esta sesión.*
    """)
    
    if st.button("Limpiar historial"):
        st.session_state.messages = []
        st.session_state.pdf_text = ""
        st.rerun()

# 4. CARGA MULTI-PDF
archivos_subidos = st.file_uploader("Subí uno o varios archivos PDF (Pliegos, Contratos, Normas)", type="pdf", accept_multiple_files=True)

if archivos_subidos and api_key:
    # Si detectamos nuevos archivos, procesamos
    if not st.session_state.pdf_text:
        texto_consolidado = ""
        for archivo in archivos_subidos:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(archivo.getvalue())
                tmp_path = tmp_file.name
            
            try:
                loader = PyPDFLoader(tmp_path)
                paginas = loader.load()
                texto_consolidado += f"\n--- DOCUMENTO: {archivo.name} ---\n"
                texto_consolidado += " ".join([p.page_content for p in paginas])
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        st.session_state.pdf_text = texto_consolidado
        st.success(f"✅ {len(archivos_subidos)} archivo(s) analizado(s) con éxito.")

    # 5. CHAT CON INSTRUCCIÓN ESTRICTA (GUARDRAILS)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Preguntá sobre los documentos subidos..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            os.environ["GROQ_API_KEY"] = api_key
            llm = ChatGroq(model="llama-3.3-70b-versatile")
            
            # EL PROMPT ESTRÍCTO (El corazón del Agente)
            prompt_estricto = f"""
            Eres un AGENTE DE AUDITORÍA TÉCNICA especializado en Telecomunicaciones.
            Tu MISIÓN es responder consultas BASÁNDOTE ÚNICAMENTE en el contenido de los documentos proporcionados.

            REGLAS DE ORO:
            1. Si la información NO está en los documentos, responde: "Lo siento, esa información no figura en la documentación técnica proporcionada."
            2. NO utilices conocimiento externo ni hables de otros temas.
            3. Si los documentos se contradicen, menciona la discrepancia entre ellos.
            
            CONTENIDO DE LOS DOCUMENTOS:
            {st.session_state.pdf_text[:15000]} 

            PREGUNTA DEL USUARIO:
            {prompt}
            """
            
            with st.spinner("Analizando documentos..."):
                respuesta = llm.invoke(prompt_estricto)
                st.markdown(respuesta.content)
                st.session_state.messages.append({"role": "assistant", "content": respuesta.content})
else:
    st.info("👋 ¡Bienvenido! Por favor, cargá tu API Key y al menos un PDF para comenzar la auditoría técnica.")
