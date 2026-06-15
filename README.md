# Missionary Meal Calendar

A Django-based missionary meal calendar, designed for ward members to sign up to feed missionaries. Built with Django and HTMX for a modern, responsive user experience.

## Features

- **Monthly Calendar**: View current and next month's availability.
- **Easy Sign-up**: Interactive HTMX-powered modals for quick sign-ups.
- **Manage Availability**: Ability to mark dates as unavailable.
- **Email Notifications**: 
    - Immediate alerts to missionaries for sign-ups/cancellations.
    - Automated reminders to users the evening before their appointment.
    - Weekly summary emails sent to missionaries every Sunday.
- **Heroku Ready**: Fully configured for deployment on Heroku with WhiteNoise for static files and PostgreSQL support.

## Tech Stack

- **Backend**: Django 6.0+
- **Frontend**: HTML5, CSS3, HTMX 2.0
- **Database**: SQLite (Local), PostgreSQL (Production)
- **Deployment**: Heroku (but others can be used)
- **Emails**: Postmark (Production), Mailtrap (Testing)

## Local Development Setup

### 1. Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`

### 2. Installation
Clone the repository and install dependencies:
```bash
uv sync
```

### 3. Environment Variables
Create a `.env` file in the project root and fill in the values (refer to `.env.example`):
```bash
cp .env.example .env
```

### 4. Database Setup
Run migrations to set up your local SQLite database:
```bash
python manage.py migrate
```

### 5. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

## Email Configuration

The system uses environment variables to manage email backends.

### Testing (Mailtrap)
To test emails without sending them to real users, use Mailtrap:
1. Set `DJANGO_EMAIL_HOST` to `sandbox.smtp.mailtrap.io`.
2. Set your Mailtrap credentials in `.env`.

### Production (Postmark)
For production, the app is optimized for Postmark:
1. Set `DJANGO_EMAIL_HOST` to `smtp.postmarkapp.com`.
2. Use your Postmark Server API Token as the username and password.
3. Ensure `DJANGO_DEFAULT_FROM_EMAIL` is a verified sender signature in Postmark.

## Background Tasks

Automated reminders and summaries are handled by a management command:
```bash
python manage.py send_notifications
```

### Manual Testing
You can manually test the appearance of all email types (Reminders, Updates, and Summaries) by running the command with the `--test` flag:
```bash
python manage.py send_notifications --test
```
This will send sample versions of all emails to your configured `MISSIONARY_EMAIL`.

## Deployment to Heroku

1. Create a Heroku app: `heroku create your-app-name`
2. Add Postgres: `heroku addons:create heroku-postgresql:essential-0`
3. Set your environment variables: `heroku config:set DJANGO_SECRET_KEY=...` (see `.env.example`)
4. Push to Heroku: `git push heroku main`
5. Run migrations: `heroku run python manage.py migrate`
6. Set up the Heroku Scheduler for the `send_notifications` command.

### Scheduling emails
Emails need to be sent by using some sort of cron job.
To automate these emails on Heroku, use the **Heroku Scheduler** add-on:

1. **Install the Add-on**:
   ```bash
   heroku addons:create scheduler:standard
   ```
2. **Open the Scheduler Dashboard**:
   ```bash
   heroku addons:open scheduler
   ```
3. **Add a New Job**:
   - **Command**: `python manage.py send_notifications`
   - **Frequency**: Daily
   - **Time**: Select your preferred evening time (e.g., 6:00 PM or 00:00 UTC).
4. **Save**: The command will now run once a day, sending reminders and (on Sundays) the weekly summary.


## License
MIT
