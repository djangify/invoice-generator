
# Invoice Generator

A Django application you run on your own computer for creating and managing invoices, tracking payments, and generating professional PDFs. Designed for UK tax year tracking (April to April).


<p align="center">
  <a href="https://www.djangoproject.com/">
    <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  </a>
  
  <a href="https://tailwindcss.com/">
    <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS">
  </a>

  <img src="https://img.shields.io/badge/Database-SQLite--First-003B57?style=for-the-badge" alt="SQLite First">


  <img src="https://img.shields.io/badge/Hosting-Self--Hosted--Ready-4B5563?style=for-the-badge" alt="Self Hosted Ready">

  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge" alt="Windows">

</p>

## Features

- **Client Management** - Add, edit, and delete clients with full contact and VAT details
- **Invoice Creation** - Create invoices with multiple line items, VAT calculations, and custom notes
- **PDF Generation** - Professional PDF invoices with company branding, bank details, and payment links
- **Recurring Invoices** - Set up weekly, monthly, quarterly, or yearly recurring invoice templates
- **Tax Year Tracking** - Organise invoices by UK tax year (6 April to 5 April)
- **Quick Actions** - Mark invoices as Sent or Paid with one click
- **Overdue Tracking** - Sent invoices past their due date are marked Overdue automatically
- **CSV Export** - Download a tax year's invoices (or just one status) for your accountant or a spreadsheet
- **Duplicate Invoices** - Clone existing invoices for repeat billing
- **Email Invoice** - One click opens your email program with a ready-written message to the client (attach the PDF and send)
- **Client History** - View all invoices for a specific client with totals and PDF export
- **Payment Integration** - Add Stripe or PayPal payment links to invoices

