from django.contrib import admin
from .models import (
    CompanySettings,
    Client,
    Invoice,
    InvoiceItem,
    InvoiceYear,
    RecurringInvoice,
    RecurringInvoiceItem,
)


@admin.register(InvoiceYear)
class InvoiceYearAdmin(admin.ModelAdmin):
    list_display = ["year_label", "start_date", "end_date", "is_active", "created_at"]
    list_filter = ["is_active"]
    ordering = ["-year_start"]

    def year_label(self, obj):
        return obj.year_label

    year_label.short_description = "Tax Year"


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ["company_name", "email", "phone", "vat_number"]

    def has_add_permission(self, request):
        return not CompanySettings.objects.exists()


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "city", "postcode", "created_at"]
    search_fields = ["name", "email", "city"]
    list_filter = ["city", "created_at"]
    ordering = ["name"]


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ["description", "quantity", "rate", "vat_rate"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "client",
        "date",
        "due_date",
        "status",
        "tax_year",
        "recurring_invoice",
        "total",
    ]
    list_filter = ["status", "date", "due_date", "tax_year"]
    search_fields = ["invoice_number", "client__name"]
    readonly_fields = ["invoice_number", "tax_year", "created_at"]
    inlines = [InvoiceItemInline]

    fieldsets = (
        (
            "Client Information",
            {"fields": ("client", "invoice_number", "tax_year", "recurring_invoice")},
        ),
        ("Invoice Details", {"fields": ("date", "due_date", "status")}),
        ("Payment Information", {"fields": ("payment_terms", "payment_link")}),
        (
            "Additional Information",
            {"fields": ("notes", "created_at"), "classes": ("collapse",)},
        ),
    )

    def total(self, obj):
        return f"£{obj.total():.2f}"

    total.short_description = "Total"


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        "invoice",
        "description",
        "quantity",
        "rate",
        "vat_rate",
        "line_total",
    ]
    list_filter = ["invoice__date"]
    search_fields = ["description", "invoice__invoice_number"]

    def line_total(self, obj):
        return f"£{obj.line_total():.2f}"

    line_total.short_description = "Line Total"


class RecurringInvoiceItemInline(admin.TabularInline):
    model = RecurringInvoiceItem
    extra = 1
    fields = ["description", "quantity", "rate", "vat_rate"]


@admin.register(RecurringInvoice)
class RecurringInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "client",
        "frequency",
        "status",
        "next_invoice_date",
        "start_date",
        "end_date",
    ]
    list_filter = ["status", "frequency", "start_date"]
    search_fields = ["client__name"]
    inlines = [RecurringInvoiceItemInline]

    fieldsets = (
        ("Client Information", {"fields": ("client", "frequency", "status")}),
        ("Schedule", {"fields": ("start_date", "end_date", "next_invoice_date")}),
        ("Payment Information", {"fields": ("payment_terms", "payment_link")}),
        (
            "Additional Information",
            {
                "fields": ("notes", "auto_send"),
            },
        ),
    )


@admin.register(RecurringInvoiceItem)
class RecurringInvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        "recurring_invoice",
        "description",
        "quantity",
        "rate",
        "vat_rate",
        "line_total",
    ]
    search_fields = ["description", "recurring_invoice__client__name"]

    def line_total(self, obj):
        return f"£{obj.line_total():.2f}"

    line_total.short_description = "Line Total"
