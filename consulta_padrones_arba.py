import pandas as pd
import streamlit as st
import traceback

try:
    from huggingface_hub import hf_hub_download
    from io import BytesIO

    st.set_page_config(page_title="Consulta ARBA", page_icon="🔍", layout="centered")

    ARCHIVOS = {
        "Retenciones":  {"filename": "PadronRGSRet042026.TXT"},
        "Percepciones": {"filename": "PadronRGSPer042026.TXT"},
    }

    COLUMNS = ["TIPO", "F_CONSULTA", "F_DESDE", "F_HASTA", "CUIT", "A0", "A1", "A2", "ALICUOTA", "A3", "A4"]
    COLS_MOSTRAR = ["CUIT", "ALICUOTA", "F_DESDE", "F_HASTA"]

    HF_REPO = "arielgonzalez/padrones_arba"

    @st.cache_data(show_spinner="Descargando padrón desde Hugging Face...")
    def cargar_padron(nombre: str) -> pd.DataFrame:
        ruta_local = hf_hub_download(
            repo_id=HF_REPO,
            filename=ARCHIVOS[nombre]["filename"],
            repo_type="dataset",
            token=st.secrets["HF_TOKEN"],
        )
        df = pd.read_csv(
            ruta_local,
            sep=";",
            names=COLUMNS,
            encoding="latin1",
            dtype={"CUIT": str},
        )
        df["CUIT"] = df["CUIT"].str.strip()
        return df

    def normalizar_cuit(cuit: str) -> str:
        return cuit.replace("-", "").replace(".", "").strip()

    def buscar_cuits(df: pd.DataFrame, lista_cuits: list) -> pd.DataFrame:
        return df[df["CUIT"].isin(lista_cuits)]

    def generar_excel(df: pd.DataFrame) -> BytesIO:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Resultado")
        buf.seek(0)
        return buf

    st.title("🔍 Consulta de Alícuotas ARBA")

    # Al cambiar el selectbox limpia el padrón cargado anteriormente
    def limpiar_padron():
        st.session_state.pop("padron", None)
        st.session_state.pop("tipo_cargado", None)

    tipo_padron = st.selectbox(
        "Padrón a consultar:",
        list(ARCHIVOS.keys()),
        on_change=limpiar_padron,
    )

    if st.button("Cargar padrón", type="primary"):
        with st.spinner("Cargando..."):
            padron = cargar_padron(tipo_padron)
            st.session_state["padron"] = padron
            st.session_state["tipo_cargado"] = tipo_padron

    if "padron" not in st.session_state:
        st.info("Seleccioná el padrón y presioná **Cargar padrón**.")
        st.stop()

    padron = st.session_state["padron"]
    st.caption(f"Padrón cargado: **{len(padron):,} registros** ({st.session_state['tipo_cargado']})")

    opcion = st.radio("Modo de consulta:", ["Individual", "Por lote (.txt)"])

    if opcion == "Individual":
        cuit_input = st.text_input("CUIT (con o sin guiones):", placeholder="20-12345678-9")

        if st.button("Consultar", type="primary"):
            cuit_norm = normalizar_cuit(cuit_input)
            if len(cuit_norm) == 11 and cuit
