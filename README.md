# 💊 MedStock Pro (MedShop)

A pharmacy inventory web app. It tracks medicines, shows what is expired, expiring soon, low or out of stock, and sends an automatic daily email alert so nothing goes unnoticed.

**Stack:** Python · Flask · MongoDB Atlas (PyMongo) · Jinja2 templates · SMTP (Gmail)

---

## Features

- **Login-protected dashboard** with live counts: total, in stock, low stock, expired
- **Medicine management (CRUD):** add, edit, delete, with server-side validation
- **Search and filters:** search by name or manufacturer; filter by *low stock*, *expired* or *expiring within 30 days*
- **Live search API:** `GET /api/search?q=...` returns JSON
- **Email alerts:** a styled HTML email listing out-of-stock, expired, low-stock and expiring-soon medicines
- **Automatic daily alert** sent by a background scheduler at a configurable time
- **Settings page** to configure the Gmail account, recipient and alert time
- **Responsive dark UI:** sidebar navigation, tables on desktop, cards on mobile

---

## Architecture

```
                    ┌──────────────────────────┐
   Browser  ──────► │  app.py (Flask routes)   │ ──────►  MongoDB Atlas
                    └───────┬──────────────────┘          (medicines collection)
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     notifier.py                   scheduler.py
     - get_alerts()                - background thread
     - builds HTML email           - checks every 60s
     - sends via Gmail SMTP        - sends once per day
```

| File | Responsibility |
|---|---|
| `app.py` | Routes, login, CRUD, search, dashboard, settings |
| `database.py` | MongoDB connection (`get_db`, `init_db`) |
| `notifier.py` | Finds items needing attention, builds and sends the alert email |
| `scheduler.py` | Daily alert thread with a "last sent" guard to prevent duplicates |
| `templates/` | Jinja2 pages: `base`, `login`, `dashboard`, `medicines`, `add_medicine`, `settings` |
| `Procfile` | Start command for hosting platforms (`python app.py`) |

### Data model (`medicines` collection)

| Field | Type | Notes |
|---|---|---|
| `name` | string | required |
| `manufacturer` | string | |
| `category` | string | |
| `price` | float | in ₹ |
| `quantity` | int | units in stock |
| `expiry_date` | string | ISO format `YYYY-MM-DD` |
| `description` | string | |
| `created_at` / `updated_at` | ISO datetime string | |

---

## How it works

**Stock and expiry rules**

- *Low stock:* quantity ≤ 10
- *Out of stock:* quantity = 0
- *Expired:* `expiry_date` is before today
- *Expiring soon:* expires within the next 30 days

Dates are stored as ISO strings, so range checks in MongoDB are simple string comparisons (`$lt`, `$gte`, `$lte`).

**Alert flow**

1. `scheduler.py` starts a daemon thread when the app launches.
2. Every 60 seconds it checks whether the current time matches the alert time and whether an email was already sent today.
3. If it is time, `notifier.get_alerts()` runs four queries and groups the results.
4. If anything needs attention, `send_alert_email()` sends a plain-text and HTML email through Gmail SMTP over SSL (port 465).

**Authentication:** a `@login_required` decorator checks the Flask session on every protected route.

---

## Getting started

### Prerequisites
- Python 3.9+
- A MongoDB Atlas cluster (free tier works)
- *(Optional)* a Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) for email alerts

### Install and run

```bash
git clone <your-repo-url>
cd medshop-main
pip install -r requirements.txt

# set your connection string (Windows: use `set` instead of `export`)
export MONGO_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"

python app.py
```

Open http://localhost:5000.

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `MONGO_URI` | Yes | MongoDB Atlas connection string |
| `GMAIL_ADDRESS` | For email | Sender Gmail address |
| `GMAIL_PASSWORD` | For email | Gmail App Password |
| `NOTIFY_EMAIL` | For email | Where alerts are sent |
| `ALERT_HOUR` / `ALERT_MINUTE` | No | Daily alert time (default 09:00) |
| `PORT` | No | Server port (default 5000) |

Email settings can also be entered on the **Email Alerts** page inside the app.

### Demo login

`admin` / `admin123` (demo credentials, see limitations below)

---

## Routes

| Route | Method | Description |
|---|---|---|
| `/login`, `/logout` | GET, POST | Sign in and out |
| `/` | GET | Dashboard |
| `/medicines` | GET | List with `?search=` and `?filter=low\|expired\|expiring` |
| `/medicines/add` | GET, POST | Add a medicine |
| `/medicines/edit/<id>` | GET, POST | Edit a medicine |
| `/medicines/delete/<id>` | POST | Delete a medicine |
| `/api/search?q=` | GET | JSON search results |
| `/send-alert` | POST | Send the alert email now |
| `/settings` | GET, POST | Configure email and alert time |

---

## Design decisions

- **Flask with server-side templates:** the app is small, so a full front-end framework was unnecessary.
- **MongoDB:** each medicine is an independent document and no joins are needed.
- **Custom scheduler thread:** no extra dependency, and the "last sent" date prevents duplicate emails.
- **Background thread and `app.app_context()`:** lets the scheduler reuse the same code as the web routes.
- **Two email parts (plain text and HTML):** works in every email client.

---

## Known limitations and next steps

These are deliberate scope limits for this version, and the first things I would improve:

- **Authentication:** a single hardcoded demo admin. Next: hashed passwords, multiple users and roles, and a secret key from the environment.
- **CSRF protection** on forms (for example Flask-WTF).
- **Settings persistence:** email settings live in process memory and reset on restart. Next: store them in the database.
- **Scheduler in production:** the thread runs once per worker, so with several workers it could send duplicates. Next: a cron job, or APScheduler with a lock.
- **Search input** is passed to MongoDB `$regex` unescaped. Next: `re.escape()`.
- **Database connection:** a new `MongoClient` is created on every call. Next: share one client.
- **Testing and pagination:** add automated tests and paginate the medicines list.
- **Front-end:** a React component for live search using the existing `/api/search`.

---

## Author

**Ravi Dhiman**
