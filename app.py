import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import os
import json
import uuid

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

# ========= CARGAR CREDENCIALES GOOGLE =========
with open("credenciales.json", "w") as f:
    json.dump(dict(st.secrets["credenciales_json"]), f)

# ========= CONEXIÓN A GOOGLE SHEETS =========
def connect_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
    client = gspread.authorize(creds)
    return client.open("F6O-OP-04V2 - Lista de Verificación del Inspector de Operaciones Prueba").sheet1

# ========= GENERAR TRAZABILIDAD =========
def generar_trazabilidad(tipo):
    fecha = datetime.now().strftime("%Y%m%d")
    codigo = uuid.uuid4().hex[:4].upper()
    return f"F6O-{tipo.upper().split()[0]}-{fecha}-{codigo}"

# ========= GENERAR PDF CON FOTOS =========
def generar_pdf(datos, fotos, trazabilidad):
    archivo_pdf = f"{trazabilidad}.pdf"
    c = canvas.Canvas(archivo_pdf, pagesize=A4)
    y = 800

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"FORMULARIO DE VERIFICACIÓN - {trazabilidad}")
    y -= 30
    c.setFont("Helvetica", 10)

    for campo, valor in datos.items():
        c.drawString(50, y, f"{campo}: {valor}")
        y -= 20
        if y < 150:
            c.showPage()
            y = 800

    if fotos:
        for foto in fotos:
            try:
                img = Image.open(foto)
                img.thumbnail((300, 300))
                temp_path = f"imagenes/temp_{uuid.uuid4().hex}.jpg"
                img.save(temp_path)
                c.drawImage(temp_path, 50, y - 200, width=250, height=150)
                y -= 220
                if y < 200:
                    c.showPage()
                    y = 800
            except:
                c.drawString(50, y, "[Error al cargar imagen]")
                y -= 20

    c.showPage()
    c.save()
    return archivo_pdf

# ========= FORMULARIO DINÁMICO =========
st.sidebar.success(f"Inspector: {st.session_state.nombre} – {st.session_state.cargo}")
sheet = connect_sheets()

# Lista de tipos
tipos_verificacion = [
    "Conteo",
    "MEYE: Material de empaque y embalaje.",
    "Destrucción",
    "Salida de desperdicios y residuos del proceso productivo o de la prestación del servicio.",
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
    "Recorrido general al parque industrial o área declarada como Zona Franca.",
    "Verificación ingresos del TAN con SAE.",
    "Traslado de mercancía entre usuarios."
]

tipo = st.selectbox("Tipo de verificación:", tipos_verificacion)
st.subheader(f"Formulario - {tipo}")

with st.form("formulario"):
    fecha = st.date_input("Fecha de verificación:", value=datetime.today())
    hora = st.time_input("Hora:")
    lugar = st.text_input("Lugar:")
    trazabilidad = generar_trazabilidad(tipo)
    fotos = st.file_uploader("Sube fotos de la verificación (opcional)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    datos = {
        "Trazabilidad": trazabilidad,
        "Tipo de verificación": tipo,
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Hora": hora.strftime("%H:%M"),
        "Lugar": lugar,
        "Inspector": st.session_state.nombre,
        "Cargo": st.session_state.cargo
    }

    # Preguntas específicas según tipo
    if tipo == "Conteo":
        datos["Usuario"] = st.text_input("Usuario:")
        datos["Documento"] = st.text_input("Tipo y número de documento comercial:")
        datos["Descripción"] = st.text_area("Descripción de la mercancía:")
        datos["Cantidad"] = st.text_input("Cantidad (bultos o unidades):")
        datos["Ubicada en área correspondiente"] = st.radio("¿Ubicada en área correspondiente?", ["Sí", "NO"])
        datos["Nivel ocupación adecuado"] = st.radio("¿Nivel ocupación permite inspección?", ["Sí", "NO"])
        datos["Personas no autorizadas"] = st.radio("¿Personas no autorizadas presentes?", ["Sí", "NO"])
        datos["Corresponde con documentos"] = st.radio("¿Corresponde con documentos?", ["Sí", "NO"])
        datos["Mercancía prohibida"] = st.radio("¿Mercancía prohibida presente?", ["Sí", "NO"])
        datos["Faltantes"] = st.radio("¿Faltantes evidentes?", ["Sí", "NO"])
        datos["Sobrantes"] = st.radio("¿Sobrantes evidentes?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto de la verificación:", ["Conforme", "No conforme"])

    elif tipo == "Destrucción":
        datos["Usuario"] = st.text_input("Usuario:")
        datos["Placa"] = st.text_input("Placa del vehículo:")
        datos["Descripción"] = st.text_area("Descripción:")
        datos["Cantidad"] = st.text_input("Cantidad:")
        datos["Acta de destrucción"] = st.text_input("Acta de destrucción No.:")
        datos["Corresponde a inventario"] = st.radio("¿Corresponde a inventario?", ["Sí", "NO"])
        datos["Corresponde con acta"] = st.radio("¿Corresponde con el acta?", ["Sí", "NO"])
        datos["Concepto"] = st.radio("Concepto:", ["Conforme", "No conforme"])

    else:
        datos["Descripción"] = st.text_area("Descripción de la actividad/verificación:")
        datos["Concepto"] = st.radio("Concepto de la verificación:", ["Conforme", "No conforme"])
        datos["Observaciones adicionales"] = st.text_area("Observaciones adicionales (opcional):")

    submit = st.form_submit_button("✅ Guardar y generar PDF")

# ========= ENVÍO Y VALIDACIÓN =========
if submit:
    campos_vacios = [campo for campo, valor in datos.items() if isinstance(valor, str) and not valor.strip()]
    if campos_vacios:
        st.error(f"Faltan campos obligatorios: {', '.join(campos_vacios)}")
    else:
        sheet.append_row(list(datos.values()))
        nombre_pdf = generar_pdf(datos, fotos, trazabilidad)
        st.success("✅ Formulario guardado y PDF generado.")
        with open(nombre_pdf, "rb") as f:
            st.download_button("📄 Descargar PDF", f, file_name=nombre_pdf)
