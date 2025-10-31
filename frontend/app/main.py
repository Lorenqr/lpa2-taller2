from flask import Flask, render_template, request, abort, send_file
import requests
import os
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

app = Flask(__name__)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generar-pdf", methods=["POST"])
def generar_pdf():
    try:
        id_factura = request.form["id_factura"]
        response = requests.get(f"{BACKEND_URL}/facturas/v1/{id_factura}")

        if response.status_code != 200:
            abort(404, description="Factura no encontrada")

        factura = response.json()

        # Crear buffer y doc para la creación del PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Adicionar el Título y ID
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=30
        )
        elements.append(Paragraph(f"Factura #{id_factura}", title_style))
        elements.append(Spacer(1, 12))

        # Agregar Información de la Empresa
        elements.append(Paragraph("INFORMACIÓN DE LA EMPRESA", styles["Heading2"]))
        empresa_info = [
            ["Nombre:", factura["empresa"]["nombre"]],
            ["NIT:", factura["empresa"]["nit"]],
            ["Dirección:", factura["empresa"]["direccion"]],
            ["Teléfono:", factura["empresa"]["telefono"]],
        ]
        empresa_table = Table(empresa_info, colWidths=[2 * inch, 4 * inch])
        empresa_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ]
            )
        )
        elements.append(empresa_table)
        elements.append(Spacer(1, 20))

        # Agregar Información del Cliente
        elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", styles["Heading2"]))
        cliente_info = [
            ["Nombre:", factura["cliente"]["nombre"]],
            ["Documento:", factura["cliente"]["documento"]],
            ["Dirección:", factura["cliente"]["direccion"]],
            ["Teléfono:", factura["cliente"]["telefono"]],
        ]
        cliente_table = Table(cliente_info, colWidths=[2 * inch, 4 * inch])
        cliente_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ]
            )
        )
        elements.append(cliente_table)
        elements.append(Spacer(1, 20))

        # Adicionar el Detalle de la Factura
        elements.append(Paragraph("DETALLE DE LA FACTURA", styles["Heading2"]))
        detalle_header = ["Cantidad", "Descripción", "Precio Unit.", "Total"]
        detalle_data = [detalle_header]

        for item in factura["items"]:
            detalle_data.append(
                [
                    str(item["cantidad"]),
                    item["descripcion"],
                    f"${item['precio_unitario']:,.2f}",
                    f"${item['cantidad'] * item['precio_unitario']:,.2f}",
                ]
            )

        detalle_table = Table(
            detalle_data, colWidths=[1.2 * inch, 3 * inch, 1.4 * inch, 1.4 * inch]
        )
        detalle_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(detalle_table)
        elements.append(Spacer(1, 20))

        # Adicionar Subtotal, impuesto y Total
        subtotal = sum(
            item["cantidad"] * item["precio_unitario"] for item in factura["items"]
        )
        iva = subtotal * 0.19  # 19% de IVA
        total = subtotal + iva

        totales_data = [
            ["Subtotal:", f"${subtotal:,.2f}"],
            ["IVA (19%):", f"${iva:,.2f}"],
            ["Total:", f"${total:,.2f}"],
        ]

        totales_table = Table(totales_data, colWidths=[2 * inch, 2 * inch])
        totales_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.grey),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.whitesmoke),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(totales_table)

        # Generar el doc y limpiar el buffer
        doc.build(elements)
        buffer.seek(0)

        # Retornar el PDF para visualizar y descargar
        return send_file(
            buffer,
            download_name=f"factura_{id_factura}.pdf",
            mimetype="application/pdf",
            as_attachment=True,
        )

    except requests.exceptions.ConnectionError:
        abort(503, description="Error de conexión con el servidor")
    except Exception as e:
        abort(500, description=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
