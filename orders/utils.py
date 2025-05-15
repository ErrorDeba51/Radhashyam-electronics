# orders/utils.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_invoice_pdf(order):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Invoice #RS{order.id}", styles['Title']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        f"Customer: {order.user.get_full_name()}<br/>"
        f"Address: {order.address}<br/>"
        f"Pincode: {order.pincode}",
        styles['Normal']
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
