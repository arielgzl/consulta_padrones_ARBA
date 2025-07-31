import streamlit as st
import pandas as pd
from datetime import datetime
import io
import gdown

# --- Descargar el archivo CSV desde Google Drive ---
file_id = "1VKZPzoK0yFKW3vu0_9NAh2mWfyLVSeHf"
url = f"https://drive.google.com/uc?id={file_id}"
output = "archivo.csv"
gdown.download(url, output, quiet=False)

# --- Leer el archivo descargado ---
padrones_ret = pd.read_csv(output, sep=",", dtype=str)
padrones_ret["CUIT"] = padrones_ret["CUIT"].str.strip()

# --- Streamlit app ---
st.title("Consulta de Alícuota por CUIT")

# Consulta individual
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
            csv_buffer = io.StringIO()
            resultado.to_csv(csv_buffer, index=False)
            st.download_button("📥 Descargar resultado", data=csv_buffer.getvalue(), file_name=nombre_archivo)
        else:
            st.error("CUIT no encontrado.")

# Consulta por archivo
st.markdown("---")
st.subheader("📂 Consulta por Lote (archivo CSV)")
archivo = st.file_uploader("Subí un archivo .csv con columna 'CUIT'", type=["csv"])

if archivo is not None:
    try:
        cuit_consulta = pd.read_csv(archivo, dtype=str, sep=",")
        if "CUIT" not in cuit_consulta.columns:
            st.error("El archivo debe tener una columna llamada 'CUIT'.")
        else:
            cuit_consulta["CUIT"] = cuit_consulta["CUIT"].str.strip()
            resultado_lote = pd.merge(cuit_consulta[["CUIT"]], padrones_ret, on="CUIT", how="left")
            st.success("Consulta por lote realizada:")
            st.dataframe(resultado_lote)

            nombre_archivo_lote = f"resultado_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_buffer_lote = io.StringIO()
            resultado_lote.to_csv(csv_buffer_lote, index=False)
            st.download_button("⬇️ Descargar archivo resultado", data=csv_buffer_lote.getvalue(), file_name=nombre_archivo_lote)
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
