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

# ============ 1. Login personalizado sin bcrypt ============
USER_CREDENTIALS = {
    "inspector1": "123",
    "inspector2": "456"
}

st.title("Acceso")

with st.form("login_form"):
    username = st.text_input("Nombre de usuario")
    password = st.text_input("Contraseña", type="password")
    login_btn = st.form_submit_button("Acceder")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if login_btn:
    if USER_CREDENTIALS.get(username) == password:
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        st.error("Credenciales incorrectas")

if not st.session_state.logged_in:
    st.stop()

# ============ 2. Leer credenciales de Google desde secrets ============
with open("credenciales.json", "w") as f:
    json.dump(dict(st.secrets["credenciales_json"]), f)

# ============ 3. Conectar con Google Sheets ============
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
def gen_pdf(data, pics, sign, pdf_name):
    c = canvas.Canvas(pdf_name, pagesize=A4)
    y = 800
    campos = [
        "Tipo", "Fecha", "Hora", "Lugar", "Inspector", "Cargo", "Usuario", "Placa",
        "Descripción", "Cantidad", "Momento", "Otro", "Acompañamiento", "Aplica",
        "Docs OK", "Material OK", "Control AMIGO", "Fotos", "Concepto"
    ]
    for i, campo in enumerate(campos):
        c.drawString(50, y, f"{campo}: {data[i]}")
        y -= 20

    if sign:
        img = Image.open(sign).resize((150, 50))
        path = f"imagenes/sign_{uuid.uuid4().hex}.png"
        img.save(path)
        c.drawImage(path, 50, y - 60)
        y -= 80

    for pic in pics:
        if y < 200:
            c.showPage()
            y = 800
        img = Image.open(pic)
        img.thumbnail((300, 300))
        path = f"imagenes/pic_{uuid.uuid4().hex}.jpg"
        img.save(path)
        c.drawImage(path, 50, y - 180, width=200, height=150)
        y -= 200

    c.showPage()
    c.save()

# ============ 5. Interfaz principal ============
st.sidebar.success(f"Bienvenido, {st.session_state.username}")
st.title("Formulario de Verificación Inspector de Operaciones")
sheet = connect_sheets()

tipo = st.selectbox("Tipo de verificación:", ["MEYE", "MEE", "MEC"])

with st.form("formulario"):
    fecha = st.date_input("Fecha:", value=datetime.today())
    hora = st.time_input("Hora:")
    lugar = st.text_input("Lugar:")
    usuario = st.text_input("Usuario:")
    placa = st.text_input("Placa del vehículo:")
    descripcion = st.text_area("Descripción de la mercancía:")
    cantidad = st.text_input("Cantidad:")
    momento = st.radio("Momento de inspección:", ["Cargue", "Descargue", "En piso", "Báscula", "Otro"])
    otro = st.text_input("¿Cuál otro?", disabled=(momento != "Otro"))
    acomp = st.checkbox("¿Acompañamiento total?")
    aplica = st.checkbox("¿No aplica?")
    docs_ok = st.radio("¿Corresponde a documentos?", ["Sí", "No"])
    material_ok = st.radio("¿Corresponde al material?", ["Sí", "No"])
    control_amigo = st.radio("¿Controlado en AMIGO?", ["Sí", "No"])
    fotos_check = st.checkbox("¿Registro fotográfico?")
    concepto = st.radio("Concepto:", ["Conforme", "No conforme"])
    firma = st.file_uploader("Firma del inspector", type=["png", "jpg", "jpeg"])
    fotos = st.file_uploader("Fotos de verificación", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    enviar = st.form_submit_button("✅ Guardar y generar PDF")

if enviar:
    fila = [
        tipo, fecha.strftime("%Y-%m-%d"), hora.strftime("%H:%M"), lugar, st.session_state.username, "-", usuario, placa,
        descripcion, cantidad, momento, otro, "Sí" if acomp else "No", "Sí" if aplica else "No",
        docs_ok, material_ok, control_amigo, "Sí" if fotos_check else "No", concepto
    ]
    append_row(sheet, fila)
    nombre_pdf = f"verif_{placa}_{fecha.strftime('%Y%m%d')}.pdf"
    gen_pdf(fila, fotos, firma, nombre_pdf)
    st.success("✅ Datos guardados y PDF generado.")
    with open(nombre_pdf, "rb") as f:
        st.download_button("📄 Descargar PDF", f, file_name=nombre_pdf)
