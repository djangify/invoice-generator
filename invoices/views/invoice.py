from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from invoices.models import (
    Invoice,
    InvoiceItem,
    InvoiceYear,
)
from invoices.forms import (
    InvoiceForm,
    InvoiceItemFormSet,
)
from invoices.pdf_generator import InvoicePDF
from .utils import get_active_year


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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
