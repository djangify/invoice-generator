#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create the first login if it does not exist. If DJANGO_SUPERUSER_PASSWORD is empty a
# random password is generated: it is printed below and saved in data/first_login.txt.
# Credentials are read from the environment by Django, never pasted into code.
echo "Checking first login..."
python manage.py create_default_user

# Initialize tax year
python manage.py shell -c "
from invoices.models import InvoiceYear
InvoiceYear.get_active_year()
print('Tax year initialized.')
"

echo "Starting server..."
exec "$@"
