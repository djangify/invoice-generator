"""
Management command to process recurring invoices.

This command checks all active recurring invoices and generates
any that are due. Run this daily via cron or a scheduler.

Usage:
    python manage.py process_recurring_invoices
    python manage.py process_recurring_invoices --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from invoices.models import RecurringInvoice


class Command(BaseCommand):
    help = "Process recurring invoices and generate any that are due"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without actually creating invoices",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN - No invoices will be created\n")
            )

        # Get all active recurring invoices
        recurring_invoices = RecurringInvoice.objects.filter(status="active")

        self.stdout.write(
            f"Checking {recurring_invoices.count()} active recurring invoices..."
        )
        self.stdout.write(f"Current date: {timezone.now().date()}\n")

        generated_count = 0
        skipped_count = 0

        for recurring in recurring_invoices:
            if recurring.should_generate_invoice():
                self.stdout.write(
                    f"  → {recurring.client.name} ({recurring.get_frequency_display()}) "
                    f"- Due: {recurring.next_invoice_date}"
                )

                if not dry_run:
                    try:
                        invoice = recurring.generate_invoice()
                        if invoice:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"    ✓ Generated {invoice.invoice_number}"
                                )
                            )
                            generated_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING("    ⚠ Could not generate invoice")
                            )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"    ✗ Error: {str(e)}"))
                else:
                    self.stdout.write(
                        self.style.SUCCESS("    ✓ Would generate invoice")
                    )
                    generated_count += 1
            else:
                skipped_count += 1

        self.stdout.write("")

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN complete: {generated_count} invoices would be generated, "
                    f"{skipped_count} not yet due"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Complete: {generated_count} invoices generated, "
                    f"{skipped_count} not yet due"
                )
            )
