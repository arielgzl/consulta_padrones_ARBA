import pandas as pd
import gdown

#drive = #https://drive.google.com/file/d/1rU09B2rpMGaxujg7Y1B0aX-VGU8thXaA/view?usp=sharing"

file_id = "1rU09B2rpMGaxujg7Y1B0aX-VGU8thXaA"

url = f"https://drive.google.com/uc?id={file_id}"

output = "archivo.csv"

gdown.download(url, output, quiet=False)

padron = pd.read_csv("archivo.csv", sep=";", encoding="latin1")

padron.columns = ["TIPO", "F_CONSULTA", "F_DESDE", "F_HASTA", "CUIT", "A0", "A1", "A2", "ALICUOTA", "A3", "A4"]

import streamlit as st
from io import BytesIO

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

# Interfaz Streamlit
st.title("Consulta de Alícuotas por CUIT")

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
