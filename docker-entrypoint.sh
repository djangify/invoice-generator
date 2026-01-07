#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if credentials provided and user doesn't exist
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Checking superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='${DJANGO_SUPERUSER_EMAIL}').exists():
    User.objects.create_superuser(email='${DJANGO_SUPERUSER_EMAIL}', password='${DJANGO_SUPERUSER_PASSWORD}')
    print('Superuser created.')
else:
    print('Superuser already exists.')
EOF
fi

# Initialize tax year
python manage.py shell << EOF
from invoices.models import InvoiceYear
InvoiceYear.get_active_year()
print('Tax year initialized.')
EOF

echo "Starting server..."
exec "$@"
