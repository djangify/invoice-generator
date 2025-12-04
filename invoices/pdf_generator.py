from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)

from io import BytesIO
from django.conf import settings
import os
from .models import CompanySettings


class InvoicePDF:
    def __init__(self, invoice):
        self.invoice = invoice
        self.buffer = BytesIO()
        self.width, self.height = A4

    def generate(self):
        """Generate the PDF and return the buffer"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Container for the 'Flowable' objects
        elements = []

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles for minimalist look
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#111827"),
            spaceAfter=30,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=10,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=6,
            fontName="Helvetica",
            textTransform="uppercase",
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#111827"),
            fontName="Helvetica",
        )

        small_style = ParagraphStyle(
            "SmallText",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#6B7280"),
            fontName="Helvetica",
        )

        # Get company settings
        company = CompanySettings.objects.first()

        # Company logo (if exists)
        if company and company.logo:
            try:
                logo_path = os.path.join(settings.MEDIA_ROOT, str(company.logo))
                if os.path.exists(logo_path):
                    # Create image with max width, maintaining aspect ratio
                    img = Image(logo_path)
                    img.drawHeight = 0.75 * inch
                    img.drawWidth = 0.75 * inch * img.imageWidth / img.imageHeight

                    # Cap the width at 2 inches max
                    if img.drawWidth > 2 * inch:
                        img.drawWidth = 2 * inch
                        img.drawHeight = 2 * inch * img.imageHeight / img.imageWidth

                    elements.append(img)
                    elements.append(Spacer(1, 0.3 * inch))
            except Exception:
                pass

        # Invoice title
        elements.append(Paragraph("INVOICE", title_style))

        # Company info
        company_info = []
        if company:
            company_info.append(
                Paragraph(f"<b>{company.company_name}</b>", normal_style)
            )
            company_info.append(Paragraph(company.address_line1, normal_style))
            if company.address_line2:
                company_info.append(Paragraph(company.address_line2, normal_style))
            company_info.append(
                Paragraph(f"{company.city}, {company.postcode}", normal_style)
            )
            if company.phone:
                company_info.append(Paragraph(f"Tel: {company.phone}", normal_style))
            company_info.append(Paragraph(company.email, normal_style))
            if company.vat_number:
                company_info.append(
                    Paragraph(f"VAT: {company.vat_number}", normal_style)
                )

        # Client info
        client_info = []
        client_info.append(Paragraph("BILL TO", heading_style))
        client_info.append(
            Paragraph(f"<b>{self.invoice.client.name}</b>", normal_style)
        )
        client_info.append(Paragraph(self.invoice.client.address_line1, normal_style))
        if self.invoice.client.address_line2:
            client_info.append(
                Paragraph(self.invoice.client.address_line2, normal_style)
            )
        client_info.append(
            Paragraph(
                f"{self.invoice.client.city}, {self.invoice.client.postcode}",
                normal_style,
            )
        )
        if self.invoice.client.vat_number:
            client_info.append(
                Paragraph(f"VAT: {self.invoice.client.vat_number}", normal_style)
            )

        # Create header table
        header_table = Table(
            [[company_info, client_info]], colWidths=[3.25 * inch, 3.25 * inch]
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(header_table)
        elements.append(Spacer(1, 0.4 * inch))

        # Invoice details
        invoice_details_data = [
            [
                Paragraph("Invoice Number:", normal_style),
                Paragraph(f"<b>{self.invoice.invoice_number}</b>", normal_style),
            ],
            [
                Paragraph("Invoice Date:", normal_style),
                Paragraph(self.invoice.date.strftime("%d %B %Y"), normal_style),
            ],
            [
                Paragraph("Due Date:", normal_style),
                Paragraph(self.invoice.due_date.strftime("%d %B %Y"), normal_style),
            ],
            [
                Paragraph("Status:", normal_style),
                Paragraph(
                    f"<b>{self.invoice.get_status_display().upper()}</b>", normal_style
                ),
            ],
        ]

        details_table = Table(invoice_details_data, colWidths=[1.5 * inch, 2 * inch])
        details_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elements.append(details_table)
        elements.append(Spacer(1, 0.4 * inch))

        # Invoice items table
        items_data = [
            [
                Paragraph("<b>DESCRIPTION</b>", heading_style),
                Paragraph("<b>QTY</b>", heading_style),
                Paragraph("<b>RATE</b>", heading_style),
                Paragraph("<b>VAT</b>", heading_style),
                Paragraph("<b>AMOUNT</b>", heading_style),
            ]
        ]

        for item in self.invoice.items.all():
            items_data.append(
                [
                    Paragraph(item.description, normal_style),
                    Paragraph(str(item.quantity), normal_style),
                    Paragraph(f"£{item.rate:.2f}", normal_style),
                    Paragraph(f"{item.vat_rate}%", normal_style),
                    Paragraph(f"£{item.line_total():.2f}", normal_style),
                ]
            )

        items_table = Table(
            items_data,
            colWidths=[3 * inch, 0.75 * inch, 1 * inch, 0.75 * inch, 1 * inch],
        )

        items_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F9FAFB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#6B7280")),
                    ("ALIGN", (1, 0), (-1, 0), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    # Data rows
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 1), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
                    # Lines
                    ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#E5E7EB")),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#E5E7EB")),
                    ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#E5E7EB")),
                ]
            )
        )

        elements.append(items_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Totals table (right-aligned)
        totals_data = [
            [
                Paragraph("Subtotal:", normal_style),
                Paragraph(f"£{self.invoice.subtotal():.2f}", normal_style),
            ],
            [
                Paragraph("VAT:", normal_style),
                Paragraph(f"£{self.invoice.vat_total():.2f}", normal_style),
            ],
            [
                Paragraph(
                    "<b>TOTAL:</b>",
                    ParagraphStyle(
                        "BoldTotal",
                        parent=normal_style,
                        fontName="Helvetica-Bold",
                        fontSize=14,
                    ),
                ),
                Paragraph(
                    f"<b>£{self.invoice.total():.2f}</b>",
                    ParagraphStyle(
                        "BoldTotal",
                        parent=normal_style,
                        fontName="Helvetica-Bold",
                        fontSize=14,
                    ),
                ),
            ],
        ]

        totals_table = Table(totals_data, colWidths=[1.5 * inch, 1.5 * inch])
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (1, 1), 6),
                    ("TOPPADDING", (0, 2), (1, 2), 12),
                    ("LINEABOVE", (0, 2), (-1, 2), 1, colors.HexColor("#E5E7EB")),
                ]
            )
        )

        # Wrap totals in a table to right-align it
        totals_wrapper = Table([[totals_table]], colWidths=[6.5 * inch])
        totals_wrapper.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(totals_wrapper)

        # Payment Information Section
        payment_link = self.invoice.get_payment_link()
        payment_terms = self.invoice.get_payment_terms()

        if (
            payment_link
            or payment_terms
            or (company and (company.bank_name or company.account_number))
        ):
            elements.append(Spacer(1, 0.4 * inch))
            elements.append(Paragraph("PAYMENT INFORMATION", heading_style))
            elements.append(Spacer(1, 0.1 * inch))

            # Payment link (Stripe/PayPal)
            if payment_link:
                payment_text = f'<b>Pay Online:</b> <link href="{payment_link}" color="blue">{payment_link}</link>'
                elements.append(Paragraph(payment_text, small_style))
                elements.append(Spacer(1, 0.1 * inch))

            # Bank details
            if company and company.bank_name:
                elements.append(Paragraph("<b>Bank Transfer Details:</b>", small_style))
                elements.append(Spacer(1, 0.05 * inch))

                bank_details = []
                if company.bank_name:
                    bank_details.append(f"Bank: {company.bank_name}")
                if company.account_name:
                    bank_details.append(f"Account Name: {company.account_name}")
                if company.account_number:
                    bank_details.append(f"Account Number: {company.account_number}")
                if company.sort_code:
                    bank_details.append(f"Sort Code: {company.sort_code}")
                if company.iban:
                    bank_details.append(f"IBAN: {company.iban}")
                if company.swift_bic:
                    bank_details.append(f"SWIFT/BIC: {company.swift_bic}")

                for detail in bank_details:
                    elements.append(Paragraph(detail, small_style))

                elements.append(Spacer(1, 0.1 * inch))

            # Payment terms
            if payment_terms:
                elements.append(Paragraph("<b>Payment Terms:</b>", small_style))
                elements.append(Spacer(1, 0.05 * inch))
                elements.append(
                    Paragraph(payment_terms.replace("\n", "<br/>"), small_style)
                )

        # Notes (only if they exist and are not empty)
        if self.invoice.notes and self.invoice.notes.strip():
            elements.append(Spacer(1, 0.4 * inch))
            elements.append(Paragraph("NOTES", heading_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(
                Paragraph(self.invoice.notes.replace("\n", "<br/>"), small_style)
            )

        # Custom footer
        if company and company.invoice_footer:
            elements.append(Spacer(1, 0.4 * inch))
            footer_style = ParagraphStyle(
                "Footer",
                parent=small_style,
                alignment=1,  # Center alignment
                textColor=colors.HexColor("#9CA3AF"),
            )
            elements.append(
                Paragraph(company.invoice_footer.replace("\n", "<br/>"), footer_style)
            )

        # Build PDF
        doc.build(elements)

        # Get the value of the BytesIO buffer and return it
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf
