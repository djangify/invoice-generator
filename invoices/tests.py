import csv
import io
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from PIL import Image

from invoices.forms import CompanySettingsForm
from invoices.models import (
    Client,
    Invoice,
    InvoiceItem,
    InvoiceYear,
    RecurringInvoice,
    RecurringInvoiceItem,
)


class InvoiceTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="owner@example.com", password="test-pass-12345"
        )
        cls.client_obj = Client.objects.create(name="Test Client", email="c@example.com")
        cls.invoice = Invoice.objects.create(
            client=cls.client_obj, date=date(2026, 5, 1), due_date=date(2026, 5, 31)
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice, description="Work", quantity=2, rate=10, vat_rate=20
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice, description="Zero rated", quantity=1, rate=5, vat_rate=0
        )


class InvoiceTotalsTests(InvoiceTestBase):
    def test_subtotal_vat_and_total(self):
        self.assertEqual(self.invoice.subtotal(), Decimal("25.00"))
        self.assertEqual(self.invoice.vat_total(), Decimal("4.00"))
        self.assertEqual(self.invoice.total(), Decimal("29.00"))


class EmailInvoiceTests(InvoiceTestBase):
    def test_mailto_link_has_address_subject_and_details(self):
        from urllib.parse import parse_qs, unquote, urlsplit

        link = self.invoice.mailto_link()
        parts = urlsplit(link)
        self.assertEqual(parts.scheme, "mailto")
        self.assertEqual(unquote(parts.path), "c@example.com")
        query = parse_qs(parts.query)
        self.assertIn(self.invoice.invoice_number, query["subject"][0])
        body = query["body"][0]
        self.assertIn("Hello Test Client,", body)
        self.assertIn(self.invoice.invoice_number, body)
        self.assertIn("\u00a329.00", body)
        self.assertIn("31 May 2026", body)

    def test_bank_details_and_payment_link_included_when_set(self):
        from urllib.parse import parse_qs, urlsplit

        from invoices.models import CompanySettings

        CompanySettings.objects.create(
            company_name="Acme Ltd",
            address_line1="1 Road",
            city="Town",
            postcode="AB1 2CD",
            email="me@acme.test",
            sort_code="12-34-56",
            account_number="12345678",
            stripe_payment_link="https://pay.example.com/abc",
        )
        body = parse_qs(urlsplit(self.invoice.mailto_link()).query)["body"][0]
        self.assertIn("Sort code: 12-34-56", body)
        self.assertIn("Account number: 12345678", body)
        self.assertIn("https://pay.example.com/abc", body)
        self.assertIn("Acme Ltd", body)

    def test_awkward_characters_are_encoded(self):
        self.client_obj.name = "Smith & Sons <x> 100%"
        self.client_obj.save()
        link = self.invoice.mailto_link()
        self.assertNotIn("<", link)
        self.assertNotIn(" ", link)
        self.assertEqual(link.count("&"), 1)  # only the subject/body separator

    def test_button_shown_on_invoice_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("invoices:invoice_detail", args=[self.invoice.pk]))
        self.assertContains(response, "Email Invoice")
        self.assertContains(response, 'href="mailto:c@example.com?subject=')


class AuthRequiredTests(InvoiceTestBase):
    def test_pages_redirect_anonymous_users_to_login(self):
        for name, args in [
            ("invoices:dashboard", []),
            ("invoices:invoice_list", []),
            ("invoices:invoice_detail", [self.invoice.pk]),
            ("invoices:invoice_pdf", [self.invoice.pk]),
            ("invoices:client_list", []),
            ("invoices:company_settings", []),
        ]:
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn("/login/", response["Location"], name)

    def test_media_requires_login(self):
        response = self.client.get("/media/logos/anything.png")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])


