import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import os
import uuid
import json

# ============ 1. Login con visibilidad condicional ============
USER_CREDENTIALS = {
    "inspector1": {"password": "123", "nombre": "Carlos Pérez", "cargo": "Inspector A"},
    "inspector2": {"password": "456", "nombre": "Laura Gómez", "cargo": "Inspector B"},
    "inspector3": {"password": "789", "nombre": "Juan Ruiz", "cargo": "Supervisor"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Acceso")
    with st.form("login_form"):
        username = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        login_btn = st.form_submit_button("Acceder")
        if login_btn:
            user = USER_CREDENTIALS.get(username)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.nombre = user["nombre"]
                st.session_state.cargo = user["cargo"]
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# ============ 2. Cargar credenciales de Google desde secrets ============
with open("credenciales.json", "w") as f:
    json.dump(dict(st.secrets["credenciales_json"]), f)

# ============ 3. Conexión a Google Sheets ============
def connect_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
    client = gspread.authorize(creds)
    return client.open("F6O-OP-04V2 - Lista de Verificación del Inspector de Operaciones Prueba").sheet1

def append_row(sheet, row):
    sheet.append_row(row)

# ============ 4. Generar PDF ============
def gen_pdf(data, pdf_name):
    c = canvas.Canvas(pdf_name, pagesize=A4)
    y = 800
    for campo, valor in data.items():
        c.drawString(50, y, f"{campo}: {valor}")
        y -= 20
        if y < 150:
            c.showPage()
            y = 800
    c.showPage()
    c.save()

# ============ 5. Formulario dinámico ============
st.sidebar.success(f"Bienvenido {st.session_state.nombre} - {st.session_state.cargo}")
sheet = connect_sheets()

tipo = st.selectbox("Tipo de verificación:", [
    "Conteo",
    "MEYE: Material de empaque y embalaje.",
    "Destrucción",
    "Salida de desperdicios y residuos del proceso productivo o de la prestación del servicio.",
    "Cerramiento perimetral"
])

with st.form("formulario"):
    fecha = st.date_input("Fecha:", value=datetime.today())
    hora = st.time_input("Hora:")
    lugar = st.text_input("Lugar:")
    datos = {
        "Tipo de verificación": tipo,
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Hora": hora.strftime("%H:%M"),
        "Lugar": lugar,
        "Inspector": st.session_state.nombre,
        "Cargo": st.session_state.cargo
    }

    if tipo == "Conteo":
        datos["Usuario"] = st.text_input("Usuario:")
        datos["Documento comercial"] = st.text_input("Tipo y número de documento que ampara la operación:")
        datos["Descripción de la mercancía"] = st.text_area("Descripción de la mercancía:")
        datos["Cantidad"] = st.text_input("Cantidades (bultos o unidades):")
        datos["Ubicada en el área correspondiente"] = st.radio("¿La mercancía está ubicada en el área correspondiente?", ["Sí", "NO"])
        datos["Nivel de ocupación permite inspección"] = st.radio("¿El nivel de ocupación permite la inspección?", ["Sí", "NO"])
        datos["Personas no autorizadas presentes"] = st.radio("¿Hay personas no autorizadas?", ["Sí", "NO"])
        datos["Corresponde con documentos"] = st.radio("¿La mercancía corresponde con los documentos?", ["Sí", "NO"])
        datos["Mercancía prohibida presente"] = st.radio("¿Se evidencian armas, estupefacientes, etc.?", ["Sí", "NO"])
        datos["Faltantes de mercancía"] = st.radio("¿Se evidencian faltantes respecto a la documentación?", ["Sí", "NO"])
        datos["Sobrantes de mercancía"] = st.radio("¿Se evidencian sobrantes respecto a la documentación?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto de la verificación:", ["Conforme", "No conforme"])

    elif tipo == "MEYE: Material de empaque y embalaje.":
        datos["Usuario"] = st.text_input("Usuario:")
        datos["Placa del vehículo"] = st.text_input("Placa del vehículo:")
        datos["Descripción de la mercancía"] = st.text_area("Descripción de la mercancía:")
        datos["Cantidad"] = st.text_input("Cantidad (bultos o unidades):")
        datos["Momento de inspección"] = st.radio("Momento de inspección:", ["Cargue", "Descargue", "En piso", "Báscula", "Otro"])
        datos["Acompañamiento total"] = st.radio("¿Se dio acompañamiento al cargue/descargue?", ["Sí", "NO", "No aplica"])
        datos["Corresponde con documentos"] = st.radio("¿Corresponde con los documentos?", ["Sí", "NO"])
        datos["Material es empaque/embalaje"] = st.radio("¿Corresponde a material de empaque/embalaje?", ["Sí", "NO"])
        datos["Controlado en AMIGO"] = st.radio("¿Controlado en el sistema AMIGO?", ["Sí", "NO"])
        datos["Registro fotográfico"] = st.radio("¿Registro fotográfico realizado?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto de la verificación:", ["Conforme", "No conforme"])

    else:
        datos["Observaciones"] = st.text_area("Observaciones:")
        datos["Concepto"] = st.radio("Concepto de la verificación:", ["Conforme", "No conforme"])

    enviar = st.form_submit_button("✅ Guardar y generar PDF")

if enviar:
    fila = list(datos.values())
    append_row(sheet, fila)
    pdf_file = f"verificacion_{tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    gen_pdf(datos, pdf_file)
    st.success("✅ Verificación guardada y PDF generado.")
    with open(pdf_file, "rb") as f:
        st.download_button("📄 Descargar PDF", f, file_name=pdf_file)
