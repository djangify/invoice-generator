# Contributing to Invoice Generator

Thanks for helping. Invoice Generator is open source under the
[MIT License](LICENSE.md). By sending a contribution you agree
that it can be distributed under that same licence.

## Scope

Invoice Generator is a **local, single-user, Windows** invoicing tool for UK sole traders:
one copy, one person, one business. That is how it works today. Other operating systems are
not supported and have not been tested. Please do not send changes for cloud hosting or
server deployment.

Several larger ideas are open to contributors (below), including multi-business support and
other currencies and tax years. Open an issue to talk about the approach before you start on
any of them.

## Ideas to work on

Pick one, open an issue to say you are working on it, then send a pull request.

**Larger changes (discuss first)**

1. **Multi-business support.** One person invoices from several businesses in one copy, with
   a way to switch between them. Today there is a single set of company settings (the code
   reads `CompanySettings.objects.first()`), and clients, invoices and recurring invoices do
   not belong to a business. It needs a business link on those models, a data migration for
   existing data, a switcher in the navigation, and the PDF, the email text and the
   dashboard following the chosen business.
2. **Other currencies and tax years.** The tax year (6 April to 5 April) is built into
   `InvoiceYear` in `invoices/models.py`, and the `£` sign is written directly into
   `invoices/pdf_generator.py`, `invoices/admin.py`, `invoices/views/client.py`, the email
   text in `invoices/models.py` and most templates. A currency setting and a tax year start
   date would make the app usable outside the UK. It needs a way to move existing invoices
   to the new years, and tests for dates either side of the new year boundary (the UK
   ones are in `invoices/tests.py`).
3. **Send the email from the app.** The **Email Invoice** button only opens the user's own
   email program, so the PDF has to be attached by hand. Sending from the app with the PDF
   attached would need SMTP settings, with the password stored encrypted and never shown
   again, and clear error messages when sending fails.

**Medium**

4. **Part payments.** Today an invoice is either paid or not. Recording a payment amount and
   date, and showing the balance still owed, would help with deposits and instalments.
5. **Back up now, and restore.** A button in Settings to make a backup of the `data` folder
   straight away, and a way to restore one. Today both are done by copying files by hand.

**Good first issues**

6. **Screenshots for the README.** The README has one image. Clear screenshots of the
   dashboard, an invoice and the PDF would help new users.

## Set up

```powershell
git clone https://github.com/djangify/invoice-generator.git
cd invoice-generator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_default_user   # prints a random password
python manage.py runserver
```

## Before you open a pull request

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

All tests must pass. Add a test for any bug you fix or behaviour you add.
Do not commit your `.env`, your `data/` folder, your virtual environment or any real client,
invoice or bank details.

## Changing the CSS

`static/css/output.css` is generated from `static/src/input.css` with Tailwind:

```powershell
npm install
npx @tailwindcss/cli -i static/src/input.css -o static/css/output.css
```

Commit the regenerated `output.css`.
