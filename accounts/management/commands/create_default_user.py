import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

# No look-alike characters (0/O, 1/l/I) so the password is easy to read and type.
_ALPHABET = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI")


def generate_password(length=16):
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


class Command(BaseCommand):
    help = (
        "Create the first login (random password) if it does not exist. "
        "Use --reset to give the existing login a new random password."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Set a NEW random password for the default login (forgotten password).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = settings.DEFAULT_USER_EMAIL
        configured_password = settings.DEFAULT_USER_PASSWORD
        user = User.objects.filter(email=email).first()

        if user and not options["reset"]:
            self.stdout.write(self.style.NOTICE(f"Login already exists: {email}"))
            return

        password = configured_password or generate_password()

        if user:
            user.set_password(password)
            user.save(update_fields=["password"])
            action = "Password reset"
        else:
            User.objects.create_superuser(email=email, password=password)
            action = "Created login"

        # Only write the password to disk when we generated it. If the user chose
        # one (DJANGO_SUPERUSER_PASSWORD) there is nothing to hand back.
        if not configured_password:
            note = settings.DATA_DIR / "first_login.txt"
            note.write_text(
                "Invoice Generator login\n"
                f"Email:    {email}\n"
                f"Password: {password}\n\n"
                "Log in, go to the password change page, choose your own password,\n"
                "then DELETE THIS FILE.\n",
                encoding="utf-8",
            )
            self.stdout.write(self.style.SUCCESS(f"{action}: {email}"))
            self.stdout.write(f"Password: {password}")
            self.stdout.write(
                f"(also saved in {note} - delete it once you have changed your password)"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action}: {email} (password from DJANGO_SUPERUSER_PASSWORD)"
                )
            )
