from flask import Flask, render_template, request, abort, send_file
import requests
import os
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

app = Flask(__name__)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generar-pdf", methods=["POST"])
def generar_pdf():
    try:
        id_factura = request.form.get("id_factura")
        if not id_factura:
            abort(400, description="Falta id_factura en el formulario")

        resp = requests.get(f"{BACKEND_URL}/facturas/v1/{id_factura}")
        if resp.status_code != 200:
            abort(resp.status_code)

        factura = resp.json()

        # Normalizar detalle: backend puede usar 'detalle' o 'items'
        detalle = factura.get("detalle") or factura.get("items") or []

        # Preparar buffer y documento con título personalizado
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            title=f"Factura #{id_factura}",
            author=factura.get("empresa", {}).get("nombre", ""),
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        styles = getSampleStyleSheet()
        elements = []

        # Encabezado: Título y Fecha
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        elements.append(Paragraph(f"FACTURA #{id_factura}", title_style))

        fecha_style = ParagraphStyle(
            "FechaStyle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#7F8C8D"),
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        fecha_emision = factura.get("fecha_emision", "-")
        elements.append(Paragraph(f"Fecha de emisión: {fecha_emision}", fecha_style))
        elements.append(Spacer(1, 20))

        # Estilos para secciones
        section_style = ParagraphStyle(
            "SectionStyle",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.white,
            backColor=colors.HexColor("#3498DB"),
            spaceAfter=10,
            spaceBefore=10,
            leftIndent=10,
            fontName="Helvetica-Bold",
        )

        # Empresa
        elements.append(Paragraph("INFORMACIÓN DE LA EMPRESA", section_style))
        empresa = factura.get("empresa") or {}
        empresa_rows = [
            ["Nombre:", empresa.get("nombre", "-")],
            ["NIT:", empresa.get("nit", "-")],
            ["Dirección:", empresa.get("direccion", "-")],
            ["Teléfono:", empresa.get("telefono", "-")],
            ["Email:", empresa.get("email", "-")],
        ]
        empresa_table = Table(empresa_rows, colWidths=[1.5 * inch, 4.5 * inch])
        empresa_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2C3E50")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(empresa_table)
        elements.append(Spacer(1, 20))

        # Cliente
        elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", section_style))
        cliente = factura.get("cliente") or {}
        cliente_rows = [
            ["Nombre:", cliente.get("nombre", "-")],
            ["Documento:", cliente.get("documento", cliente.get("dni", "-"))],
            ["Dirección:", cliente.get("direccion", "-")],
            ["Teléfono:", cliente.get("telefono", "-")],
        ]
        cliente_table = Table(cliente_rows, colWidths=[1.5 * inch, 4.5 * inch])
        cliente_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2C3E50")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(cliente_table)
        elements.append(Spacer(1, 20))

        # Detalle con estilo mejorado
        detalle_section_style = ParagraphStyle(
            "DetalleSection",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=10,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )
        elements.append(Paragraph("DETALLE DE LA FACTURA", detalle_section_style))

        header = ["Cantidad", "Descripción", "Precio Unit.", "Total"]
        data = [header]
        for it in detalle:
            if isinstance(it, dict):
                qty = it.get("cantidad", it.get("qty", 1))
                desc = it.get("descripcion", it.get("descripcion_item", "-"))
                price = it.get("precio_unitario", it.get("precio", 0.0))
            else:
                qty = 1
                desc = str(it)
                price = 0.0
            line_total = round(qty * price, 2)
            data.append([str(qty), desc, f"${price:,.2f}", f"${line_total:,.2f}"])

        detalle_table = Table(
            data, colWidths=[1.2 * inch, 3 * inch, 1.4 * inch, 1.4 * inch]
        )
        detalle_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(detalle_table)
        elements.append(Spacer(1, 20))

        # Totales con mejor diseño
        subtotal = factura.get("subtotal")
        impuesto = factura.get("impuesto")
        total = factura.get("total")

        if subtotal is None:
            subtotal = sum(
                (
                    it.get("cantidad", it.get("qty", 0))
                    * it.get("precio_unitario", it.get("precio", 0.0))
                )
                for it in detalle
                if isinstance(it, dict)
            )
        if impuesto is None:
            impuesto = round(subtotal * (factura.get("tax_rate") or 0.21), 2)
        if total is None:
            total = round(subtotal + impuesto, 2)

        totales_data = [
            ["Subtotal:", f"${subtotal:,.2f}"],
            ["IVA (19%):", f"${impuesto:,.2f}"],
            ["Total:", f"${total:,.2f}"],
        ]

        totales_table = Table(totales_data, colWidths=[2 * inch, 2 * inch])
        totales_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#3498DB")),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.whitesmoke),
                    ("FONTSIZE", (0, -1), (-1, -1), 13),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(totales_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            download_name=f"factura_{id_factura}.pdf",
            mimetype="application/pdf",
            as_attachment=True,
        )

    except requests.exceptions.ConnectionError:
        abort(503, description="No se pudo conectar con backend")
    except Exception as e:
        abort(500, description=str(e))


