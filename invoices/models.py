from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import os


class InvoiceYear(models.Model):
    """Track invoice activity by UK tax year (April to April)"""

    year_start = models.IntegerField(unique=True)
    year_end = models.IntegerField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year_start"]
        verbose_name = "Invoice Year"
        verbose_name_plural = "Invoice Years"

    def __str__(self):
        return f"{self.year_start}-{self.year_end}"

    @property
    def year_label(self):
        return f"{self.year_start}-{str(self.year_end)[-2:]}"

    @property
    def start_date(self):
        return date(self.year_start, 4, 6)

    @property
    def end_date(self):
        return date(self.year_end, 4, 5)

    @classmethod
    def get_active_year(cls):
        active = cls.objects.filter(is_active=True).first()
        if not active:
            active = cls.create_current_year()
        return active

    @classmethod
    def create_current_year(cls):
        today = date.today()
        if today.month < 4 or (today.month == 4 and today.day < 6):
            year_start = today.year - 1
        else:
            year_start = today.year
        year_end = year_start + 1

        cls.objects.all().update(is_active=False)

        year, created = cls.objects.get_or_create(
            year_start=year_start, defaults={"year_end": year_end, "is_active": True}
        )

        if not created:
            year.is_active = True
            year.save()

        return year

    @classmethod
    def get_year_for_date(cls, invoice_date):
        if invoice_date.month < 4 or (invoice_date.month == 4 and invoice_date.day < 6):
            year_start = invoice_date.year - 1
        else:
            year_start = invoice_date.year
        year_end = year_start + 1

        year, created = cls.objects.get_or_create(
            year_start=year_start, defaults={"year_end": year_end, "is_active": False}
        )
        return year

    def save(self, *args, **kwargs):
        if self.is_active:
            InvoiceYear.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class CompanySettings(models.Model):
    company_name = models.CharField(max_length=200)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField()
    vat_number = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

    bank_name = models.CharField(max_length=200, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    sort_code = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    swift_bic = models.CharField(max_length=20, blank=True)

    stripe_payment_link = models.URLField(
        blank=True, help_text="Your Stripe payment link"
    )
    paypal_me_link = models.URLField(blank=True, help_text="Your PayPal.me link")

    default_payment_terms = models.TextField(
        blank=True,
        default="Payment is due within 30 days of the invoice date. Late payments may incur additional charges.",
        help_text="Default payment terms",
    )

    invoice_footer = models.TextField(
        blank=True, help_text="Custom footer text for invoices"
    )

    class Meta:
        verbose_name_plural = "Company Settings"


class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    vat_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


def invoice_pdf_path(instance, filename):
    year_label = instance.tax_year.year_label if instance.tax_year else "unknown"
    return f"invoices/{year_label}/{instance.invoice_number}.pdf"


class RecurringInvoice(models.Model):
    """Template for recurring invoices"""

    FREQUENCY_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Start and end dates
    start_date = models.DateField()
    end_date = models.DateField(
        blank=True, null=True, help_text="Leave blank for no end date"
    )
    next_invoice_date = models.DateField()

    # Invoice details
    notes = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True)
    payment_link = models.URLField(blank=True)

    # Auto-send (for future feature)
    auto_send = models.BooleanField(
        default=False, help_text="Automatically create invoices (manual for now)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recurring: {self.client.name} - {self.get_frequency_display()}"

    def calculate_next_date(self, from_date=None):
        """Calculate the next invoice date based on frequency"""
        if from_date is None:
            from_date = self.next_invoice_date

        if self.frequency == "weekly":
            return from_date + timedelta(weeks=1)
        elif self.frequency == "monthly":
            return from_date + relativedelta(months=1)
        elif self.frequency == "quarterly":
            return from_date + relativedelta(months=3)
        elif self.frequency == "yearly":
            return from_date + relativedelta(years=1)

        return from_date

    def should_generate_invoice(self):
        """Check if it's time to generate a new invoice"""
        if self.status != "active":
            return False

        if self.next_invoice_date > date.today():
            return False

        if self.end_date and date.today() > self.end_date:
            return False

        return True

    def generate_invoice(self):
        """Generate a new invoice from this recurring template"""
        if not self.should_generate_invoice():
            return None

        # Calculate due date (30 days from invoice date by default)
        invoice_date = self.next_invoice_date
        due_date = invoice_date + timedelta(days=30)

        # Create the invoice
        invoice = Invoice.objects.create(
            client=self.client,
            date=invoice_date,
            due_date=due_date,
            status="draft",
            notes=self.notes,
            payment_terms=self.payment_terms,
            payment_link=self.payment_link,
        )

        # Copy items from the most recent invoice for this recurring template
        # or from the template items
        for template_item in self.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                description=template_item.description,
                quantity=template_item.quantity,
                rate=template_item.rate,
                vat_rate=template_item.vat_rate,
            )

        # Generate PDF
        invoice.generate_and_save_pdf()

        # Update next invoice date
        self.next_invoice_date = self.calculate_next_date()
        self.save()

        return invoice

    class Meta:
        ordering = ["-created_at"]


