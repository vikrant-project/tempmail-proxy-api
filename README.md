# TempMail Proxy API 📬

> A lightweight Flask-based proxy API for [TempMail.lol](https://tempmail.lol) — create disposable emails, check inboxes, and log everything to local JSON storage. Self-hosted and ready to deploy.

---

## ✨ What It Does

This API acts as a clean proxy layer over the TempMail.lol service. It exposes simple HTTP endpoints to create temporary email addresses, poll inboxes, and maintain a persistent local history — all stored in a single JSON file on disk.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **Email Creation** | Instantly generate a disposable email address + token via one GET request |
| **Inbox Polling** | Check received emails for any active token |
| **JSON Persistence** | All emails and errors are logged locally to `tempmail_data.json` |
| **Duplicate Guard** | Avoids re-storing emails already in local history |
| **Error Logging** | Captures API timeouts, connection errors, and unexpected failures with timestamps |
| **Self-Hosted** | Runs on your own server at port `4500` — no external dashboard needed |

---

## 📋 Prerequisites

- **Python 3.8+**
- **pip**
- Network access to `https://api.tempmail.lol`

---

## 🛠 Setup

### 1. Clone the Repository

```bash
git clone https://soulcrack-spoofs-admin@bitbucket.org/soulcrack-spoofs/tempmail-proxy-api.git
cd tempmail-proxy-api
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python app.py
```

Server starts at `http://0.0.0.0:4500`

---

## 🎮 API Endpoints

### `GET /create`
Creates a new temporary email address.

```bash
curl http://YOUR_IP:4500/create
```

**Response:**
```json
{
  "success": true,
  "address": "random123@tempmail.lol",
  "token": "abc123token",
  "created_at": "2025-01-01T12:00:00",
  "message": "Email created and saved to JSON"
}
```

---

### `GET /check/<token>`
Checks inbox for a specific token.

```bash
curl http://YOUR_IP:4500/check/abc123token
```

**Response:**
```json
{
  "success": true,
  "token": "abc123token",
  "total_emails": 2,
  "new_emails_added": 1,
  "expired": false,
  "emails": [...]
}
```

---

### `GET /history`
Returns all stored emails and error logs.

```bash
curl http://YOUR_IP:4500/history
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_emails_created": 10,
    "total_emails_received": 34,
    "total_errors": 1,
    "json_file_location": "/path/to/tempmail_data.json"
  },
  "emails": [...],
  "errors": [...]
}
```

---

### `GET /`
Returns API documentation and available endpoints.

```bash
curl http://YOUR_IP:4500/
```

---

## 🗂 Project Structure

```
tempmail-proxy-api/
├── app.py                  # Main Flask app + all route handlers
├── requirements.txt        # Python dependencies
├── tempmail_data.json      # Auto-generated — stores all emails & logs
└── README.md
```

> `tempmail_data.json` is auto-created on first run. Do not delete it unless you want to reset all history.

---

## ⚙️ How It Works

```
Client (curl / browser)
        │
        ▼
  Flask Proxy API (port 4500)
        │
        ├── POST /inbox/create ──► TempMail.lol API
        │         │
        │    Returns address + token
        │         │
        └── Saves to tempmail_data.json

  GET /check/<token>
        │
        ├── GET /inbox?token=... ──► TempMail.lol API
        │         │
        │    Returns emails list
        │         │
        └── Deduplicates + saves new emails to JSON
```

---

## 🚢 Deployment

### Run in Background (Linux)

```bash
nohup python app.py > output.log 2>&1 &
```

### Run with Screen

```bash
screen -S tempmail
python app.py
# Detach with Ctrl+A then D
```

### Run with PM2

```bash
pm2 start app.py --interpreter python3 --name tempmail-api
```

---

## ⚠️ Legal Disclaimer

This project is intended for **educational purposes and legitimate testing workflows** only (e.g., automated sign-up testing, inbox verification pipelines). Users are responsible for ensuring usage complies with [TempMail.lol's Terms of Service](https://tempmail.lol) and all applicable laws.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

---

<p align="center">Built for developers who need disposable inboxes, fast ⚡</p>