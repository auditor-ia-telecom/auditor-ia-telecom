import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
import tempfile

# 1. CONFIGURACIÓN DE PÁGINA (Nivel PRO)
st.set_page_config(page_title="IA Auditor Técnico", page_icon="📡", layout="wide")
st.title("📡 Sistema de Auditoría de Pliegos - Ing. Cristian Loyola")

# 2. INICIALIZAR ESTADOS DE MEMORIA
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# 3. BARRA LATERAL (Configuración y Herramientas)
with st.sidebar:
    st.header("🔑 Acceso y Seguridad")
    api_key = st.text_input("Ingresá tu Groq API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 💡 Guía Rápida")
    st.markdown("""
    1. Obtené tu llave gratis en [Groq Console](https://console.groq.com).
    2. Subí hasta 3 PDFs técnicos.
    3. Consultá datos específicos.
    *La sesión es privada y segura.*
    """)
    
    # BOTÓN DE DESCARGA: Aparece aquí cuando hay contenido en el chat
    if st.session_state.messages:
        st.markdown("---")
        st.subheader("📥 Reporte")
        chat_export = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button(
            label="Descargar Análisis (TXT)",
            data=chat_export,
            file_name="auditoria_reporte.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("---")
    if st.button("Limpiar todo y reiniciar", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pdf_text = ""
        st.rerun()

# 4. CARGA DE ARCHIVOS (Múltiple)
archivos_subidos = st.file_uploader("Subí tus archivos PDF (Pliegos, Contratos, Normas)", type="pdf", accept_multiple_files=True)

if archivos_subidos and api_key:
    # Procesamos los PDFs si aún no han sido cargados en esta sesión
    if not st.session_state.pdf_text:
        with st.status("Analizando documentos...", expanded=True) as status:
            texto_consolidado = ""
            for archivo in archivos_subidos:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(archivo.getvalue())
                    tmp_path = tmp_file.name
                try:
                    loader = PyPDFLoader(tmp_path)
                    paginas = loader.load()
                    texto_consolidado += f"\n\n--- ORIGEN: {archivo.name} ---\n"
                    texto_consolidado += " ".join([p.page_content for p in paginas])
                    st.write(f"✅ {archivo.name} procesado.")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            st.session_state.pdf_text = texto_consolidado
            status.update(label="Análisis completo", state="complete", expanded=False)

    # 5. INTERFAZ DE CHAT (Estilo Agente)
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
            
            # EL PROMPT ESTRICTO (El cerebro del Agente)
            prompt_estricto = f"""
            Eres un AGENTE DE AUDITORÍA TÉCNICA especializado en Telecomunicaciones. 
            Tu MISIÓN es responder consultas BASÁNDOTE ÚNICAMENTE en el contenido de los documentos proporcionados.

            REGLAS DE ORO:
            1. Si la información NO está en los documentos, responde: "Lo siento, esa información no figura en la documentación técnica proporcionada."
            2. NO utilices conocimiento previo sobre marcas, leyes o normas que no estén mencionadas en este texto.
            3. Si el usuario te saluda, recuérdale brevemente que estás listo para auditar los documentos.
            
            DOCUMENTACIÓN DE REFERENCIA:
            {st.session_state.pdf_text[:18000]} 

            PREGUNTA DEL USUARIO:
            {prompt}
            """
            
            respuesta = llm.invoke(prompt_estricto)
            st.markdown(respuesta.content)
            st.session_state.messages.append({"role": "assistant", "content": respuesta.content})
            # Forzamos refresco para que aparezca el botón de descarga en la sidebar
            st.rerun()
else:
    if not api_key:
        st.warning("⚠️ Por favor, ingresá tu API Key en la barra lateral para comenzar.")
    if not archivos_subidos:
        st.info("👋 Subí al menos un archivo PDF para habilitar el análisis del Agente.")

