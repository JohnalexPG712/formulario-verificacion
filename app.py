import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
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

# ========== TÍTULO DEL FORMULARIO ==========
st.markdown(
    """
    <div style='background-color: #f0f2f6; padding: 18px 8px 18px 8px; border-radius: 10px; margin-bottom: 18px; border: 1px solid #DDD;'>
        <h2 style='color: #262730; text-align:center; margin:0;'>Lista de verificación Inspector de Operaciones</h2>
    </div>
    """,
    unsafe_allow_html=True
)

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

# ========== FUNCIONES AUXILIARES PARA PDF ==========
def marcar_opcion_pdf(valor_seleccionado, opciones_disponibles):
    # Genera la cadena para el PDF con cuadros y el valor seleccionado
    # Ejemplo: "SI ☒ NO ☐"
    result = []
    for opcion in opciones_disponibles:
        if isinstance(valor_seleccionado, list):
            result.append(f"{opcion} {'☒' if opcion in valor_seleccionado else '☐'}")
        else:
            result.append(f"{opcion} {'☒' if str(opcion) == str(valor_seleccionado) else '☐'}")
    return "   ".join(result)

# ========== GENERAR PDF CON ESTRUCTURA OFICIAL ==========
def generar_pdf(datos, fotos, trazabilidad):
    archivo_pdf = f"{trazabilidad}.pdf"
    c = canvas.Canvas(archivo_pdf, pagesize=A4)
    width, height = A4
    margin_left = 30
    current_y = height - 30

    blue_color = colors.Color(47/255, 82/255, 143/255)
    light_blue_color = colors.Color(220/255, 230/255, 241/255)

    # Título principal con fondo azul
    c.setFillColor(blue_color)
    c.rect(0, current_y - 20, width, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width/2, current_y - 10, "LISTA DE VERIFICACIÓN DEL INSPECTOR DE OPERACIONES")
    current_y -= 40

    # Consecutivo del documento
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(margin_left, current_y, f"Consecutivo del documento: {trazabilidad}")
    current_y -= 25

    # Bloque: DATOS GENERALES DE LA VERIFICACIÓN
    block_height_general = 6 * 15 + 25
    c.setFillColor(light_blue_color)
    c.rect(margin_left - 5, current_y - block_height_general + 5, width - margin_left * 2 + 10, block_height_general, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, current_y, "DATOS GENERALES DE LA VERIFICACIÓN")
    current_y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(margin_left + 5, current_y, f"Tipo de Verificación: {datos.get('Tipo de verificación', '')}")
    c.drawString(margin_left + 250, current_y, f"Cargo: {datos.get('Cargo', '')}")
    current_y -= 15
    c.drawString(margin_left + 5, current_y, f"Nombre del inspector: {datos.get('Funcionario', '')}")
    c.drawString(margin_left + 250, current_y, f"Fecha: {datos.get('Fecha', '')}")
    current_y -= 15
    c.drawString(margin_left + 5, current_y, f"Hora: {datos.get('Hora', '')}")
    c.drawString(margin_left + 250, current_y, f"Lugar: {datos.get('Lugar', '')}")
    current_y -= 25

    # Bloque: RUTA DE ALMACENAMIENTO
    c.setFillColor(light_blue_color)
    c.rect(margin_left - 5, current_y - 15, width - margin_left * 2 + 10, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, current_y, "RUTA DE ALMACENAMIENTO O NOMBRE DE LA(S) CARPETA(S) CONTENEDORA(S) DE LOS REGISTROS FOTOGRÁFICOS")
    current_y -= 25
    c.setFont("Helvetica", 10)
    if fotos:
        for i, foto in enumerate(fotos):
            file_name = getattr(foto, 'name', f'foto_{i+1}.jpg')
            c.drawString(margin_left + 5, current_y, f"• {file_name}")
            current_y -= 13
            if current_y < 120:
                c.showPage()
                current_y = height - 40
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 10)
    else:
        c.drawString(margin_left + 5, current_y, "No se adjuntaron registros fotográficos.")
        current_y -= 13
    current_y -= 10

    # Bloque: RESUMEN DE LA VERIFICACIÓN
    c.setFillColor(light_blue_color)
    c.rect(margin_left - 5, current_y - 15, width - margin_left * 2 + 10, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, current_y, "RESUMEN DE LA VERIFICACIÓN")
    current_y -= 25
    c.setFont("Helvetica", 10)

    # Preguntas y respuestas dinámicas
    for pregunta_def in TIPOS_PREGUNTAS[datos['Tipo de verificación']]:
        label = pregunta_def['label']
        valor = datos.get(label, "")

        if pregunta_def['type'] == 'radio':
            display_text = f"{label}: {marcar_opcion_pdf(valor, pregunta_def['options'])}"
        elif pregunta_def['type'] == 'checkboxes':
            options_selected = [s.strip() for s in valor.split(',')] if isinstance(valor, str) else []
            formatted_options = []
            for opt in pregunta_def['options']:
                formatted_options.append(f"{opt} {'☒' if opt in options_selected else '☐'}")
            display_text = f"{label}: {'   '.join(formatted_options)}"
        else:
            display_text = f"{label}: {valor}"

        c.drawString(margin_left + 5, current_y, display_text)
        current_y -= 13
        if current_y < 120:
            c.showPage()
            current_y = height - 40
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)

    # Pregunta fija: Observaciones, siempre después de Concepto de la verificación
    obs = datos.get("OBSERVACIONES Y/O NOVEDADES EVIDENCIADAS EN EL PROCESO DE VERIFICACIÓN", "")
    c.setFillColor(light_blue_color)
    c.rect(margin_left - 5, current_y - 15, width - margin_left * 2 + 10, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, current_y, "OBSERVACIONES Y/O NOVEDADES EVIDENCIADAS EN EL PROCESO DE VERIFICACIÓN")
    current_y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(margin_left + 5, current_y, obs if obs else "(No aplica)")
    current_y -= 20

    # Bloque: REGISTRO FOTOGRÁFICO
    if fotos:
        c.showPage()
        current_y = height - 40
        c.setFillColor(light_blue_color)
        c.rect(margin_left - 5, current_y - 15, width - margin_left * 2 + 10, 20, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_left, current_y, "REGISTRO FOTOGRÁFICO DE LA VERIFICACIÓN")
        current_y -= 30
        for i, foto in enumerate(fotos):
            try:
                img = Image.open(foto)
                img.thumbnail((350, 350))
                temp_path = f"imagenes/temp_{uuid.uuid4().hex}.jpg"
                os.makedirs("imagenes", exist_ok=True)
                img.save(temp_path)
                draw_width = 250
                draw_height = int((img.height / img.width) * draw_width)
                img_x = margin_left + ((width - margin_left*2) - draw_width) / 2
                if current_y - draw_height < 100:
                    c.showPage()
                    current_y = height - 40
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(margin_left, current_y, "REGISTRO FOTOGRÁFICO DE LA VERIFICACIÓN (Continuación)")
                    current_y -= 30
                c.drawImage(temp_path, img_x, current_y - draw_height - 10, width=draw_width, height=draw_height)
                current_y -= (draw_height + 20)
                os.remove(temp_path)
            except Exception as e:
                c.setFont("Helvetica", 10)
                c.drawString(margin_left + 5, current_y, f"[Error al cargar imagen {i+1}: {e}]")
                current_y -= 20

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

