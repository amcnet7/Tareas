import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

PDF_EXTRACT_AVAILABLE = True
try:
    from PyPDF2 import PdfReader
except ImportError:
    PDF_EXTRACT_AVAILABLE = False

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?")
AMOUNT_PATTERN = re.compile(r"\d{1,3}(?:,\d{3})*(?:\.\d{2})?")


def normalize_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def extract_values_from_xml(ruta_xml):
    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()
    except ET.ParseError:
        return None, None

    # Intentar obtener valores de atributos de la raíz
    fecha = root.attrib.get("Fecha") or root.attrib.get("fecha") or root.attrib.get("FechaEmision")
    importe = root.attrib.get("Total") or root.attrib.get("total") or root.attrib.get("Importe")

    if fecha and importe:
        return normalize_text(fecha), normalize_text(importe)

    # Buscar en el árbol etiquetas con nombre relacionado
    for elem in root.iter():
        tag = elem.tag.split("}")[-1].lower()
        text = normalize_text(elem.text)
        if not fecha and tag in ("fecha", "fechaemision", "fechaemision", "fechadeemision", "fecha_factura", "date"):
            if DATE_PATTERN.search(text):
                fecha = text
        if not importe and tag in ("total", "importe", "subtotal", "monto", "valor"):
            if AMOUNT_PATTERN.search(text):
                importe = AMOUNT_PATTERN.search(text).group(0)

    if fecha and importe:
        return normalize_text(fecha), normalize_text(importe)

    # Fallback a través del texto completo del archivo XML
    try:
        contenido = Path(ruta_xml).read_text(encoding="utf-8", errors="ignore")
        fecha_match = DATE_PATTERN.search(contenido)
        importe_match = AMOUNT_PATTERN.search(contenido)
        fecha = fecha or (fecha_match.group(0) if fecha_match else None)
        importe = importe or (importe_match.group(0) if importe_match else None)
    except Exception:
        pass

    return normalize_text(fecha), normalize_text(importe)


def extract_text_from_pdf(ruta_pdf):
    if not PDF_EXTRACT_AVAILABLE:
        return ""

    try:
        reader = PdfReader(ruta_pdf)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception:
        return ""


def buscar_rfc_en_archivos(ruta_carpeta, rfc):
    resultados = []
    valor_busqueda = rfc.strip().upper()

    for raiz, _, archivos in os.walk(ruta_carpeta):
        for archivo in archivos:
            nombre_archivo = archivo
            extension = archivo.lower().split('.')[-1]
            ruta_archivo = os.path.join(raiz, archivo)
            contenido = ""
            encontrado = False
            fecha = ""
            importe = ""

            if extension == "xml":
                try:
                    contenido = Path(ruta_archivo).read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                if valor_busqueda in contenido.upper():
                    encontrado = True
                    fecha, importe = extract_values_from_xml(ruta_archivo)

            elif extension == "pdf":
                contenido = extract_text_from_pdf(ruta_archivo)
                if contenido and valor_busqueda in contenido.upper():
                    encontrado = True
                    fecha_match = DATE_PATTERN.search(contenido)
                    amount_match = AMOUNT_PATTERN.search(contenido)
                    fecha = fecha_match.group(0) if fecha_match else ""
                    importe = amount_match.group(0) if amount_match else ""

            if encontrado:
                resultados.append({
                    "archivo": nombre_archivo,
                    "fecha_emision": fecha or "No disponible",
                    "importe": importe or "No disponible",
                    "ruta": ruta_archivo,
                })

    return resultados


@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    mensaje = None
    carpeta = ""
    rfc = ""
    error = None

    if request.method == "POST":
        carpeta = request.form.get("carpeta", "").strip()
        rfc = request.form.get("rfc", "").strip()

        if not carpeta or not rfc:
            error = "Debe ingresar la ruta de la carpeta y el RFC a buscar."
        elif not os.path.isdir(carpeta):
            error = "La ruta ingresada no existe o no es una carpeta válida."
        else:
            resultados = buscar_rfc_en_archivos(carpeta, rfc)
            if not resultados:
                mensaje = f"No se encontró el RFC '{rfc}' en los archivos de la carpeta." 

    return render_template(
        "index.html",
        carpeta=carpeta,
        rfc=rfc,
        resultados=resultados,
        error=error,
        mensaje=mensaje,
        pdf_support=PDF_EXTRACT_AVAILABLE,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
