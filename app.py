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

# ============ 1. Login personalizado ============
USER_CREDENTIALS = {
    "inspector1": "123",
    "inspector2": "456",
    "inspector3": "789",
    "marcela": "abc123"
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
        "Descripción", "Cantidad", "Momentos de inspección", "¿Cuál otro?", "Acompañamiento",
        "¿Aplica?", "Documentos OK", "Material OK", "Control AMIGO", "Fotos", "Concepto"
    ]

    for i, campo in enumerate(campos):
        texto = f"{campo}: {data[i]}"
        c.drawString(50, y, texto)
        y -= 20
        if y < 150:
            c.showPage()
            y = 800

    if sign:
        try:
            img = Image.open(sign).resize((150, 50))
            path = f"imagenes/sign_{uuid.uuid4().hex}.png"
            img.save(path)
            c.drawImage(path, 50, y - 60)
            y -= 80
        except:
            c.drawString(50, y, "[Firma no válida]")
            y -= 40

    for pic in pics:
        if y < 200:
            c.showPage()
            y = 800
        try:
            img = Image.open(pic)
            img.thumbnail((300, 300))
            path = f"imagenes/pic_{uuid.uuid4().hex}.jpg"
            img.save(path)
            c.drawImage(path, 50, y - 180, width=200, height=150)
            y -= 200
        except:
            c.drawString(50, y, "[Foto no válida]")
            y -= 40

    c.showPage()
    c.save()

# ============ 5. Interfaz del formulario ============
st.sidebar.success(f"Bienvenido, {st.session_state.username}")
st.title("Formulario de Verificación Inspector de Operaciones")
sheet = connect_sheets()

tipo = st.selectbox("Tipo de verificación:", [
    "MEYE: Material de empaque y embalaje.",
    "Salida de desperdicios y residuos del proceso productivo o de la prestación del servicio.",
    "Destrucción.",
    "Diferencias de peso (+-5%) en mercancías menores o iguales 100 Kg.",
    "Inspección de mantenimiento de Contenedores o unidades de carga.",
    "Inventarios de vehículos usuarios de Patios.",
    "Modificación de área.",
    "Reimportación en el mismo estado.",
    "Residuos peligrosos y/o Contaminados que no hacen parte del proceso productivo o prestación del servicio.",
    "Salida de chatarra que no hace parte del proceso productivo o prestación del servicio.",
    "Salida a Proceso Parcial y/o pruebas técnicas.",
    "Salida a Revisión, Reparación y/o Mantenimiento, pruebas técnicas.",
    "Reingreso por Proceso Parcial y/o pruebas técnicas.",
    "Reingreso por Revisión, Reparación y/o Mantenimiento, pruebas técnicas.",
    "Acompañamiento en el ingreso y salida de mercancía que no es para ningún usuario.",
    "Cerramiento perimetral.",
    "Conteo.",
    "Recorrido general al parque industrial o área declarada como Zona Franca.",
    "Verificación ingresos del TAN con SAE.",
    "Traslado de mercancía entre usuarios."
])

with st.form("formulario"):
    fecha = st.date_input("Fecha:", value=datetime.today())
    hora = st.time_input("Hora:")
    lugar = st.text_input("Lugar:")
    usuario = st.text_input("Usuario:")
    placa = st.text_input("Placa del vehículo:")
    descripcion = st.text_area("Descripción de la mercancía:")
    cantidad = st.text_input("Cantidad:")

    momentos = st.multiselect(
        "¿En qué momento se realizó inspección física?",
        ["Cargue", "Descargue", "Mercancía en Piso", "Báscula", "Otro"]
    )
    otro_momento = ""
    if "Otro" in momentos:
        otro_momento = st.text_input("¿Cuál?", placeholder="Especifique el otro momento")

    acomp = st.radio("¿Se dio acompañamiento total al cargue/descargue?", ["Sí", "No", "No aplica"])
    docs_ok = st.radio("¿La mercancía corresponde con los documentos?", ["Sí", "No"])
    material_ok = st.radio("¿La mercancía corresponde a empaque y embalaje?", ["Sí", "No"])
    control_amigo = st.radio("¿Está controlado en el sistema AMIGO?", ["Sí", "No"])
    fotos_check = st.radio("¿Registro fotográfico (obligatorio)?", ["Sí", "No"])
    concepto = st.radio("Concepto de la verificación:", ["Conforme", "No conforme"])

    firma = st.file_uploader("Firma del inspector", type=["png", "jpg", "jpeg"])
    fotos = st.file_uploader("Fotos de verificación", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    enviar = st.form_submit_button("✅ Guardar y generar PDF")

if enviar:
    fila = [
        tipo, fecha.strftime("%Y-%m-%d"), hora.strftime("%H:%M"), lugar,
        st.session_state.username, "-", usuario, placa, descripcion, cantidad,
        ", ".join(momentos), otro_momento, acomp, "-", docs_ok,
        material_ok, control_amigo, fotos_check, concepto
    ]
    append_row(sheet, fila)
    nombre_pdf = f"verif_{placa}_{fecha.strftime('%Y%m%d')}.pdf"
    gen_pdf(fila, fotos, firma, nombre_pdf)
    st.success("✅ Datos guardados y PDF generado.")
    with open(nombre_pdf, "rb") as f:
        st.download_button("📄 Descargar PDF", f, file_name=nombre_pdf)
