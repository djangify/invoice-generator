from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from invoices.models import (
    Client,
    Invoice,
    CompanySettings,
    InvoiceYear,
)
from invoices.forms import (
    CompanySettingsForm,
)
from .utils import get_active_year
from django.http import JsonResponse


@login_required
def switch_year(request, year_id):
    """Switch the active year for the session"""
    year = get_object_or_404(InvoiceYear, id=year_id)
    request.session["active_year_id"] = year.id
    messages.success(request, f"Switched to tax year {year.year_label}")
    return redirect("invoices:dashboard")


@login_required
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


# Settings view
@login_required
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


def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({"status": "healthy"})