@app.route("/vista-previa-pdf", methods=["POST"])
def vista_previa_pdf():
    """
    Genera el PDF para vista previa (sin descarga automática)
    """
    try:
        id_factura = request.form.get("id_factura")
        if not id_factura:
            abort(400, description="Falta id_factura en el formulario")

        resp = requests.get(f"{BACKEND_URL}/facturas/v1/{id_factura}")
        if resp.status_code != 200:
            abort(resp.status_code)

        factura = resp.json()

        # Normalizar detalle: backend puede usar 'detalle' o 'items'
        detalle = factura.get("detalle") or factura.get("items") or []

        # Preparar buffer y documento con título personalizado
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            title=f"Factura #{id_factura}",
            author=factura.get("empresa", {}).get("nombre", ""),
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        styles = getSampleStyleSheet()
        elements = []

        # Encabezado: Título y Fecha
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        elements.append(Paragraph(f"FACTURA #{id_factura}", title_style))

        fecha_style = ParagraphStyle(
            "FechaStyle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#7F8C8D"),
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        fecha_emision = factura.get("fecha_emision", "-")
        elements.append(Paragraph(f"Fecha de emisión: {fecha_emision}", fecha_style))
        elements.append(Spacer(1, 20))

        # Estilos para secciones
        section_style = ParagraphStyle(
            "SectionStyle",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.white,
            backColor=colors.HexColor("#3498DB"),
            spaceAfter=10,
            spaceBefore=10,
            leftIndent=10,
            fontName="Helvetica-Bold",
        )

        # Empresa
        elements.append(Paragraph("INFORMACIÓN DE LA EMPRESA", section_style))
        empresa = factura.get("empresa") or {}
        empresa_rows = [
            ["Nombre:", empresa.get("nombre", "-")],
            ["NIT:", empresa.get("nit", "-")],
            ["Dirección:", empresa.get("direccion", "-")],
            ["Teléfono:", empresa.get("telefono", "-")],
            ["Email:", empresa.get("email", "-")],
        ]
        empresa_table = Table(empresa_rows, colWidths=[1.5 * inch, 4.5 * inch])
        empresa_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2C3E50")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(empresa_table)
        elements.append(Spacer(1, 20))

        # Cliente
        elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", section_style))
        cliente = factura.get("cliente") or {}
        cliente_rows = [
            ["Nombre:", cliente.get("nombre", "-")],
            ["Documento:", cliente.get("documento", cliente.get("dni", "-"))],
            ["Dirección:", cliente.get("direccion", "-")],
            ["Teléfono:", cliente.get("telefono", "-")],
        ]
        cliente_table = Table(cliente_rows, colWidths=[1.5 * inch, 4.5 * inch])
        cliente_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2C3E50")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(cliente_table)
        elements.append(Spacer(1, 20))

        # Detalle con estilo mejorado
        detalle_section_style = ParagraphStyle(
            "DetalleSection",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=10,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )
        elements.append(Paragraph("DETALLE DE LA FACTURA", detalle_section_style))

        header = ["Cantidad", "Descripción", "Precio Unit.", "Total"]
        data = [header]
        for it in detalle:
            if isinstance(it, dict):
                qty = it.get("cantidad", it.get("qty", 1))
                desc = it.get("descripcion", it.get("descripcion_item", "-"))
                price = it.get("precio_unitario", it.get("precio", 0.0))
            else:
                qty = 1
                desc = str(it)
                price = 0.0
            line_total = round(qty * price, 2)
            data.append([str(qty), desc, f"${price:,.2f}", f"${line_total:,.2f}"])

        detalle_table = Table(
            data, colWidths=[1.2 * inch, 3 * inch, 1.4 * inch, 1.4 * inch]
        )
        detalle_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(detalle_table)
        elements.append(Spacer(1, 20))

        # Totales con mejor diseño
        subtotal = factura.get("subtotal")
        impuesto = factura.get("impuesto")
        total = factura.get("total")

        if subtotal is None:
            subtotal = sum(
                (
                    it.get("cantidad", it.get("qty", 0))
                    * it.get("precio_unitario", it.get("precio", 0.0))
                )
                for it in detalle
                if isinstance(it, dict)
            )
        if impuesto is None:
            impuesto = round(subtotal * (factura.get("tax_rate") or 0.19), 2)
        if total is None:
            total = round(subtotal + impuesto, 2)

        totales_data = [
            ["Subtotal:", f"${subtotal:,.2f}"],
            ["IVA (19%):", f"${impuesto:,.2f}"],
            ["Total:", f"${total:,.2f}"],
        ]

        totales_table = Table(totales_data, colWidths=[2 * inch, 2 * inch])
        totales_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#3498DB")),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.whitesmoke),
                    ("FONTSIZE", (0, -1), (-1, -1), 13),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(totales_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Enviar sin forzar descarga (as_attachment=False)
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"factura_{id_factura}.pdf",
        )

    except requests.exceptions.ConnectionError:
        abort(503, description="No se pudo conectar con backend")
    except Exception as e:
        abort(500, description=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
