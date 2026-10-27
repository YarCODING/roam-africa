# Roam Africa

Full-stack Django application for booking tours and safari expeditions across Africa.

## Features

* Dynamic tour search and filtering (HTMX)
* Multi-currency booking and payment processing (django-money, Stripe)
* Modern admin dashboard and user management (django-unfold, django-hijack, simple-history)
* Authentication, social accounts, and bot protection (django-allauth, Cloudflare Turnstile)
* Automated PDF ticket generation with QR codes (ReportLab, qrcode)
* Background task queue & scheduled jobs (Celery, django-celery-beat, Flower)
* Integrated Telegram bot assistant (aiogram 3)
* Transactional & system email processing (Gmail SMTP & Brevo)
* Data import/export and audit logging (django-import-export, django-simple-history)
* Travel blog and newsletter module

## Tech Stack

* **Core & Backend:** Python 3.14, Django 6.0.9, Celery, Uvicorn
* **Frontend:** Tailwind CSS, daisyUI, HTMX
* **Admin & Auth:** django-unfold, django-allauth, django-hijack, django-turnstile
* **Database & Storage:** Supabase PostgreSQL, Supabase S3 (django-storages, boto3)
* **Task Broker & Monitoring:** Upstash Redis, CloudAMQP RabbitMQ
* **Email & Notifications:** Brevo, Gmail SMTP, aiogram 3 (Telegram)
* **Deployment:** Render

## Author

* Yaroslav Zaitsev ([@YarCODING](https://github.com/YarCODING))
* Live Demo: [roamafrica.onrender.com](https://roamafrica.onrender.com/)
