from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models import (
    Client,
    Invoice,
    InvoiceItem,
    CompanySettings,
    RecurringInvoice,
    InvoiceYear,
)
from .forms import (
    ClientForm,
    InvoiceForm,
    InvoiceItemFormSet,
    CompanySettingsForm,
    RecurringInvoiceForm,
    RecurringInvoiceItemFormSet,
)
from .pdf_generator import InvoicePDF


def get_active_year(request):
    """Get active year from session or default"""
    year_id = request.session.get("active_year_id")
    if year_id:
        try:
            return InvoiceYear.objects.get(id=year_id)
        except InvoiceYear.DoesNotExist:
            pass
    return InvoiceYear.get_active_year()


def switch_year(request, year_id):
    """Switch the active year for the session"""
    year = get_object_or_404(InvoiceYear, id=year_id)
    request.session["active_year_id"] = year.id
    messages.success(request, f"Switched to tax year {year.year_label}")
    return redirect("invoices:dashboard")


def dashboard(request):
    """Main dashboard view"""
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    # Filter invoices by active year
    year_invoices = Invoice.objects.filter(tax_year=active_year)

    total_clients = Client.objects.count()
    total_invoices = year_invoices.count()
    draft_invoices = year_invoices.filter(status="draft").count()
    unpaid_invoices = year_invoices.filter(status__in=["sent", "overdue"]).count()

    # Calculate total revenue for the year
    total_revenue = sum(
        invoice.total() for invoice in year_invoices.filter(status="paid")
    )

    recent_invoices = year_invoices[:5]

    context = {
        "active_year": active_year,
        "all_years": all_years,
        "total_clients": total_clients,
        "total_invoices": total_invoices,
        "draft_invoices": draft_invoices,
        "unpaid_invoices": unpaid_invoices,
        "total_revenue": total_revenue,
        "recent_invoices": recent_invoices,
    }
    return render(request, "invoices/dashboard.html", context)


# Client views
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


