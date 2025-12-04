from django import forms
from .models import (
    Client,
    Invoice,
    InvoiceItem,
    CompanySettings,
    RecurringInvoice,
    RecurringInvoiceItem,
)
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "name",
            "email",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "postcode",
            "vat_number",
        ]


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "client",
            "date",
            "due_date",
            "status",
            "notes",
            "payment_terms",
            "payment_link",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "payment_terms": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get("date")
        due_date = cleaned_data.get("due_date")

        if invoice_date and due_date:
            if due_date < invoice_date:
                raise ValidationError(
                    {"due_date": "Due date must be on or after the invoice date."}
                )

        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["description", "quantity", "rate", "vat_rate"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"step": "0.01"}),
            "rate": forms.NumberInput(attrs={"step": "0.01"}),
            "vat_rate": forms.NumberInput(attrs={"step": "0.01"}),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=3, can_delete=True
)


class RecurringInvoiceForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoice
        fields = [
            "client",
            "frequency",
            "start_date",
            "end_date",
            "next_invoice_date",
            "status",
            "notes",
            "payment_terms",
            "payment_link",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "next_invoice_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "payment_terms": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError(
                    {"end_date": "End date must be after the start date."}
                )

        return cleaned_data


class RecurringInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoiceItem
        fields = ["description", "quantity", "rate", "vat_rate"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"step": "0.01"}),
            "rate": forms.NumberInput(attrs={"step": "0.01"}),
            "vat_rate": forms.NumberInput(attrs={"step": "0.01"}),
        }


RecurringInvoiceItemFormSet = inlineformset_factory(
    RecurringInvoice,
    RecurringInvoiceItem,
    form=RecurringInvoiceItemForm,
    extra=3,
    can_delete=True,
)


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = [
            "company_name",
            "address_line1",
            "address_line2",
            "city",
            "postcode",
            "phone",
            "email",
            "vat_number",
            "logo",
            "bank_name",
            "account_name",
            "account_number",
            "sort_code",
            "iban",
            "swift_bic",
            "stripe_payment_link",
            "paypal_me_link",
            "default_payment_terms",
            "invoice_footer",
        ]
        widgets = {
            "default_payment_terms": forms.Textarea(attrs={"rows": 3}),
            "invoice_footer": forms.Textarea(attrs={"rows": 2}),
        }