class StateChangingActionsTests(InvoiceTestBase):
    ACTIONS = [
        "invoices:invoice_mark_paid",
        "invoices:invoice_mark_sent",
        "invoices:invoice_duplicate",
        "invoices:invoice_regenerate_pdf",
    ]

    def setUp(self):
        self.client.force_login(self.user)

    def test_actions_reject_get(self):
        for name in self.ACTIONS:
            response = self.client.get(reverse(name, args=[self.invoice.pk]))
            self.assertEqual(response.status_code, 405, name)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "draft")
        self.assertEqual(Invoice.objects.count(), 1)

    def test_mark_paid_with_post(self):
        response = self.client.post(reverse("invoices:invoice_mark_paid", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 302)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")

    def test_duplicate_with_post_creates_draft(self):
        self.client.post(reverse("invoices:invoice_duplicate", args=[self.invoice.pk]))
        self.assertEqual(Invoice.objects.count(), 2)
        new = Invoice.objects.exclude(pk=self.invoice.pk).get()
        self.assertEqual(new.status, "draft")
        self.assertEqual(new.items.count(), 2)

    def test_post_without_csrf_token_is_rejected(self):
        from django.test import Client as HttpClient

        strict = HttpClient(enforce_csrf_checks=True)
        strict.force_login(self.user)
        response = strict.post(reverse("invoices:invoice_mark_paid", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 403)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "draft")

    def test_pdf_download(self):
        response = self.client.get(reverse("invoices:invoice_pdf", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_dashboard_and_lists_render(self):
        for name in ["invoices:dashboard", "invoices:invoice_list", "invoices:client_list"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)


def make_png(size=(120, 60)):
    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, "PNG")
    return buf.getvalue()


class LogoUploadSecurityTests(TestCase):
    def logo_errors(self, upload):
        form = CompanySettingsForm(data={"company_name": "Acme"}, files={"logo": upload})
        form.is_valid()
        return form

    def test_valid_png_is_accepted_and_renamed(self):
        upload = SimpleUploadedFile("My Logo.png", make_png(), content_type="image/png")
        form = self.logo_errors(upload)
        self.assertNotIn("logo", form.errors)
        self.assertNotIn("My Logo", form.cleaned_data["logo"].name)

    def test_php_disguised_as_image_is_rejected(self):
        upload = SimpleUploadedFile(
            "logo.jpg", b"<?php echo 'pwned'; ?>", content_type="image/jpeg"
        )
        self.assertIn("logo", self.logo_errors(upload).errors)

    def test_oversized_file_is_rejected(self):
        big = make_png() + b"0" * (6 * 1024 * 1024)
        upload = SimpleUploadedFile("big.png", big, content_type="image/png")
        self.assertIn("logo", self.logo_errors(upload).errors)

    def test_huge_dimensions_are_rejected(self):
        upload = SimpleUploadedFile(
            "wide.png", make_png((5000, 20)), content_type="image/png"
        )
        self.assertIn("logo", self.logo_errors(upload).errors)

    def test_media_responses_get_security_headers(self):
        user = get_user_model().objects.create_user(email="u@example.com", password="x-pass-12345")
        self.client.force_login(user)
        # The headers are added to every /media/ response, even for a missing file.
        response = self.client.get("/media/does-not-exist.txt")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")


class TempMediaMixin:
    """Keep any PDFs a test creates out of the real data/media folder."""

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        override = override_settings(MEDIA_ROOT=tmp.name)
        override.enable()
        self.addCleanup(override.disable)


class TaxYearTests(TestCase):
    def test_year_boundaries(self):
        cases = {
            date(2026, 1, 1): 2025,
            date(2026, 4, 5): 2025,  # last day of the 2025-26 tax year
            date(2026, 4, 6): 2026,  # first day of the 2026-27 tax year
            date(2026, 12, 31): 2026,
        }
        for day, expected_start in cases.items():
            self.assertEqual(InvoiceYear.get_year_for_date(day).year_start, expected_start, day)

    def test_year_dates_and_label(self):
        year = InvoiceYear.get_year_for_date(date(2026, 5, 1))
        self.assertEqual(year.start_date, date(2026, 4, 6))
        self.assertEqual(year.end_date, date(2027, 4, 5))
        self.assertEqual(year.year_label, "2026-27")

    def test_invoice_gets_the_right_tax_year(self):
        client = Client.objects.create(name="C", email="c@example.com")
        before = Invoice.objects.create(client=client, date=date(2026, 4, 5), due_date=date(2026, 5, 5))
        after = Invoice.objects.create(client=client, date=date(2026, 4, 6), due_date=date(2026, 5, 6))
        self.assertEqual(before.tax_year.year_label, "2025-26")
        self.assertEqual(after.tax_year.year_label, "2026-27")


class RecurringDatesTests(InvoiceTestBase):
    def make(self, **kwargs):
        defaults = dict(
            client=self.client_obj,
            frequency="monthly",
            start_date=date(2026, 1, 31),
            next_invoice_date=date(2026, 1, 31),
        )
        defaults.update(kwargs)
        return RecurringInvoice.objects.create(**defaults)

    def test_monthly_from_the_31st_does_not_drift_to_the_28th(self):
        recurring = self.make()
        day = date(2026, 1, 31)
        seen = []
        for _ in range(4):
            day = recurring.calculate_next_date(day)
            seen.append(day)
        self.assertEqual(
            seen, [date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30), date(2026, 5, 31)]
        )

    def test_weekly_quarterly_and_yearly(self):
        weekly = self.make(frequency="weekly", start_date=date(2026, 3, 2), next_invoice_date=date(2026, 3, 2))
        self.assertEqual(weekly.calculate_next_date(date(2026, 3, 2)), date(2026, 3, 9))
        quarterly = self.make(frequency="quarterly", start_date=date(2026, 11, 30), next_invoice_date=date(2026, 11, 30))
        self.assertEqual(quarterly.calculate_next_date(date(2026, 11, 30)), date(2027, 2, 28))
        yearly = self.make(frequency="yearly", start_date=date(2028, 2, 29), next_invoice_date=date(2028, 2, 29))
        self.assertEqual(yearly.calculate_next_date(date(2028, 2, 29)), date(2029, 2, 28))
        self.assertEqual(yearly.calculate_next_date(date(2031, 2, 28)), date(2032, 2, 29))


class RecurringGenerationTests(TempMediaMixin, InvoiceTestBase):
    def make(self, **kwargs):
        today = date.today()
        defaults = dict(
            client=self.client_obj,
            frequency="monthly",
            start_date=today - timedelta(days=60),
            next_invoice_date=today,
        )
        defaults.update(kwargs)
        recurring = RecurringInvoice.objects.create(**defaults)
        RecurringInvoiceItem.objects.create(
            recurring_invoice=recurring, description="Retainer", quantity=1, rate=100, vat_rate=20
        )
        return recurring

    def test_generates_a_draft_with_items_and_moves_the_date_on(self):
        recurring = self.make()
        before = Invoice.objects.count()
        invoice = recurring.generate_invoice()
        self.assertEqual(Invoice.objects.count(), before + 1)
        self.assertEqual(invoice.status, "draft")
        self.assertEqual(invoice.items.count(), 1)
        self.assertEqual(invoice.total(), Decimal("120.00"))
        self.assertTrue(invoice.pdf_file)
        recurring.refresh_from_db()
        self.assertGreater(recurring.next_invoice_date, date.today())

    def test_running_twice_does_not_make_a_duplicate(self):
        self.make()
        before = Invoice.objects.count()
        call_command("process_recurring_invoices", stdout=io.StringIO())
        call_command("process_recurring_invoices", stdout=io.StringIO())
        self.assertEqual(Invoice.objects.count(), before + 1)

    def test_not_due_paused_and_ended_are_skipped(self):
        not_due = self.make(next_invoice_date=date.today() + timedelta(days=5))
        paused = self.make(status="paused")
        self.assertFalse(not_due.should_generate_invoice())
        self.assertFalse(paused.should_generate_invoice())
        self.assertIsNone(paused.generate_invoice())

    def test_last_invoice_before_the_end_date_is_made_once_only(self):
        # The end date is today, so this is the final invoice. Generating it must
        # succeed and must not make another one on the next run.
        recurring = self.make(end_date=date.today())
        before = Invoice.objects.count()
        self.assertIsNotNone(recurring.generate_invoice())
        recurring.refresh_from_db()
        self.assertFalse(recurring.should_generate_invoice())
        call_command("process_recurring_invoices", stdout=io.StringIO())
        self.assertEqual(Invoice.objects.count(), before + 1)


class OverdueTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name="C", email="c@example.com")
        self.today = date(2026, 6, 15)

    def invoice(self, status, due):
        return Invoice.objects.create(
            client=self.client_obj, date=date(2026, 5, 1), due_date=due, status=status
        )

    def test_only_sent_invoices_past_their_due_date_become_overdue(self):
        late_sent = self.invoice("sent", date(2026, 6, 14))
        due_today = self.invoice("sent", date(2026, 6, 15))
        late_draft = self.invoice("draft", date(2026, 6, 1))
        late_paid = self.invoice("paid", date(2026, 6, 1))
        changed = Invoice.mark_overdue(today=self.today)
        self.assertEqual(changed, 1)
        for invoice, expected in [
            (late_sent, "overdue"),
            (due_today, "sent"),
            (late_draft, "draft"),
            (late_paid, "paid"),
        ]:
            invoice.refresh_from_db()
            self.assertEqual(invoice.status, expected)

    def test_dashboard_and_list_mark_invoices_overdue(self):
        user = get_user_model().objects.create_user(email="u@example.com", password="x-pass-12345")
        self.client.force_login(user)
        invoice = Invoice.objects.create(
            client=self.client_obj,
            date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=30),
            status="sent",
        )
        self.client.get(reverse("invoices:dashboard"))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "overdue")


