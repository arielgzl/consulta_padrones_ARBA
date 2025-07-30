import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

# 🔹 Cargar padrón desde Google Drive
@st.cache_data
def cargar_padron():
    file_id = "1rU09B2rpMGaxujg7Y1B0aX-VGU8thXaA"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    response = requests.get(url)
    response.raise_for_status()

    columnas = ["Fecha_Consulta", "Fecha_desde", "Fecha_hasta", "CUIT", "A0", "A1", "A2", "Alicuota", "A3", "A4"]
    df = pd.read_csv(io.StringIO(response.text), sep=";", header=None, names=columnas, dtype=str)
    df["CUIT"] = df["CUIT"].str.strip()
    df["Alicuota"] = df["Alicuota"].str.strip()
    return df[["CUIT", "Alicuota"]].drop_duplicates()

padrones_ret = cargar_padron()

st.title("Consulta de Alícuota por CUIT")

# 🔹 Consulta Individual
st.subheader("🔎 Consulta Individual")

cuit_input = st.text_input("Ingresá un CUIT para consultar:")

if st.button("Consultar"):
    cuit_input = cuit_input.strip()
    if not cuit_input:
        st.warning("Ingresá un CUIT válido.")
    else:
        resultado = padrones_ret[padrones_ret["CUIT"] == cuit_input]
        if not resultado.empty:
            st.success("Resultado encontrado:")
            st.dataframe(resultado)

            nombre_archivo = f"consulta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            resultado.to_csv(nombre_archivo, index=False)
            with open(nombre_archivo, "rb") as f:
                st.download_button("📥 Descargar resultado", f, file_name=nombre_archivo)
        else:
            st.error("CUIT no encontrado.")

# 🔹 Consulta por archivo
st.markdown("---")
st.subheader("📂 Consulta por Lote (archivo CSV)")

archivo = st.file_uploader("Subí un archivo .csv con columna 'CUIT'", type=["csv"])

if archivo is not None:
    try:
        cuit_consulta = pd.read_csv(archivo, dtype=str)
        if "CUIT" not in cuit_consulta.columns:
            st.error("El archivo debe tener una columna llamada 'CUIT'.")
        else:
            cuit_consulta["CUIT"] = cuit_consulta["CUIT"].str.strip()
            resultado_lote = pd.merge(cuit_consulta[["CUIT"]], padrones_ret, on="CUIT", how="left")
            st.success("Consulta por lote realizada:")
            st.dataframe(resultado_lote)

            nombre_archivo_lote = f"resultado_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            resultado_lote.to_csv(nombre_archivo_lote, index=False)

            with open(nombre_archivo_lote, "rb") as f:
                st.download_button("⬇️ Descargar archivo resultado", f, file_name=nombre_archivo_lote)
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