class RecurringInvoiceItem(models.Model):
    """Template items for recurring invoices"""

    recurring_invoice = models.ForeignKey(
        RecurringInvoice, related_name="items", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)

    def line_total(self):
        return self.quantity * self.rate

    def vat_amount(self):
        return self.line_total() * (self.vat_rate / 100)

    def total_with_vat(self):
        return self.line_total() + self.vat_amount()

    def __str__(self):
        return f"{self.description} - {self.recurring_invoice}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    tax_year = models.ForeignKey(
        InvoiceYear, on_delete=models.PROTECT, null=True, blank=True
    )

    # Link to recurring invoice if generated from one
    recurring_invoice = models.ForeignKey(
        RecurringInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_invoices",
    )

    pdf_file = models.FileField(upload_to=invoice_pdf_path, blank=True, null=True)
    pdf_generated_at = models.DateTimeField(blank=True, null=True)

    payment_terms = models.TextField(blank=True)
    payment_link = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        if not self.tax_year:
            self.tax_year = InvoiceYear.get_year_for_date(self.date)

        if self.pk:
            try:
                old_invoice = Invoice.objects.get(pk=self.pk)
                if (
                    old_invoice.client_id != self.client_id
                    or old_invoice.date != self.date
                    or old_invoice.due_date != self.due_date
                    or old_invoice.status != self.status
                    or old_invoice.notes != self.notes
                    or old_invoice.payment_terms != self.payment_terms
                    or old_invoice.payment_link != self.payment_link
                ):
                    if self.pdf_file:
                        self.delete_pdf()
            except Invoice.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        year = self.date.year
        last_invoice = (
            Invoice.objects.filter(invoice_number__startswith=f"INV-{year}-")
            .order_by("invoice_number")
            .last()
        )

        if last_invoice:
            last_number = int(last_invoice.invoice_number.split("-")[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"INV-{year}-{new_number:03d}"

    def generate_and_save_pdf(self):
        from .pdf_generator import InvoicePDF
        from django.core.files.base import ContentFile

        pdf_generator = InvoicePDF(self)
        pdf_content = pdf_generator.generate()

        if self.pdf_file:
            self.delete_pdf()

        filename = f"{self.invoice_number}.pdf"
        self.pdf_file.save(filename, ContentFile(pdf_content), save=False)
        self.pdf_generated_at = timezone.now()
        self.save(update_fields=["pdf_file", "pdf_generated_at"])

        return self.pdf_file.path

    def delete_pdf(self):
        if self.pdf_file:
            if os.path.isfile(self.pdf_file.path):
                os.remove(self.pdf_file.path)
            self.pdf_file = None
            self.pdf_generated_at = None

    def get_or_generate_pdf(self):
        if not self.pdf_file:
            self.generate_and_save_pdf()
        return self.pdf_file

    def pdf_needs_regeneration(self):
        if not self.pdf_file:
            return True
        if not self.pdf_generated_at:
            return True
        if self.updated_at > self.pdf_generated_at:
            return True
        return False

    def get_payment_terms(self):
        if self.payment_terms:
            return self.payment_terms
        company = CompanySettings.objects.first()
        return company.default_payment_terms if company else ""

    def get_payment_link(self):
        if self.payment_link:
            return self.payment_link
        company = CompanySettings.objects.first()
        if company:
            return company.stripe_payment_link or company.paypal_me_link
        return ""

    def subtotal(self):
        return sum(item.line_total() for item in self.items.all())

    def vat_total(self):
        return sum(item.vat_amount() for item in self.items.all())

    def total(self):
        return self.subtotal() + self.vat_total()

    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"

    class Meta:
        ordering = ["-date", "-created_at"]

    def delete(self, *args, **kwargs):
        self.delete_pdf()
        super().delete(*args, **kwargs)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)

    def line_total(self):
        return self.quantity * self.rate

    def vat_amount(self):
        return self.line_total() * (self.vat_rate / 100)

    def total_with_vat(self):
        return self.line_total() + self.vat_amount()

    def __str__(self):
        return f"{self.description} - {self.invoice.invoice_number}"
