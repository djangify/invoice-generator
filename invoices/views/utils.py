from invoices.models import InvoiceYear


def get_active_year(request):
    year_id = request.session.get("active_year_id")
    if year_id:
        try:
            return InvoiceYear.objects.get(id=year_id)
        except InvoiceYear.DoesNotExist:
            pass
    return InvoiceYear.get_active_year()