# Invoice views
def invoice_list(request):
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    invoices = Invoice.objects.filter(tax_year=active_year)
    status_filter = request.GET.get("status")
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    context = {
        "invoices": invoices,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/invoice_list.html", context)


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    context = {
        "invoice": invoice,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/invoice_detail.html", context)


def invoice_create(request):
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.instance = invoice
            formset.save()
            messages.success(
                request, f"Invoice {invoice.invoice_number} created successfully."
            )
            return redirect("invoices:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()

    context = {
        "form": form,
        "formset": formset,
        "action": "Create",
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/invoice_form.html", context)


def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(
                request, f"Invoice {invoice.invoice_number} updated successfully."
            )
            return redirect("invoices:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)

    context = {
        "form": form,
        "formset": formset,
        "action": "Edit",
        "invoice": invoice,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/invoice_form.html", context)


def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f"Invoice {invoice_number} deleted successfully.")
        return redirect("invoices:invoice_list")

    context = {
        "invoice": invoice,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/invoice_confirm_delete.html", context)


def invoice_pdf(request, pk):
    """Generate and download invoice PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Generate PDF
    pdf_generator = InvoicePDF(invoice)
    pdf = pdf_generator.generate()

    # Create the HttpResponse object with PDF header
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{invoice.invoice_number}.pdf"'
    )

    return response


def invoice_regenerate_pdf(request, pk):
    """Regenerate and save invoice PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)

    try:
        invoice.generate_and_save_pdf()
        messages.success(
            request, f"PDF for {invoice.invoice_number} regenerated successfully."
        )
    except Exception as e:
        messages.error(request, f"Error regenerating PDF: {str(e)}")

    return redirect("invoices:invoice_detail", pk=pk)


def invoice_mark_paid(request, pk):
    """Quick action to mark invoice as paid"""
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.status = "paid"
    invoice.save()
    messages.success(request, f"Invoice {invoice.invoice_number} marked as paid.")

    # Return to the referring page or invoice detail
    referer = request.META.get("HTTP_REFERER")
    if referer and "invoice_list" in referer:
        return redirect("invoices:invoice_list")
    return redirect("invoices:invoice_detail", pk=pk)


def invoice_mark_sent(request, pk):
    """Quick action to mark invoice as sent"""
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.status = "sent"
    invoice.save()
    messages.success(request, f"Invoice {invoice.invoice_number} marked as sent.")

    referer = request.META.get("HTTP_REFERER")
    if referer and "invoice_list" in referer:
        return redirect("invoices:invoice_list")
    return redirect("invoices:invoice_detail", pk=pk)


def invoice_duplicate(request, pk):
    """Duplicate an existing invoice"""
    original = get_object_or_404(Invoice, pk=pk)

    # Create new invoice with copied data
    new_invoice = Invoice.objects.create(
        client=original.client,
        date=timezone.now().date(),
        due_date=timezone.now().date() + timezone.timedelta(days=30),
        status="draft",
        notes=original.notes,
        payment_terms=original.payment_terms,
        payment_link=original.payment_link,
    )

    # Copy all items
    for item in original.items.all():
        InvoiceItem.objects.create(
            invoice=new_invoice,
            description=item.description,
            quantity=item.quantity,
            rate=item.rate,
            vat_rate=item.vat_rate,
        )

    messages.success(
        request,
        f"Invoice duplicated. New invoice {new_invoice.invoice_number} created as draft.",
    )
    return redirect("invoices:invoice_edit", pk=new_invoice.pk)


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


# Recurring Invoice views
def recurring_invoice_list(request):
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    recurring_invoices = RecurringInvoice.objects.all()
    status_filter = request.GET.get("status")
    if status_filter:
        recurring_invoices = recurring_invoices.filter(status=status_filter)

    context = {
        "recurring_invoices": recurring_invoices,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/recurring_invoice_list.html", context)


def recurring_invoice_detail(request, pk):
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    # Get invoices generated from this recurring invoice
    generated_invoices = recurring_invoice.generated_invoices.all()[:10]

    context = {
        "recurring_invoice": recurring_invoice,
        "generated_invoices": generated_invoices,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/recurring_invoice_detail.html", context)


def recurring_invoice_create(request):
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        form = RecurringInvoiceForm(request.POST)
        formset = RecurringInvoiceItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            recurring_invoice = form.save()
            formset.instance = recurring_invoice
            formset.save()
            messages.success(
                request,
                f"Recurring invoice for {recurring_invoice.client.name} created successfully.",
            )
            return redirect(
                "invoices:recurring_invoice_detail", pk=recurring_invoice.pk
            )
    else:
        form = RecurringInvoiceForm()
        formset = RecurringInvoiceItemFormSet()

    context = {
        "form": form,
        "formset": formset,
        "action": "Create",
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/recurring_invoice_form.html", context)


def recurring_invoice_edit(request, pk):
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        form = RecurringInvoiceForm(request.POST, instance=recurring_invoice)
        formset = RecurringInvoiceItemFormSet(request.POST, instance=recurring_invoice)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(
                request,
                f"Recurring invoice for {recurring_invoice.client.name} updated successfully.",
            )
            return redirect(
                "invoices:recurring_invoice_detail", pk=recurring_invoice.pk
            )
    else:
        form = RecurringInvoiceForm(instance=recurring_invoice)
        formset = RecurringInvoiceItemFormSet(instance=recurring_invoice)

    context = {
        "form": form,
        "formset": formset,
        "action": "Edit",
        "recurring_invoice": recurring_invoice,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/recurring_invoice_form.html", context)


def recurring_invoice_delete(request, pk):
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=pk)
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        client_name = recurring_invoice.client.name
        recurring_invoice.delete()
        messages.success(
            request, f"Recurring invoice for {client_name} deleted successfully."
        )
        return redirect("invoices:recurring_invoice_list")

    context = {
        "recurring_invoice": recurring_invoice,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/recurring_invoice_confirm_delete.html", context)


def recurring_invoice_generate(request, pk):
    """Manually generate an invoice from a recurring template"""
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=pk)

    try:
        invoice = recurring_invoice.generate_invoice()
        if invoice:
            messages.success(
                request, f"Invoice {invoice.invoice_number} generated successfully."
            )
            return redirect("invoices:invoice_detail", pk=invoice.pk)
        else:
            messages.warning(
                request,
                "Invoice could not be generated. Check the recurring invoice status and dates.",
            )
            return redirect("invoices:recurring_invoice_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"Error generating invoice: {str(e)}")
        return redirect("invoices:recurring_invoice_detail", pk=pk)


def recurring_invoice_pause(request, pk):
    """Pause a recurring invoice"""
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=pk)
    recurring_invoice.status = "paused"
    recurring_invoice.save()
    messages.success(
        request,
        f"Recurring invoice for {recurring_invoice.client.name} has been paused.",
    )
    return redirect("invoices:recurring_invoice_detail", pk=pk)


def recurring_invoice_resume(request, pk):
    """Resume a recurring invoice"""
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=pk)
    recurring_invoice.status = "active"
    recurring_invoice.save()
    messages.success(
        request,
        f"Recurring invoice for {recurring_invoice.client.name} has been resumed.",
    )
    return redirect("invoices:recurring_invoice_detail", pk=pk)


# Settings view
def company_settings(request):
    settings_obj = CompanySettings.objects.first()
    active_year = get_active_year(request)
    all_years = InvoiceYear.objects.all()

    if request.method == "POST":
        if settings_obj:
            form = CompanySettingsForm(
                request.POST, request.FILES, instance=settings_obj
            )
        else:
            form = CompanySettingsForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Company settings updated successfully.")
            return redirect("invoices:company_settings")
    else:
        if settings_obj:
            form = CompanySettingsForm(instance=settings_obj)
        else:
            form = CompanySettingsForm()

    context = {
        "form": form,
        "active_year": active_year,
        "all_years": all_years,
    }
    return render(request, "invoices/company_settings.html", context)
