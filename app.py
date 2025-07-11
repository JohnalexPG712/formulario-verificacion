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
    return client.open("FO-OP-064 - Lista de Verificación del Inspector de Operaciones Prueba").sheet1

# ========== GENERAR TRAZABILIDAD ==========
def generar_trazabilidad(tipo):
    fecha = datetime.now().strftime("%Y%m%d")
    codigo = uuid.uuid4().hex[:4].upper()
    return f"FO-OP-064-{tipo.upper().split()[0]}-{fecha}-{codigo}"

# ========== GENERAR PDF CON LOGO Y FOTOS ==========
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

def marcar_opcion(valor, opciones):
    # Devuelve una cadena como: SI [X]   NO [ ]
    return "   ".join(f"{op} [{'X' if valor == op else ' '}]"
                      for op in opciones)

def generar_pdf(datos, fotos, trazabilidad):
    archivo_pdf = f"{trazabilidad}.pdf"
    c = canvas.Canvas(archivo_pdf, pagesize=A4)
    width, height = A4
    y = height - 40

    # Título principal
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width/2, y, "LISTA DE VERIFICACIÓN DEL INSPECTOR DE OPERACIONES")
    y -= 30

    # Consecutivo del documento
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Consecutivo del documento: {trazabilidad}")
    y -= 20

    # DATOS GENERALES DE LA VERIFICACIÓN
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "DATOS GENERALES DE LA VERIFICACIÓN")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"Tipo de Verificación: {datos.get('Tipo de verificación', '')}")
    y -= 15
    c.drawString(60, y, f"Cargo: {datos.get('Cargo', '')}")
    y -= 15
    c.drawString(60, y, f"Nombre del inspector: {datos.get('Funcionario', '')}")
    y -= 15
    c.drawString(60, y, f"Fecha: {datos.get('Fecha', '')}")
    y -= 15
    c.drawString(60, y, f"Hora: {datos.get('Hora', '')}")
    y -= 15
    c.drawString(60, y, f"Lugar: {datos.get('Lugar', '')}")
    y -= 25

    # RESUMEN DE LA VERIFICACIÓN
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "RESUMEN DE LA VERIFICACIÓN")
    y -= 18
    c.setFont("Helvetica", 10)

    # Preguntas y respuestas
    for campo, valor in datos.items():
        if campo in ["Trazabilidad", "Tipo de verificación", "Funcionario", "Cargo", "Fecha", "Hora", "Lugar"]:
            continue
        # Opciones SI/NO, Conforme/No conforme, etc.
        if isinstance(valor, str) and valor in ["SI", "NO"]:
            c.drawString(60, y, f"{campo}: {marcar_opcion(valor, ['SI', 'NO'])}")
        elif isinstance(valor, str) and valor in ["Conforme", "No conforme"]:
            c.drawString(60, y, f"{campo}: {marcar_opcion(valor, ['Conforme', 'No conforme'])}")
        elif isinstance(valor, str) and "," in valor and "SI" in valor and "NO" in valor:
            # Para checkboxes múltiples
            opciones = [v.strip() for v in valor.split(",")]
            c.drawString(60, y, f"{campo}: {', '.join(opciones)}")
        else:
            c.drawString(60, y, f"{campo}: {valor}")
        y -= 15
        if y < 120:
            c.showPage()
            y = height - 40

    # Ruta de almacenamiento de registros fotográficos
    if fotos:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "RUTA DE ALMACENAMIENTO O NOMBRE DE LA(S) CARPETA(S) CONTENEDORA(S) DE LOS REGISTROS FOTOGRÁFICOS")
        y -= 18
        c.setFont("Helvetica", 10)
        for i, foto in enumerate(fotos):
            c.drawString(60, y, f"Foto {i+1}: {getattr(foto, 'name', f'foto_{i+1}.jpg')}")
            y -= 15
            if y < 120:
                c.showPage()
                y = height - 40

    # Observaciones y/o novedades (si tienes un campo específico)
    if "Observaciones" in datos and datos["Observaciones"].strip():
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "OBSERVACIONES Y/O NOVEDADES EVIDENCIADAS EN EL PROCESO DE VERIFICACIÓN")
        y -= 18
        c.setFont("Helvetica", 10)
        c.drawString(60, y, datos["Observaciones"])
        y -= 25

    # Registro fotográfico
    if fotos:
        c.showPage()
        y = height - 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "REGISTRO FOTOGRÁFICO DE LA VERIFICACIÓN")
        y -= 30
        for foto in fotos:
            try:
                img = Image.open(foto)
                img.thumbnail((350, 350))
                temp_path = f"imagenes/temp_{uuid.uuid4().hex}.jpg"
                os.makedirs("imagenes", exist_ok=True)
                img.save(temp_path)
                c.drawImage(temp_path, 50, y - 180, width=250, height=150)
                y -= 170
                os.remove(temp_path)
                if y < 150:
                    c.showPage()
                    y = height - 40
            except Exception:
                c.setFont("Helvetica", 10)
                c.drawString(50, y, "[Error al cargar imagen]")
                y -= 20

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

# Título grande y destacado siempre arriba
st.title("Lista de verificación Inspector de Operaciones")

# Campos manuales antes del formulario
nombre_funcionario = st.text_input("Nombre del funcionario")
cargo_funcionario = st.text_input("Cargo del funcionario")

# Tipo de verificación fuera del formulario para refresco dinámico
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

    submit = st.form_submit_button("✅ Guardar y generar PDF")
    fotos = st.file_uploader(
        "Sube fotos de la verificación (opcional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        label_visibility="visible"
    )

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