**Links:** [Product page](https://www.dianecorriette.com/shop/product/invoice-generator-software/) · [Download and setup guide](https://www.dianecorriette.com/docs/invoice-generator-download-and-setup-guide/) · [Latest release](https://github.com/djangify/invoice-generator/releases/latest) · [Introducing Invoice Generator](https://www.dianecorriette.com/blog/invoice-generator-open-source-django/)

## Requirements

- Windows 10 or 11
- Python 3.12 or newer
- Node.js, only if you change the design (the built CSS is included)

## Installation

Open PowerShell and run these steps once. There is also a step-by-step
[download and setup guide](https://www.dianecorriette.com/docs/invoice-generator-download-and-setup-guide/) on the website.

### 1. Get the code

Download the zip from the [latest release](https://github.com/djangify/invoice-generator/releases/latest) and unzip it, or use Git:

```powershell
git clone https://github.com/djangify/invoice-generator.git
cd invoice-generator
```

### 2. Create a virtual environment and install

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Settings (optional)

```powershell
copy .env.example .env
```

For normal use you do not need to change anything in `.env`. The app creates its own
secret key the first time it runs (saved in `data/secret_key.txt`). Open `.env` only if you
want to set your own login email, timezone or email settings. Every setting is explained in
the file.

### 4. Create the database and your first login

```powershell
python manage.py migrate
python manage.py create_default_user
```

The second command prints a random password for your first login (email `admin@example.com`,
or the `DJANGO_SUPERUSER_EMAIL` you set in `.env`) and saves the same details in
`data/first_login.txt`. Log in, change your password on the password change page, then delete
`data/first_login.txt`.

### 5. Run the app

Double-click `start.bat` in the `invoice-generator` folder. It updates the database, creates
your login if it does not exist yet, and starts the app. Or run the commands yourself:

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in. The admin panel is at http://127.0.0.1:8000/admin.

### Starting it again later

Double-click `start.bat`. Close its window, or press Ctrl+C in it, to stop the app.

### Forgot your password?

Give the login a new random password (shown on screen and saved to `data/first_login.txt`):

```powershell
python manage.py create_default_user --reset
```

### Updating to a newer version

Check the [releases page](https://github.com/djangify/invoice-generator/releases) for the latest version.
Unzip the new release into a new folder, copy your old `data` folder into it, then follow the
installation steps above. Keep the old folder until you have checked your invoices look right.

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
├── secret_key.txt      # Generated secret key (keep private)
└── first_login.txt     # First login details (delete after changing your password)
```

**Important**: Back up the `./data/` directory regularly to prevent data loss. It holds your
invoices, client details and bank details, so keep the backups private.

## Invoice Workflow

1. **Draft** - Invoice is created but not yet sent
2. **Sent** - Invoice has been sent to the client
3. **Paid** - Client has paid the invoice
4. **Overdue** - A sent invoice that is past its due date. This is set for you whenever you open the dashboard or invoice list, and each time the daily recurring invoice task runs. Drafts are never marked overdue

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

Recurring invoices are created by running `run-recurring.bat`, so set Windows Task Scheduler to
run it every day. The app does not need to be open for this. The same run also marks overdue
invoices, and adds what it did to `data\recurring.log`.

**Using Task Scheduler:**
1. Open Task Scheduler
2. Create a Basic Task
3. Set trigger to Daily at your preferred time
4. Action: Start a program
5. Program: `C:\path\to\invoice-generator\run-recurring.bat`
6. Start in: `C:\path\to\invoice-generator`

**To run it by hand:**
```powershell
python manage.py process_recurring_invoices
```

**To see what would be generated (dry run):**
```powershell
python manage.py process_recurring_invoices --dry-run
```

### How It Works

1. The command checks all **active** recurring invoices
2. If `next_invoice_date` is today or earlier, an invoice is generated
3. The invoice is created as a **Draft** with items copied from the template
4. A PDF is automatically generated
5. The `next_invoice_date` advances based on the frequency (weekly/monthly/quarterly/yearly)
6. The process continues until the optional `end_date` is reached

If you do not need automatic generation, do not set up the Task Scheduler task. You can still use **Generate Invoice Now** on each recurring invoice.

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
```powershell
python manage.py collectstatic --noinput
```

### Database errors after an update
```powershell
python manage.py migrate
```

### The app will not start
Check that the virtual environment is active (you should see `(venv)` at the start of the
line) and that the packages are installed:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Forgot admin password
```powershell
python manage.py create_default_user --reset
```
This gives the login a new random password (shown on screen and saved to `data/first_login.txt`).
The "forgot password" email only works if you have set the `EMAIL_HOST` settings in `.env`.

## Environment Variables

All optional. See `.env.example` for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated once, saved in `data/secret_key.txt` |
| `DEBUG` | Detailed error pages (development only) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `DJANGO_SUPERUSER_EMAIL` | Email for the first login | `admin@example.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Your own first password (not recommended) | Random, saved to `data/first_login.txt` |
| `TZ` | Timezone | `Europe/London` |
| `EMAIL_HOST` and related | SMTP settings for password-reset emails | Emails print to the console |

## Backup and Restore

### Backup
Stop the app first (Ctrl+C) so the database file is not being written to.

```powershell
# Create the backup folder and a dated copy of everything in data
mkdir backups
Copy-Item -Recurse .\data ".\backups\data-$(Get-Date -Format yyyyMMdd)"
```

### Restore
```powershell
# Stop the app (Ctrl+C), then replace data with the backup you want (change the date)
Remove-Item -Recurse -Force .\data
Copy-Item -Recurse .\backups\data-YYYYMMDD .\data
```

## Security Recommendations

1. **Keep `DEBUG=False`** - Never run debug mode
2. **Keep `data/secret_key.txt` private** - or set your own `SECRET_KEY`
3. **Strong passwords** - Change the generated password and use a strong one
4. **Uploads are checked** - The logo upload is verified as a real image, limited in size and dimensions, and renamed; uploaded files are only served to logged-in users
5. **Regular backups** - Back up the `data` folder regularly and keep the copies private, as they hold client and bank details
6. **Keep updated** - Update dependencies regularly
7. **Built for your own computer** - The app is designed and tested for running on your own machine

## Self-hosting

You can host Invoice Generator on a server of your own if you choose to. It is an ordinary Django app, so the usual Django deployment steps apply. That setup is not covered here and is not supported. If you do it, you are responsible for the server, HTTPS, `ALLOWED_HOSTS`, firewall and backups, because the app holds client and bank details.

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE.md) file for details.

## Contributions are welcome.  
Please read [CONTRIBUTING](CONTRIBUTING.md) before submitting a pull request.

## DISCLAIMER
          
This Invoice Generator is provided "as is" without warranty of any kind. If you choose to run or self-host this software, you do so at your own risk. The developer accepts no responsibility for data loss, inaccuracies, or any issues arising from its use. Always maintain your own backups and verify calculations independently.

<p align="center">
  Made for UK self employed and sole traders<br>
  <a href="https://www.dianecorriette.com/blog/invoice-generator-open-source-django/">Introducing Invoice Generator</a>
</p>

Maintained by [Diane Corriette](https://github.com/todiane) · [dianecorriette.com](https://www.dianecorriette.com)

[Buy Me A Tea](https://tips.todiane.com/)
