from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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
