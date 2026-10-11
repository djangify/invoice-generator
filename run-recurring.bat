@echo off
rem Run by Windows Task Scheduler (see README.md). Creates any recurring invoices that are
rem due and marks unpaid invoices overdue. The result is added to data\recurring.log.
cd /d "%~dp0"
if not exist data mkdir data
venv\Scripts\python.exe manage.py process_recurring_invoices >> data\recurring.log 2>&1