nombre_funcionario = st.text_input("Nombre del funcionario")
cargo_funcionario = st.text_input("Cargo del funcionario")
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

    # PREGUNTA FIJA: Observaciones
    datos["OBSERVACIONES Y/O NOVEDADES EVIDENCIADAS EN EL PROCESO DE VERIFICACIÓN"] = st.text_area(
        "OBSERVACIONES Y/O NOVEDADES EVIDENCIADAS EN EL PROCESO DE VERIFICACIÓN (si aplica)"
    )

    # Botón y uploader alineados horizontalmente
    col1, col2 = st.columns([1, 2])
    with col1:
        submit = st.form_submit_button("✅ Guardar y generar PDF")
    with col2:
        fotos = st.file_uploader(
            "Sube fotos de la verificación (opcional)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            label_visibility="visible"
        )

# ========== ENVÍO Y VALIDACIÓN ==========
if 'submit' in locals() and submit:
    campos_vacios = [campo for campo, valor in datos.items() if isinstance(valor, str) and not valor.strip() and campo != "OBSERVACIONES Y/O NOVEDADES EVIDENCIADAS EN EL PROCESO DE VERIFICACIÓN"]
    if campos_vacios:
        st.error(f"Faltan campos obligatorios: {', '.join(campos_vacios)}")
    else:
        sheet.append_row(list(datos.values()))
        nombre_pdf = generar_pdf(datos, fotos, trazabilidad)
        st.success("✅ Formulario guardado y PDF generado.")
        with open(nombre_pdf, "rb") as f:
            st.download_button("📄 Descargar PDF", f, file_name=nombre_pdf)
