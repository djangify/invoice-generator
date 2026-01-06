from django.urls import path
from . import views

app_name = "invoices"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    # Year switching
    path("switch-year/<int:year_id>/", views.switch_year, name="switch_year"),
    # Clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_create, name="client_create"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),
    # Invoices
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/add/", views.invoice_create, name="invoice_create"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("invoices/<int:pk>/delete/", views.invoice_delete, name="invoice_delete"),
    path("invoices/<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path(
        "invoices/<int:pk>/regenerate-pdf/",
        views.invoice_regenerate_pdf,
        name="invoice_regenerate_pdf",
    ),
    # Recurring Invoices
    path("recurring/", views.recurring_invoice_list, name="recurring_invoice_list"),
    path(
        "recurring/add/",
        views.recurring_invoice_create,
        name="recurring_invoice_create",
    ),
    path(
        "recurring/<int:pk>/",
        views.recurring_invoice_detail,
        name="recurring_invoice_detail",
    ),
    path(
        "recurring/<int:pk>/edit/",
        views.recurring_invoice_edit,
        name="recurring_invoice_edit",
    ),
    path(
        "recurring/<int:pk>/delete/",
        views.recurring_invoice_delete,
        name="recurring_invoice_delete",
    ),
    path(
        "recurring/<int:pk>/generate/",
        views.recurring_invoice_generate,
        name="recurring_invoice_generate",
    ),
    path(
        "recurring/<int:pk>/pause/",
        views.recurring_invoice_pause,
        name="recurring_invoice_pause",
    ),
    path(
        "recurring/<int:pk>/resume/",
        views.recurring_invoice_resume,
        name="recurring_invoice_resume",
    ),
    # Settings
    path("settings/", views.company_settings, name="company_settings"),
]
