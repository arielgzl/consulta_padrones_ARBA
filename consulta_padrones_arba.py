import pandas as pd
import gdown
import streamlit as st
from io import BytesIO
import os

# ─── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Consulta ARBA", page_icon="🔍", layout="centered")

ARCHIVOS = {
    "Retenciones":  {"id": "1He_ve8_nnxtHfUsMcodQby29i1VB1rFz", "local": "retenciones_ARBA.csv"},
    "Percepciones": {"id": "1ivL1AMT4q79uWTVM5OBOrCMq-OVowQhj", "local": "percepciones_ARBA.csv"},
}

COLUMNS = ["TIPO", "F_CONSULTA", "F_DESDE", "F_HASTA", "CUIT", "A0", "A1", "A2", "ALICUOTA", "A3", "A4"]

# ─── Carga con caché (clave para archivos de 200 MB) ─────────────────────────
@st.cache_data(show_spinner="Descargando y cargando padrón...")
def cargar_padron(nombre: str) -> pd.DataFrame:
    cfg = ARCHIVOS[nombre]
    if not os.path.exists(cfg["local"]):
        gdown.download(id=cfg["id"], output=cfg["local"], quiet=False)

    df = pd.read_csv(
        cfg["local"],
        sep=";",
        names=COLUMNS,
        encoding="latin1",
        dtype={"CUIT": str},   # ← FIX: CUIT siempre como string
    )
    # Limpiar espacios/caracteres ocultos en CUIT
    df["CUIT"] = df["CUIT"].str.strip()
    return df

# ─── Helpers ──────────────────────────────────────────────────────────────────
def normalizar_cuit(cuit: str) -> str:
    """Elimina guiones, puntos y espacios."""
    return cuit.replace("-", "").replace(".", "").strip()

def buscar_cuits(df: pd.DataFrame, lista_cuits: list[str]) -> pd.DataFrame:
    return df[df["CUIT"].isin(lista_cuits)]

def generar_excel(df: pd.DataFrame) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    buf.seek(0)
    return buf

# ─── UI ───────────────────────────────────────────────────────────────────────
st.title("🔍 Consulta de Alícuotas ARBA")

tipo_padron = st.selectbox("Padrón a consultar:", list(ARCHIVOS.keys()))
padron = cargar_padron(tipo_padron)

st.caption(f"Padrón cargado: **{len(padron):,} registros**")

opcion = st.radio("Modo de consulta:", ["Individual", "Por lote (.txt)"])

COLS_MOSTRAR = ["CUIT", "ALICUOTA", "F_DESDE", "F_HASTA"]

# ── Consulta individual ───────────────────────────────────────────────────────
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

# ── Consulta por lote ─────────────────────────────────────────────────────────
else:
    archivo = st.file_uploader("Archivo .txt con CUITs (uno por línea):", type=["txt"])

    if archivo:
        contenido = archivo.read().decode("utf-8")
        lista_raw = [normalizar_cuit(l) for l in contenido.splitlines() if l.strip()]
        lista_validos = [c for c in lista_raw if len(c) == 11 and c.isnumeric()]
        invalidos = len(lista_raw) - len(lista_validos)

        st.info(f"CUITs leídos: **{len(lista_validos)}** válidos" +
                (f", {invalidos} ignorados por formato incorrecto." if invalidos else "."))

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
