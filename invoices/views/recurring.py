from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from invoices.models import (
    RecurringInvoice,
    InvoiceYear,
)
from invoices.forms import (
    RecurringInvoiceForm,
    RecurringInvoiceItemFormSet,
)
from .utils import get_active_year


# Recurring Invoice views
@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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


@login_required
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
