import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import json

# ========= LOGIN =========
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

# ========= CONEXIÓN GOOGLE SHEETS =========
with open("credenciales.json", "w") as f:
    json.dump(dict(st.secrets["credenciales_json"]), f)

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

# ========= GENERAR PDF =========
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

# ========= FORMULARIO =========
st.sidebar.success(f"Bienvenido {st.session_state.nombre} - {st.session_state.cargo}")
sheet = connect_sheets()

tipo = st.selectbox("Tipo de verificación:", [
    "Conteo",
    "MEYE: Material de empaque y embalaje.",
    "Destrucción"
])

st.subheader(f"Formulario de Verificación - {tipo}")

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
        datos["Documento"] = st.text_input("Tipo y número de documento:")
        datos["Descripción"] = st.text_area("Descripción de la mercancía:")
        datos["Cantidad"] = st.text_input("Cantidad (bultos o unidades):")
        datos["Ubicada en área"] = st.radio("¿Ubicada en el área correspondiente?", ["Sí", "NO"])
        datos["Nivel de ocupación"] = st.radio("¿Nivel de ocupación permite inspección?", ["Sí", "NO"])
        datos["Personas no autorizadas"] = st.radio("¿Hay personas no autorizadas?", ["Sí", "NO"])
        datos["Coincide con documentos"] = st.radio("¿Coincide con los documentos?", ["Sí", "NO"])
        datos["Mercancía prohibida"] = st.radio("¿Mercancía prohibida presente?", ["Sí", "NO"])
        datos["Faltantes"] = st.radio("¿Faltantes respecto documentación?", ["Sí", "NO"])
        datos["Sobrantes"] = st.radio("¿Sobrantes respecto documentación?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto:", ["Conforme", "No conforme"])

    elif tipo == "MEYE: Material de empaque y embalaje.":
        datos["Usuario"] = st.text_input("Usuario:")
        datos["Placa"] = st.text_input("Placa del vehículo:")
        datos["Descripción"] = st.text_area("Descripción de la mercancía:")
        datos["Cantidad"] = st.text_input("Cantidad:")
        datos["Momento"] = st.radio("Momento:", ["Cargue", "Descargue", "En piso", "Báscula", "Otro"])
        datos["Acompañamiento"] = st.radio("¿Acompañamiento total?", ["Sí", "NO", "No aplica"])
        datos["Coincide con documentos"] = st.radio("¿Coincide con documentos?", ["Sí", "NO"])
        datos["Es material de empaque"] = st.radio("¿Es material de empaque?", ["Sí", "NO"])
        datos["Controlado en AMIGO"] = st.radio("¿Controlado en AMIGO?", ["Sí", "NO"])
        datos["Registro fotográfico"] = st.radio("¿Registro fotográfico realizado?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto:", ["Conforme", "No conforme"])

    elif tipo == "Destrucción":
        datos["Usuario"] = st.text_input("Usuario:")
        datos["Placa"] = st.text_input("Placa del vehículo:")
        datos["Descripción"] = st.text_area("Descripción de la mercancía:")
        datos["Cantidad"] = st.text_input("Cantidad:")
        datos["Acta de destrucción"] = st.text_input("Acta de destrucción No.:")
        datos["Corresponde a inventario"] = st.radio("¿Corresponde al inventario?", ["Sí", "NO"])
        datos["Corresponde con acta"] = st.radio("¿Corresponde con el acta?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto:", ["Conforme", "No conforme"])

    enviar = st.form_submit_button("✅ Guardar y generar PDF")

if enviar:
    vacios = [k for k, v in datos.items() if isinstance(v, str) and not v.strip()]
    if vacios:
        st.error(f"Faltan campos obligatorios: {', '.join(vacios)}")
    else:
        fila = list(datos.values())
        append_row(sheet, fila)
        pdf_file = f"verif_{tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
        gen_pdf(datos, pdf_file)
        st.success("✅ Verificación guardada y PDF generado.")
        with open(pdf_file, "rb") as f:
            st.download_button("📄 Descargar PDF", f, file_name=pdf_file)
