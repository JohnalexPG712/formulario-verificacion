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

# ========== LOGIN ==========
USER_CREDENTIALS = {
    "inspector1": {"password": "123"},
    "inspector2": {"password": "456"},
    "inspector3": {"password": "789"}
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
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# ========== CARGAR CREDENCIALES GOOGLE ==========
with open("credenciales.json", "w") as f:
    json.dump(dict(st.secrets["credenciales_json"]), f)

# ========== CONEXIÓN A GOOGLE SHEETS ==========
def connect_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
    client = gspread.authorize(creds)
    return client.open("F6O-OP-04V2 - Lista de Verificación del Inspector de Operaciones Prueba").sheet1

# ========== GENERAR TRAZABILIDAD ==========
def generar_trazabilidad(tipo):
    fecha = datetime.now().strftime("%Y%m%d")
    codigo = uuid.uuid4().hex[:4].upper()
    return f"F6O-{tipo.upper().split()[0]}-{fecha}-{codigo}"

# ========== GENERAR PDF CON LOGO Y FOTOS ==========
def generar_pdf(datos, fotos, trazabilidad):
    archivo_pdf = f"{trazabilidad}.pdf"
    c = canvas.Canvas(archivo_pdf, pagesize=A4)
    y = 800

    logo_path = "logo.png"
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 50, y-40, width=100, height=50)
        y -= 60

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
                os.makedirs("imagenes", exist_ok=True)
                img.save(temp_path)
                c.drawImage(temp_path, 50, y - 200, width=250, height=150)
                y -= 220
                os.remove(temp_path)
                if y < 200:
                    c.showPage()
                    y = 800
            except Exception as e:
                c.drawString(50, y, "[Error al cargar imagen]")
                y -= 20

    c.showPage()
    c.save()
    return archivo_pdf

