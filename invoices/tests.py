import io
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from PIL import Image

from invoices.forms import CompanySettingsForm
from invoices.models import Client, Invoice, InvoiceItem


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

    def test_health_check_is_public(self):
        self.assertEqual(self.client.get(reverse("invoices:health_check")).status_code, 200)

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
