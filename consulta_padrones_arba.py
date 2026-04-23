import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import os

# -------------------------------
# DESCARGA ROBUSTA (SIN GDOWN)
# -------------------------------
def download_drive_file(file_id, output):
    if os.path.exists(output):
        return  # ya descargado

    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)

    # manejar confirmación de Google
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            response = session.get(URL, params={'id': file_id, 'confirm': value}, stream=True)
            break

    with open(output, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

# -------------------------------
# CARGA CON CACHE (CLAVE)
# -------------------------------
@st.cache_data
def cargar_padron(file_id, filename):
    download_drive_file(file_id, filename)

    columns = ["TIPO", "F_CONSULTA", "F_DESDE", "F_HASTA", "CUIT", "A0", "A1", "A2", "ALICUOTA", "A3", "A4"]

    df = pd.read_csv(filename, sep=";", names=columns, encoding="latin1")

    # optimización clave
    df = df[["CUIT", "ALICUOTA"]]
    df["CUIT"] = df["CUIT"].astype(str)

    return df

# -------------------------------
# CARGA PADRONES (UNA VEZ)
# -------------------------------
padron_retenciones = cargar_padron(
    "1He_ve8_nnxtHfUsMcodQby29i1VB1rFz",
    "retenciones.csv"
)

padron_percepciones = cargar_padron(
    "1ivL1AMT4q79uWTVM5OBOrCMq-OVowQhj",
    "percepciones.csv"
)

# -------------------------------
# FUNCIONES
# -------------------------------
def buscar_cuits(padron, lista_cuits):
    lista_cuits = [str(c) for c in lista_cuits]
    return padron[padron['CUIT'].isin(lista_cuits)]

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# -------------------------------
# UI
# -------------------------------
st.title("Consulta de Alícuotas por CUIT ARBA")

tipo_padron = st.selectbox(
    "Seleccioná el padrón:",
    ["Retenciones", "Percepciones"]
)

padron = padron_retenciones if tipo_padron == "Retenciones" else padron_percepciones

opcion = st.radio("Modo:", ["Individual", "Por lote (.txt)"])

# -------------------------------
# INDIVIDUAL
# -------------------------------
if opcion == "Individual":
    cuit = st.text_input("CUIT (11 dígitos):")

    if st.button("Consultar"):
        if cuit.isnumeric() and len(cuit) == 11:
            resultado = buscar_cuits(padron, [cuit])

            if not resultado.empty:
                st.dataframe(resultado)
            else:
                st.warning("No encontrado")
        else:
            st.error("CUIT inválido")

# -------------------------------
# LOTE
# -------------------------------
else:
    archivo = st.file_uploader("Archivo .txt", type=["txt"])

    if archivo:
        contenido = archivo.read().decode("utf-8")
        lista_cuits = [line.strip() for line in contenido.splitlines() if line.strip().isdigit()]

        resultado = buscar_cuits(padron, lista_cuits)

        if not resultado.empty:
            st.dataframe(resultado)

            excel = generar_excel(resultado)
            st.download_button(
                "Descargar Excel",
                data=excel,
                file_name="resultado.xlsx"
            )
        else:
            st.warning("Sin resultados")
