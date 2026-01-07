from .main_views import (
    dashboard,
    switch_year,
    company_settings,
    health_check,
)

from .client import (
    client_list,
    client_create,
    client_edit,
    client_delete,
    client_invoices,
    client_invoices_pdf,
)

from .invoice import (
    invoice_list,
    invoice_detail,
    invoice_create,
    invoice_edit,
    invoice_delete,
    invoice_pdf,
    invoice_regenerate_pdf,
    invoice_mark_paid,
    invoice_mark_sent,
    invoice_duplicate,
)

from .recurring import (
    recurring_invoice_list,
    recurring_invoice_detail,
    recurring_invoice_create,
    recurring_invoice_edit,
    recurring_invoice_delete,
    recurring_invoice_generate,
    recurring_invoice_pause,
    recurring_invoice_resume,
)
