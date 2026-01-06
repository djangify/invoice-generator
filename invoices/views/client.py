from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from invoices.models import (
    Client,
    Invoice,
    InvoiceYear,
)
from invoices.forms import (
    ClientForm,
)
from .utils import get_active_year


# Client views
@login_required
def client_list(request):
    clients = Client.objects.all()
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    context = {
        "clients": clients,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/client_list.html", context)


@login_required
def client_create(request):
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Client created successfully.")
            return redirect("invoices:client_list")
    else:
        form = ClientForm()

    context = {
        "form": form,
        "action": "Add",
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/client_form.html", context)


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated successfully.")
            return redirect("invoices:client_list")
    else:
        form = ClientForm(instance=client)

    context = {
        "form": form,
        "action": "Edit",
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/client_form.html", context)


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        client.delete()
        messages.success(request, "Client deleted successfully.")
        return redirect("invoices:client_list")

    context = {
        "client": client,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/client_confirm_delete.html", context)


@login_required
def client_invoices(request, pk):
    """View all invoices for a specific client"""
    client = get_object_or_404(Client, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    # Get all invoices for this client, optionally filtered by year
    invoices = Invoice.objects.filter(client=client)

    # Optional year filter
    year_filter = request.GET.get("year")
    if year_filter == "all":
        pass  # Show all years
    elif year_filter:
        try:
            filter_year = InvoiceYear.objects.get(id=year_filter)
            invoices = invoices.filter(tax_year=filter_year)
        except InvoiceYear.DoesNotExist:
            pass
    else:
        # Default to active year
        invoices = invoices.filter(tax_year=active_year)

    # Calculate totals
    total_invoiced = sum(inv.total() for inv in invoices)
    total_paid = sum(inv.total() for inv in invoices.filter(status="paid"))
    total_outstanding = sum(inv.total() for inv in invoices.exclude(status="paid"))

    context = {
        "client": client,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "active_year": active_year,
        "all_years": all_years,
        "year_filter": year_filter,
    }
    return render(request, "invoices/client_invoices.html", context)


@login_required
def client_invoices_pdf(request, pk):
    """Generate PDF of client invoice history"""
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
    )
    from io import BytesIO

    client = get_object_or_404(Client, pk=pk)
    active_year = get_active_year(request)

    # Get invoices (same logic as view)
    invoices = Invoice.objects.filter(client=client)
    year_filter = request.GET.get("year")
    filter_label = "All Years"

    if year_filter == "all":
        filter_label = "All Years"
    elif year_filter:
        try:
            filter_year = InvoiceYear.objects.get(id=year_filter)
            invoices = invoices.filter(tax_year=filter_year)
            filter_label = f"Tax Year {filter_year.year_label}"
        except InvoiceYear.DoesNotExist:
            pass
    else:
        invoices = invoices.filter(tax_year=active_year)
        filter_label = f"Tax Year {active_year.year_label}"

    # Calculate totals
    total_invoiced = sum(inv.total() for inv in invoices)
    total_paid = sum(inv.total() for inv in invoices.filter(status="paid"))
    total_outstanding = sum(inv.total() for inv in invoices.exclude(status="paid"))

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=20,
        fontName="Helvetica",
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#6B7280"),
        fontName="Helvetica",
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#111827"),
        fontName="Helvetica",
    )

    # Header
    elements.append(Paragraph(f"Invoice History: {client.name}", title_style))
    elements.append(Paragraph(filter_label, subtitle_style))

    # Summary
    summary_data = [
        ["Total Invoiced", "Total Paid", "Outstanding"],
        [f"£{total_invoiced:.2f}", f"£{total_paid:.2f}", f"£{total_outstanding:.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F9FAFB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#6B7280")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 14),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#E5E7EB")),
                ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#E5E7EB")),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Invoice table
    if invoices:
        inv_data = [
            [
                Paragraph("<b>INVOICE #</b>", heading_style),
                Paragraph("<b>DATE</b>", heading_style),
                Paragraph("<b>DUE DATE</b>", heading_style),
                Paragraph("<b>TOTAL</b>", heading_style),
                Paragraph("<b>STATUS</b>", heading_style),
            ]
        ]

        for inv in invoices:
            inv_data.append(
                [
                    Paragraph(inv.invoice_number, normal_style),
                    Paragraph(inv.date.strftime("%d %b %Y"), normal_style),
                    Paragraph(inv.due_date.strftime("%d %b %Y"), normal_style),
                    Paragraph(f"£{inv.total():.2f}", normal_style),
                    Paragraph(inv.get_status_display(), normal_style),
                ]
            )

        inv_table = Table(
            inv_data,
            colWidths=[1.4 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1 * inch],
        )
        inv_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F9FAFB")),
                    ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#E5E7EB")),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#E5E7EB")),
                    ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#E5E7EB")),
                ]
            )
        )
        elements.append(inv_table)
    else:
        elements.append(Paragraph("No invoices found.", normal_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{client.name.replace(" ", "_")}_invoices.pdf"'
    )
    return response
