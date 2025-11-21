# Transaction Service — Django + MongoDB + Celery

A backend service built with **Django**, **Django REST Framework**, **MongoDB**, and **Celery**, designed to:

1. Process a large volume of transaction records
2. Generate **daily**, **weekly**, and **monthly** aggregated summaries
3. Expose optimized APIs that read from a cached summary collection
4. Provide a **centralized notification system** with async sending logic
5. Run fully inside **Docker Compose** (web + celery + redis + mongodb)

---

## 🚀 Features

### ✅ 1. Transaction Aggregation

* Reads raw transactions from MongoDB (main `transactions` collection).
* Aggregates totals by:

  * **Daily**
  * **Weekly**
  * **Monthly**
* Stores results in a dedicated summary collection for fast, lightweight queries.
* Designed to work efficiently even when raw transactions grow large.

---

### ✅ 2. Summary API (Optimized)

Single endpoint:

```http
GET /api/transactions/summary?mode=daily|weekly|monthly&type=amount|count&merchant_id=...
```

Parameters:

* `mode`: `daily`, `weekly`, or `monthly`
* `type`: `amount` or `count`
* `merchant_id` (optional): filter by merchant

Response example:

```json
[
  { "key": "1403/04/04", "value": 120000 },
  { "key": "1403/04/05", "value": 56000 }
]
```

This API **never** scans the big raw transactions collection directly; it only reads from precomputed summaries.

---

### ✅ 3. Notification System

A modular, async notification architecture:

* Stores one `Notification` document per logical notification (e.g. *"Daily summary for merchant X"*).
* For each medium (e.g. SMS, Email, Telegram), a `NotificationLog` row is created.
* A Celery worker processes logs asynchronously and simulates sending messages.
* Easy to plug in real senders later (KavehNegar, SMTP, Telegram bot, etc.) via `senders.py`.

Flow:

1. API creates a `Notification` + related `NotificationLog` rows.
2. Celery task `send_notification_task(notification_id)` is queued.
3. Worker:

   * Fetches the notification + logs
   * Iterates logs and "sends" via a strategy per medium
   * Updates `status`, `attempts`, `last_attempt_at`, `error_message`
4. Notification status becomes `sent` only if all logs succeed.

---

### ✅ 4. Asynchronous Processing with Celery

* Uses **Redis** as both **broker** and **result backend**:

  * `redis://redis:6379/0` (broker)
  * `redis://redis:6379/1` (results)
* Celery is configured in `transaction_service/celery.py`.
* Tasks are auto-discovered from all Django apps (e.g. `notifications.tasks`).

---

## 🐳 Running with Docker

Build and start all services:

```bash
docker compose up --build
```

This will start:

* `web` → Django app (REST API)
* `celery` → Celery worker
* `redis` → Celery broker / result backend
* `db` → MongoDB

Stop everything:

```bash
docker compose down
```

---

## 🔁 Rebuilding Transaction Summaries

When you need to (re)generate the `summary_transaction` collection from raw transactions, run:

```bash
docker compose exec web python manage.py rebuild_summaries --truncate
```

* `--truncate` clears old summary data before rebuilding.
* Safely iterates through raw transactions and writes aggregated data.

---

## 🔔 Example Notification Flow

1. **Create notification via API** (example payload):

   ```json
   {
     "user_id": "12345",
     "title": "Daily Transaction Summary",
     "body": "Your total settled amount for today is 490000 Rials.",
     "channels": ["sms", "email"]
   }
   ```

2. **What happens internally:**

   * `Notification` is saved.
   * `NotificationLog` entries are created for each channel.
   * Celery task `send_notification_task(notification_id)` is enqueued.

3. **Celery worker:**

   * Loads the notification and logs.
   * For now: just prints a “fake send” log for each medium.
   * Marks logs as `success` and the notification as `sent`.


---

## 🧱 Tech Stack

* **Language**: Python 3.11
* **Framework**: Django, Django REST Framework
* **Database**: MongoDB (via `djongo`)
* **Async Worker**: Celery
* **Broker / Backend**: Redis
* **Containerization**: Docker & Docker Compose

---

## 📝 Testing & Local Development

### Run tests

```bash
docker compose exec web python manage.py test
```

### Running Django without Docker (optional)

If you want to run locally:

```bash
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=transaction_service.settings
python manage.py runserver
```

Make sure MongoDB and Redis are running locally or update the settings accordingly.