# ========== PREGUNTAS SEGÚN TIPO ==========
TIPOS_PREGUNTAS = {
    "Salida de desperdicios y residuos del proceso productivo o de la prestación del servicio": [
        {"label": "Usuario", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La salida es parcializada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía a retirar corresponde con la descripción y origen reportada por el usuario?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Faltantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Destrucción": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Tipo y número de documento comercial que ampara la operación", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La salida es parcializada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿En qué estado se encuentra la mercancía?", "type": "checkboxes", "options": ["Descomposición", "Daño total", "Demerito absoluto", "Deterioro"]},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Diferencias de peso (+-5%) en mercancías menores o iguales 100 Kg.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La salida es parcializada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Faltantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Sobrantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Irregularidades en los bultos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Inspección de mantenimiento de Contenedores o unidades de carga.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. de unidad de carga", "type": "text"},
        {"label": "Remolque", "type": "text"},
        {"label": "Motivo de la Reparación o el mantenimiento", "type": "textarea"},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Inventarios de vehículos usuarios de Patios.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "¿Cual es la muestra de chasis? (cantidades a verificar)", "type": "text"},
        {"label": "% de inventario auditado respecto al total actual en inventario", "type": "text"},
        {"label": "Relacione el listado de chasises auditados", "type": "textarea"},
        {"label": "¿El área calificada o autorizada está señalizada o demarcada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Si la respuesta es si, marque a continuación:", "type": "checkboxes", "options": ["Linderos con soga", "Demarcación de piso", "Otro"]},
        {"label": "¿Cúal? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿La mercancía inspeccionada esta ubicada en el área correspondiente al usuario al cual se le endosó o consignó dicha mercancía?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Hay otras personas naturales o jurídicas no autorizadas como empresas de apoyo o proveedores de servicio operando al interior de las instalaciones del usuario?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Modificación de área.": [
        {"label": "Usuario", "type": "text"},
        {"label": "¿El usuario acató los cambios en el área calificada o declarada al usuario según documento?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿El área calificada o autorizada está señalizada o demarcada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Si la respuesta es si, marque a continuación:", "type": "checkboxes", "options": ["Linderos con soga", "Demarcación de piso", "Otro"]},
        {"label": "¿Cúal? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿La mercancía inspeccionada esta ubicada en el área correspondiente al usuario al cual se le endosó o consignó dicha mercancía?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿El nivel de ocupación la bodega permite realizar la inspección?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Hay otras personas naturales o jurídicas no autorizadas como empresas de apoyo o proveedores de servicio operando al interior de las instalaciones del usuario?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Relacione los aspectos más relevantes revisados en el recorrido", "type": "textarea"},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Reimportación en el mismo estado.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Tipo y número de documento comercial que ampara la operación", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía fue objeto de transformación durante el tiempo de permanencia en la zona franca?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Residuos peligrosos y/o Contaminados que no hacen parte del proceso productivo o prestación del servicio.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Salida de chatarra que no hace parte del proceso productivo o prestación del servicio.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Salida a Proceso Parcial y/o pruebas técnicas.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿Ingresa el desperdicio del proceso?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Salida a Revisión, Reparación y/o Mantenimiento, pruebas técnicas.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Reingreso por Proceso Parcial y/o pruebas técnicas.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Tipo y número de documento comercial que ampara la operación", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía fue objeto de transformación durante el tiempo de permanencia fuera de la zona franca?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Ingresa el desperdicio del proceso?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Reingreso por Revisión, Reparación y/o Mantenimiento, pruebas técnicas.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Tipo y número de documento comercial que ampara la operación", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "Motivo de la Reparación o el mantenimiento", "type": "textarea"},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía fue objeto de transformación durante el tiempo de permanencia fuera de la zona franca?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Ingresa el desperdicio del proceso?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Acompañamiento en el ingreso y salida de mercancía que no es para ningún usuario.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Proveedor / Cliente", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Cerramiento perimetral.": [
        {"label": "Relacione los aspectos más relevantes revisados en el recorrido", "type": "textarea"},
    ],
    "Conteo": [
        {"label": "Usuario", "type": "text"},
        {"label": "Tipo y número de documento comercial que ampara la operación", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La mercancía inspeccionada está ubicada en el área correspondiente al usuario al cual se le endosó o consignó dicha mercancía?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿El nivel de ocupación la bodega permite realizar la inspección?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Hay otras personas naturales o jurídicas no autorizadas como empresas de apoyo o proveedores de servicio operando al interior de las instalaciones del usuario?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Se evidencian divisas, armas, estupefacientes, narcóticos o mercancía prohibida?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Faltantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Sobrantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Recorrido general al parque industrial o área declarada como Zona Franca.": [
        {"label": "¿El área calificada o autorizada está señalizada o demarcada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Relacione los aspectos más relevantes revisados en el recorrido", "type": "textarea"},
    ],
    "Verificación ingresos del TAN con SAE.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Remolque", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía fue objeto de transformación durante el tiempo de permanencia en la zona franca?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía fue objeto de transformación durante el tiempo de permanencia fuera de la zona franca?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Faltantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Sobrantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Irregularidades en los bultos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "Traslado de mercancía entre usuarios.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "No. FMM", "type": "text"},
        {"label": "Tipo y número de documento comercial que ampara la operación", "type": "text"},
        {"label": "No. Documento de transporte", "type": "text"},
        {"label": "No. de unidad de carga", "type": "text"},
        {"label": "Remolque", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿La salida es parcializada?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía a retirar corresponde con la descripción y origen reportada por el usuario?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Faltantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Sobrantes respecto a la documentación soporte?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿Irregularidades en los bultos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ],
    "MEYE: Material de empaque y embalaje.": [
        {"label": "Usuario", "type": "text"},
        {"label": "Placa del vehículo", "type": "text"},
        {"label": "Descripción de la mercancía", "type": "textarea"},
        {"label": "Cantidades (bultos o unidades)", "type": "text"},
        {"label": "¿En que momento se realizó inspección física?", "type": "radio", "options": ["Cargue o descargue", "Mercancía en Piso", "Báscula", "Otro"]},
        {"label": "¿Cual? (si selecciona Otro en la pregunta anterior)", "type": "text"},
        {"label": "¿Acompañamiento a la totalidad del cargue / descargue?", "type": "radio", "options": ["SI", "NO", "No aplica"]},
        {"label": "¿La mercancía física corresponde con la descripción de los documentos?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿La mercancía verificada corresponde efectivamente a material de empaque y embalaje?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "¿El material de empaque y embalaje a despachar se controla dentro del inventario del sistema AMIGO?", "type": "radio", "options": ["SI", "NO"]},
        {"label": "Registro fotográfico de la diligencia de inspección realizado", "type": "radio", "options": ["SI"]},
        {"label": "Concepto de la verificación", "type": "radio", "options": ["Conforme", "No conforme"]},
    ]
}

# ========== FORMULARIO DINÁMICO ==========
st.sidebar.success(f"Usuario: {st.session_state.username}")

sheet = connect_sheets()

st.title("Lista de verificación Inspector de Operaciones")

# Nombre y cargo manuales ANTES de la fecha y tipo
nombre_funcionario = st.text_input("Nombre del funcionario")
cargo_funcionario = st.text_input("Cargo del funcionario")

# Elige tipo de verificación FUERA del formulario
tipo = st.selectbox("Tipo de verificación:", list(TIPOS_PREGUNTAS.keys()))

with st.form("formulario"):
    trazabilidad = generar_trazabilidad(tipo)
    fecha = st.date_input("Fecha de verificación:", value=datetime.today())
    hora = st.time_input("Hora:")
    lugar = st.text_input("Lugar:")

    datos = {
        "Trazabilidad": trazabilidad,
        "Tipo de verificación": tipo,
        "Funcionario": nombre_funcionario,
        "Cargo": cargo_funcionario,
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Hora": hora.strftime("%H:%M"),
        "Lugar": lugar
    }

    for pregunta in TIPOS_PREGUNTAS[tipo]:
        label = pregunta["label"]
        if pregunta["type"] == "text":
            datos[label] = st.text_input(label)
        elif pregunta["type"] == "textarea":
            datos[label] = st.text_area(label)
        elif pregunta["type"] == "radio":
            datos[label] = st.radio(label, pregunta["options"])
        elif pregunta["type"] == "checkboxes":
            datos[label] = ", ".join(st.multiselect(label, pregunta["options"]))

    # Distribución horizontal: botón y carga de fotos
    col1, col2 = st.columns([1, 2])
    with col1:
        submit = st.form_submit_button("✅ Guardar y generar PDF")

    # Uploader debajo, ocupando todo el ancho
    st.markdown("")  # Espacio opcional
    fotos = st.file_uploader(
        "Sube fotos de la verificación (opcional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        label_visibility="visible",
        key="fotos_verificacion"
    )
    # Puedes agregar un separador visual si lo deseas:
    # st.markdown("---")
# ========== ENVÍO Y VALIDACIÓN ==========
if 'submit' in locals() and submit:
    campos_vacios = [campo for campo, valor in datos.items() if isinstance(valor, str) and not valor.strip()]
    if campos_vacios:
        st.error(f"Faltan campos obligatorios: {', '.join(campos_vacios)}")
    else:
        sheet.append_row(list(datos.values()))
        nombre_pdf = generar_pdf(datos, fotos, trazabilidad)
        st.success("✅ Formulario guardado y PDF generado.")
        with open(nombre_pdf, "rb") as f:
            st.download_button("📄 Descargar PDF", f, file_name=nombre_pdf)
