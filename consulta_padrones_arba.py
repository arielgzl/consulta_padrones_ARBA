import pandas as pd
import streamlit as st
import traceback

try:
    import dropbox
    from io import BytesIO

    st.set_page_config(page_title="Consulta ARBA", page_icon="🔍", layout="centered")

    ARCHIVOS = {
        "Retenciones":  "/Padrones/PadronRGSRet042026.TXT",
        "Percepciones": "/Padrones/PadronRGSPer042026.TXT",
    }

    COLUMNS = ["TIPO", "F_CONSULTA", "F_DESDE", "F_HASTA", "CUIT", "A0", "A1", "A2", "ALICUOTA", "A3", "A4"]
    COLS_MOSTRAR = ["CUIT", "ALICUOTA", "F_DESDE", "F_HASTA"]

    @st.cache_data(show_spinner="Descargando padrón desde Dropbox...")
    def cargar_padron(nombre: str) -> pd.DataFrame:
        dbx = dropbox.Dropbox(st.secrets["DROPBOX_TOKEN"])
        _, response = dbx.files_download(ARCHIVOS[nombre])
        df = pd.read_csv(
            BytesIO(response.content),
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

    tipo_padron = st.selectbox("Padrón a consultar:", list(ARCHIVOS.keys()))

    if st.button("Cargar padrón", type="primary"):
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
            if len(cuit_norm) == 11 and cuit_norm.isnumeric():
                resultado = buscar_cuits(padron, [cuit_norm])
                if not resultado.empty:
                    st.success(f"✅ CUIT encontrado — alícuota: **{resultado['ALICUOTA'].iloc[0]}**")
                    st.dataframe(resultado[COLS_MOSTRAR], use_container_width=True)
                else:
                    st.warning("⚠️ CUIT no encontrado en el padrón.")
            else:
                st.error("El CUIT debe tener 11 dígitos numéricos.")

    else:
        archivo = st.file_uploader("Archivo .txt con CUITs (uno por línea):", type=["txt"])

        if archivo:
            contenido = archivo.read().decode("utf-8")
            lista_raw = [normalizar_cuit(l) for l in contenido.splitlines() if l.strip()]
            lista_validos = [c for c in lista_raw if len(c) == 11 and c.isnumeric()]
            invalidos = len(lista_raw) - len(lista_validos)

            st.info(
                f"CUITs leídos: **{len(lista_validos)}** válidos" +
                (f", {invalidos} ignorados por formato incorrecto." if invalidos else ".")
            )

            resultado_lote = buscar_cuits(padron, lista_validos)

            if not resultado_lote.empty:
                st.success(f"✅ {len(resultado_lote)} registros encontrados de {len(lista_validos)} consultados.")
                st.dataframe(resultado_lote[COLS_MOSTRAR], use_container_width=True)
                st.download_button(
                    "📥 Descargar Excel",
                    data=generar_excel(resultado_lote[COLS_MOSTRAR]),
                    file_name=f"resultado_{tipo_padron.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.warning("⚠️ Ningún CUIT fue encontrado en el padrón.")

except Exception as e:
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())