class CsvExportTests(InvoiceTestBase):
    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse("invoices:invoice_export_csv")

    def rows(self, response):
        text = response.content.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(text)))

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_exports_the_active_year(self):
        # InvoiceTestBase makes a May 2026 invoice, which is in tax year 2026-27.
        session = self.client.session
        session["active_year_id"] = self.invoice.tax_year_id
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("invoices-2026-27.csv", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        rows = self.rows(response)
        self.assertEqual(rows[0][0], "Invoice number")
        self.assertEqual(
            rows[1],
            [
                self.invoice.invoice_number,
                "Test Client",
                "c@example.com",
                "2026-05-01",
                "2026-05-31",
                "Draft",
                "25.00",
                "4.00",
                "29.00",
            ],
        )

    def test_status_filter_is_applied(self):
        session = self.client.session
        session["active_year_id"] = self.invoice.tax_year_id
        session.save()
        rows = self.rows(self.client.get(self.url + "?status=paid"))
        self.assertEqual(len(rows), 1)  # headings only

    def test_spreadsheet_formulas_in_names_are_neutralised(self):
        self.client_obj.name = "=HYPERLINK(\"http://evil.test\",\"x\")"
        self.client_obj.save()
        session = self.client.session
        session["active_year_id"] = self.invoice.tax_year_id
        session.save()
        rows = self.rows(self.client.get(self.url))
        self.assertTrue(rows[1][1].startswith("'="))

    def test_export_button_on_invoice_list(self):
        response = self.client.get(reverse("invoices:invoice_list"))
        self.assertContains(response, "Export CSV")
