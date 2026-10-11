import io
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings


class CreateDefaultUserTests(TestCase):
    def run_command(self, *args):
        out = io.StringIO()
        call_command("create_default_user", *args, stdout=out)
        return out.getvalue()

    def test_creates_login_with_random_password_and_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(
                DATA_DIR=Path(tmp),
                DEFAULT_USER_EMAIL="first@example.com",
                DEFAULT_USER_PASSWORD="",
            ):
                self.run_command()
                note = (Path(tmp) / "first_login.txt").read_text(encoding="utf-8")
                password = note.split("Password: ")[1].splitlines()[0]
                user = get_user_model().objects.get(email="first@example.com")
                self.assertTrue(user.is_superuser)
                self.assertGreaterEqual(len(password), 16)
                self.assertTrue(user.check_password(password))

    def test_does_not_change_existing_login_without_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(
                DATA_DIR=Path(tmp),
                DEFAULT_USER_EMAIL="first@example.com",
                DEFAULT_USER_PASSWORD="",
            ):
                self.run_command()
                before = get_user_model().objects.get(email="first@example.com").password
                self.run_command()
                after = get_user_model().objects.get(email="first@example.com").password
                self.assertEqual(before, after)

    def test_reset_gives_new_password(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(
                DATA_DIR=Path(tmp),
                DEFAULT_USER_EMAIL="first@example.com",
                DEFAULT_USER_PASSWORD="",
            ):
                self.run_command()
                before = get_user_model().objects.get(email="first@example.com").password
                self.run_command("--reset")
                after = get_user_model().objects.get(email="first@example.com").password
                self.assertNotEqual(before, after)

    def test_configured_password_is_used_and_not_written_to_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(
                DATA_DIR=Path(tmp),
                DEFAULT_USER_EMAIL="first@example.com",
                DEFAULT_USER_PASSWORD="my-own-pass-98765",
            ):
                self.run_command()
                user = get_user_model().objects.get(email="first@example.com")
                self.assertTrue(user.check_password("my-own-pass-98765"))
                self.assertFalse((Path(tmp) / "first_login.txt").exists())
