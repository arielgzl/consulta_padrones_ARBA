import pandas as pd
import gdown
import streamlit as st
from io import BytesIO

#RETENCIONES

#drive = #https://drive.google.com/file/d/1qw4c3l4X8_TrBFy4gxCzRmAxULB7edWv/view?usp=drive_link

file_id = "1qw4c3l4X8_TrBFy4gxCzRmAxULB7edWv"

url = f"https://drive.google.com/uc?id={file_id}"

output = "retenciones_ARBA.csv"

gdown.download(url, output, quiet=False, use_cookies=False)

columns = ["TIPO", "F_CONSULTA", "F_DESDE", "F_HASTA", "CUIT", "A0", "A1", "A2", "ALICUOTA", "A3", "A4"]

padron_retenciones = pd.read_csv("retenciones_ARBA.csv", sep=";", names = columns, encoding="latin1")
padron_retenciones.head()

#PERCEPCIONES

#drive = #https://drive.google.com/file/d/1gIXBcmmz5ep4X1BwZ0WJmadHr8CWAakt/view?usp=drive_link

file_id = "1gIXBcmmz5ep4X1BwZ0WJmadHr8CWAakt"

url = f"https://drive.google.com/uc?id={file_id}"

output = "percepciones_ARBA.csv"

gdown.download(url, output, quiet=False, use_cookies=False)

padron_percepciones = pd.read_csv("percepciones_ARBA.csv", sep=";", names = columns, encoding="latin1")
padron_percepciones.head()

# Función para filtrar por CUIT
def buscar_cuits(padron, lista_cuits):
    return padron[padron['CUIT'].isin(lista_cuits)]

# Función para generar archivo Excel
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultado')
    output.seek(0)
    return output

# Simulación de los dos padrones cargados como DataFrames
# Asegurate de tener esto bien cargado antes en tu código real
# padron_retenciones = pd.read_csv(...)
# padron_percepciones = pd.read_csv(...)

# Interfaz Streamlit
st.title("Consulta de Alícuotas por CUIT")

# Elegir base de datos
tipo_padron = st.selectbox("Seleccioná el padrón a consultar:", ["Retenciones", "Percepciones"])

# Selección del padrón
padron = padron_retenciones if tipo_padron == "Retenciones" else padron_percepciones

# Método de consulta
opcion = st.radio("¿Cómo querés consultar?", ["Individual", "Por lote (.txt)"])

if opcion == "Individual":
    cuit = st.text_input("Ingresá el CUIT (sin guiones ni puntos):")

    if st.button("Consultar"):
        if cuit.isnumeric() and len(cuit) == 11:
            resultado = buscar_cuits(padron, [int(cuit)])
            if not resultado.empty:
                st.success("Resultado:")
                st.dataframe(resultado[["CUIT", "ALICUOTA"]])
            else:
                st.warning("CUIT no encontrado en el padrón.")
        else:
            st.error("El CUIT debe tener 11 dígitos numéricos.")

else:
    archivo = st.file_uploader("Subí el archivo .txt con los CUITs (uno por línea)", type=["txt"])

    if archivo is not None:
        contenido = archivo.read().decode("utf-8")
        lista_cuits = [int(line.strip()) for line in contenido.strip().splitlines() if line.strip().isdigit()]

        resultado_lote = buscar_cuits(padron, lista_cuits)

        if not resultado_lote.empty:
            st.success("Resultados encontrados:")
            st.dataframe(resultado_lote[["CUIT", "ALICUOTA"]])

            excel_data = generar_excel(resultado_lote[["CUIT", "ALICUOTA"]])
            st.download_button("📥 Descargar resultados en Excel", data=excel_data, file_name="resultado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("Ningún CUIT del archivo fue encontrado en el padrón.")
