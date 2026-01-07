
# Invoice Generator

![Invoice Generator header](https://github.com/djangify/invoice-generator/blob/436e389e92f8b87cec47ebb776ae71ee699cf439/invoice-generator-diane-corriette.png)


A self-hosted Django application for creating and managing invoices, tracking payments, and generating professional PDFs. Designed for UK tax year tracking (April to April).


<p align="center">
  <a href="https://www.djangoproject.com/">
    <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  </a>
  
  <a href="https://tailwindcss.com/">
    <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS">
  </a>

  <img src="https://img.shields.io/badge/Database-SQLite--First-003B57?style=for-the-badge" alt="SQLite First">


  <img src="https://img.shields.io/badge/Deployment-Docker--Ready-2496ED?style=for-the-badge" alt="Docker Ready">

  <img src="https://img.shields.io/badge/Hosting-Self--Hosted--Ready-4B5563?style=for-the-badge" alt="Self Hosted Ready">

  <a href="https://www.hardenize.com/">
    <img src="https://img.shields.io/badge/VPS%20Hosting-Self%20Managed-blue?style=for-the-badge&logo=linux&logoColor=white" alt="VPS Hosting">
  </a>

</p>

## Features

- **Client Management** - Add, edit, and delete clients with full contact and VAT details
- **Invoice Creation** - Create invoices with multiple line items, VAT calculations, and custom notes
- **PDF Generation** - Professional PDF invoices with company branding, bank details, and payment links
- **Recurring Invoices** - Set up weekly, monthly, quarterly, or yearly recurring invoice templates
- **Tax Year Tracking** - Organise invoices by UK tax year (6 April to 5 April)
- **Quick Actions** - Mark invoices as Sent or Paid with one click
- **Duplicate Invoices** - Clone existing invoices for repeat billing
- **Client History** - View all invoices for a specific client with totals and PDF export
- **Payment Integration** - Add Stripe or PayPal payment links to invoices

## Requirements

- Docker and Docker Compose

OR for local development:
- Python 3.11+
- pip

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/invoice-generator.git
cd invoice-generator
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
SECRET_KEY=generate-a-secure-random-string-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

DJANGO_SUPERUSER_EMAIL=your@email.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password

TZ=Europe/London
```

**Generate a secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Build and Run

```bash
docker compose up --build -d
```

### 4. Access the Application

- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

Login with the email and password you set in `.env`

## First-Time Setup

After logging in for the first time:

### 1. Configure Company Settings

Go to **Settings** in the navigation bar and complete:

- **Company Information** - Your company name, address, email, phone, VAT number
- **Company Logo** - Upload your logo (recommended: max 600×300px horizontal or 300×300px square)
- **Bank Details** - Bank name, account name, account number, sort code (appears on invoices for bank transfers)
- **Payment Links** - Add your Stripe payment link or PayPal.me link
- **Payment Terms** - Default terms that appear on all invoices
- **Invoice Footer** - Optional footer text (e.g., "Thank you for your business!")

### 2. Add Your First Client

Go to **Clients** → **Add Client** and enter:
- Client name
- Email address
- Phone (optional)
- Full address
- VAT number (optional)

### 3. Create Your First Invoice

Go to **Invoices** → **New Invoice**:
1. Select the client
2. Set invoice date and due date
3. Add line items with description, quantity, rate, and VAT rate
4. Add any notes
5. Save the invoice

## Data Storage

All persistent data is stored in the `./data/` directory:

```
data/
├── db/
│   └── db.sqlite3      # SQLite database
├── media/
│   ├── logos/          # Company logos
│   └── invoices/       # Generated PDF invoices (organised by tax year)
└── logs/
    └── django.log      # Application error logs
```

Static files are stored in `./staticfiles/`

**Important**: Back up the `./data/` directory regularly to prevent data loss.

## Docker Commands

```bash
# Start the application
docker compose up -d

# Stop the application
docker compose down

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up --build -d

# Restart the application
docker compose restart

# Create superuser manually
docker compose exec web python manage.py createsuperuser

# Access Django shell
docker compose exec web python manage.py shell

# Run migrations manually
docker compose exec web python manage.py migrate

# Backup database
cp ./data/db/db.sqlite3 ./backups/db-$(date +%Y%m%d).sqlite3
```

## Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p db media logs

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## Invoice Workflow

1. **Draft** - Invoice is created but not yet sent
2. **Sent** - Invoice has been sent to the client
3. **Paid** - Client has paid the invoice
4. **Overdue** - Invoice is past due date and unpaid

Use the quick action buttons on the invoice list or detail page to change status.

## Tax Years

The application organises invoices by UK tax year (6 April to 5 April). 

- Use the dropdown in the top right to switch between tax years
- The dashboard shows statistics for the currently selected tax year
- Invoices are automatically assigned to the correct tax year based on the invoice date

## Recurring Invoices

Set up recurring invoice templates for regular billing:

1. Go to **Recurring** → **New Recurring Invoice**
2. Select client and frequency (weekly/monthly/quarterly/yearly)
3. Set start date, next invoice date, and optional end date
4. Add the standard line items
5. Save the template

To generate an invoice from a template:
- Click **Generate Invoice Now** on the recurring invoice detail page
- The system automatically advances the next invoice date

## Recurring Invoice Automation

Recurring invoices can be automatically generated when they're due. There are several ways to set this up:

### Docker (Recommended)

The `docker-compose.yml` includes a scheduler service that automatically checks for due recurring invoices daily at 6:00 AM.

**To change the schedule time**, edit `docker-compose.yml`:
```yaml
scheduler:
  environment:
    - SCHEDULE_HOUR=6    # Hour (0-23)
    - SCHEDULE_MINUTE=0  # Minute (0-59)
```

**To check scheduler status:**
```bash
docker compose logs scheduler -f
```

**To manually trigger recurring invoice processing:**
```bash
docker compose exec web python manage.py process_recurring_invoices
```

**To see what would be generated (dry run):**
```bash
docker compose exec web python manage.py process_recurring_invoices --dry-run
```

### Local Development

For local development, you'll need to run the command manually or set up your own scheduler:

**Manual processing:**
```bash
python manage.py process_recurring_invoices
```

**Using cron (Linux/macOS):**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6:00 AM
0 6 * * * cd /path/to/invoice-generator && /path/to/venv/bin/python manage.py process_recurring_invoices >> logs/recurring.log 2>&1
```

**Using Task Scheduler (Windows):**
1. Open Task Scheduler
2. Create a Basic Task
3. Set trigger to Daily at your preferred time
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `manage.py process_recurring_invoices`
7. Start in: `C:\path\to\invoice-generator`

### How It Works

1. The scheduler checks all **active** recurring invoices
2. If `next_invoice_date` is today or earlier, an invoice is generated
3. The invoice is created as a **Draft** with items copied from the template
4. A PDF is automatically generated
5. The `next_invoice_date` advances based on the frequency (weekly/monthly/quarterly/yearly)
6. The process continues until the optional `end_date` is reached

### Disabling the Scheduler

If you don't need automatic recurring invoice generation, you can disable the scheduler service:
```bash
# Run only the web service
docker compose up -d web
```

Or remove/comment out the `scheduler` section in `docker-compose.yml`.

## PDF Invoices

PDFs are generated automatically and include:
- Company logo and details
- Client information
- Invoice number, date, and due date
- Line items with VAT calculations
- Subtotal, VAT total, and grand total
- Bank details for transfers
- Payment link (clickable in PDF)
- Custom payment terms
- Notes
- Footer text

PDFs are stored in `./data/media/invoices/{tax-year}/`

## Troubleshooting

### Static files not loading
```bash
docker compose exec web python manage.py collectstatic --noinput
```

### Database errors after update
```bash
docker compose exec web python manage.py migrate
```

### Permission errors on data directory
```bash
# Linux/macOS
sudo chown -R $USER:$USER ./data
```

### Container won't start
```bash
# Check logs for errors
docker compose logs web

# Rebuild from scratch
docker compose down
docker compose up --build -d
```

### Forgot admin password
```bash
docker compose exec web python manage.py changepassword your@email.com
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (required for production) | Insecure default |
| `DEBUG` | Enable debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list with protocol | `http://localhost:8000` |
| `DJANGO_SUPERUSER_EMAIL` | Auto-create admin with this email | - |
| `DJANGO_SUPERUSER_PASSWORD` | Auto-create admin with this password | - |
| `TZ` | Timezone | `Europe/London` |

## Backup and Restore

### Backup
```bash
# Create backup directory
mkdir -p backups

# Backup database
cp ./data/db/db.sqlite3 ./backups/db-$(date +%Y%m%d).sqlite3

# Backup everything
tar -czvf backups/invoice-generator-$(date +%Y%m%d).tar.gz ./data
```

### Restore
```bash
# Stop the application
docker compose down

# Restore database
cp ./backups/db-YYYYMMDD.sqlite3 ./data/db/db.sqlite3

# Start the application
docker compose up -d
```

## Security Recommendations

For production deployments:

1. **Generate a strong SECRET_KEY** - Never use the default
2. **Set DEBUG=False** - Never run debug mode in production
3. **Use HTTPS** - Put behind a reverse proxy with SSL
4. **Strong passwords** - Use secure passwords for admin accounts
5. **Regular backups** - Back up the data directory regularly
6. **Keep updated** - Update dependencies regularly

## License

This project is licensed under the MIT License.  
See the [LICENSE](license.md) file for details.

## Contributions are welcome.  
Please read [CONTRIBUTING](contributing.md) before submitting a pull request.

## DISCLAIMER
          
This Invoice Generator is provided "as is" without warranty of any kind. If you choose to self-host this software, you do so at your own risk. The developer accepts no responsibility for data loss, inaccuracies, or any issues arising from its use. Always maintain your own backups and verify calculations independently.

<p align="center">
  Made for UK self employed and sole traders<br>
  <a href="https://todiane.com/blog/invoice-generator-open-source-django">Introducing Invoice Generator</a>
</p>