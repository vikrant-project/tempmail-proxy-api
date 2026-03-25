#!/usr/bin/env python3
"""
TempMail.lol Proxy API with JSON Storage
Run this script and access:
- GET /create - Create new temporary email
- GET /check/<token> - Check emails for a token
- GET /history - View all stored emails and logs
"""

from flask import Flask, jsonify, request
import requests
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# JSON file stored in the same directory as this script
SCRIPT_DIR = Path(__file__).parent.absolute()
JSON_FILE = SCRIPT_DIR / "tempmail_data.json"

# TempMail API base URL
API_BASE = "https://api.tempmail.lol/v2"


def load_data():
    """Load existing data from JSON file"""
    if JSON_FILE.exists():
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"emails": [], "errors": []}
    return {"emails": [], "errors": []}


def save_data(data):
    """Save data to JSON file"""
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False


def log_error(error_type, message, details=None):
    """Log error to JSON file"""
    data = load_data()
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "message": message,
        "details": details
    }
    data["errors"].append(error_entry)
    save_data(data)
    return error_entry


@app.route('/create', methods=['GET'])
def create_email():
    """Create a new temporary email address"""
    try:
        # Call TempMail API using POST with proper endpoint
        response = requests.post(
            f"{API_BASE}/inbox/create",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={"domain": None, "prefix": None},
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            error = log_error(
                "API_ERROR",
                f"TempMail API returned status {response.status_code}",
                {"status_code": response.status_code, "response": response.text}
            )
            return jsonify({
                "error": "Failed to create email",
                "details": error
            }), 500
        
        api_data = response.json()
        
        # Extract address and token
        email_address = api_data.get('address')
        token = api_data.get('token')
        
        if not email_address or not token:
            error = log_error(
                "INVALID_RESPONSE",
                "TempMail API response missing address or token",
                {"api_response": api_data}
            )
            return jsonify({
                "error": "Invalid response from TempMail API",
                "details": error
            }), 500
        
        # Load existing data
        data = load_data()
        
        # Create new email entry
        email_entry = {
            "address": email_address,
            "token": token,
            "created_at": datetime.now().isoformat(),
            "total_emails_received": 0,
            "emails": []
        }
        
        # Append to emails list
        data["emails"].append(email_entry)
        
        # Save to JSON
        if save_data(data):
            return jsonify({
                "success": True,
                "address": email_address,
                "token": token,
                "created_at": email_entry["created_at"],
                "message": "Email created and saved to JSON"
            }), 200
        else:
            return jsonify({
                "success": True,
                "address": email_address,
                "token": token,
                "warning": "Email created but failed to save to JSON"
            }), 200
            
    except requests.exceptions.Timeout:
        error = log_error("TIMEOUT", "TempMail API request timed out")
        return jsonify({
            "error": "Request timeout",
            "details": error
        }), 504
        
    except requests.exceptions.ConnectionError:
        error = log_error("CONNECTION_ERROR", "Could not connect to TempMail API")
        return jsonify({
            "error": "Connection error",
            "details": error
        }), 503
        
    except Exception as e:
        error = log_error("UNEXPECTED_ERROR", str(e), {"exception_type": type(e).__name__})
        return jsonify({
            "error": "Unexpected error occurred",
            "details": error
        }), 500


@app.route('/check/<token>', methods=['GET'])
def check_email(token):
    """Check emails for a specific token"""
    try:
        # Call TempMail API
        response = requests.get(
            f"{API_BASE}/inbox",
            params={"token": token},
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 404:
            error = log_error(
                "INVALID_TOKEN",
                f"Token not found: {token}",
                {"token": token}
            )
            return jsonify({
                "error": "Invalid or expired token",
                "details": error
            }), 404
            
        if response.status_code != 200:
            error = log_error(
                "API_ERROR",
                f"TempMail API returned status {response.status_code}",
                {"status_code": response.status_code, "token": token, "response": response.text}
            )
            return jsonify({
                "error": "Failed to check emails",
                "details": error
            }), 500
        
        api_data = response.json()
        emails = api_data.get('emails', [])
        expired = api_data.get('expired', False)
        
        # Format emails
        formatted_emails = []
        for email in emails:
            formatted_email = {
                "from": email.get('from', 'Unknown'),
                "subject": email.get('subject', 'No Subject'),
                "body": email.get('body', ''),
                "html": email.get('html'),
                "date": email.get('date', 'Unknown'),
                "received_at": datetime.now().isoformat()
            }
            formatted_emails.append(formatted_email)
        
        # Update JSON data
        data = load_data()
        
        # Find the email entry with this token
        email_entry = None
        for entry in data["emails"]:
            if entry["token"] == token:
                email_entry = entry
                break
        
        if email_entry:
            # Update existing emails (avoid duplicates by checking subject+from)
            existing_signatures = {
                (e.get('from'), e.get('subject')) for e in email_entry.get('emails', [])
            }
            
            new_emails_added = 0
            for formatted_email in formatted_emails:
                signature = (formatted_email['from'], formatted_email['subject'])
                if signature not in existing_signatures:
                    email_entry['emails'].append(formatted_email)
                    new_emails_added += 1
            
            # Update total count
            email_entry['total_emails_received'] = len(email_entry['emails'])
            email_entry['last_checked'] = datetime.now().isoformat()
            email_entry['expired'] = expired
            
            save_data(data)
            
            return jsonify({
                "success": True,
                "token": token,
                "total_emails": len(formatted_emails),
                "new_emails_added": new_emails_added,
                "expired": expired,
                "emails": formatted_emails
            }), 200
        else:
            # Token not in our records, but still return emails
            return jsonify({
                "success": True,
                "token": token,
                "total_emails": len(formatted_emails),
                "expired": expired,
                "warning": "Token not found in local storage",
                "emails": formatted_emails
            }), 200
            
    except requests.exceptions.Timeout:
        error = log_error("TIMEOUT", f"TempMail API request timed out for token: {token}")
        return jsonify({
            "error": "Request timeout",
            "details": error
        }), 504
        
    except requests.exceptions.ConnectionError:
        error = log_error("CONNECTION_ERROR", "Could not connect to TempMail API")
        return jsonify({
            "error": "Connection error",
            "details": error
        }), 503
        
    except Exception as e:
        error = log_error("UNEXPECTED_ERROR", str(e), {"exception_type": type(e).__name__, "token": token})
        return jsonify({
            "error": "Unexpected error occurred",
            "details": error
        }), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Get all stored email history from JSON"""
    try:
        data = load_data()
        
        # Summary statistics
        total_emails_created = len(data.get("emails", []))
        total_emails_received = sum(
            entry.get("total_emails_received", 0) 
            for entry in data.get("emails", [])
        )
        total_errors = len(data.get("errors", []))
        
        return jsonify({
            "success": True,
            "summary": {
                "total_emails_created": total_emails_created,
                "total_emails_received": total_emails_received,
                "total_errors": total_errors,
                "json_file_location": str(JSON_FILE)
            },
            "emails": data.get("emails", []),
            "errors": data.get("errors", [])
        }), 200
        
    except Exception as e:
        error = log_error("HISTORY_ERROR", str(e), {"exception_type": type(e).__name__})
        return jsonify({
            "error": "Failed to retrieve history",
            "details": error
        }), 500


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        "service": "TempMail.lol Proxy API",
        "version": "1.0",
        "endpoints": {
            "/create": "GET - Create a new temporary email",
            "/check/<token>": "GET - Check emails for a specific token",
            "/history": "GET - View all stored emails and error logs"
        },
        "data_storage": str(JSON_FILE),
        "examples": {
            "create_email": "curl http://YOUR_IP:4500/create",
            "check_email": "curl http://YOUR_IP:4500/check/YOUR_TOKEN",
            "view_history": "curl http://YOUR_IP:4500/history"
        }
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("TempMail.lol Proxy API Starting...")
    print("=" * 60)
    print(f"JSON Data File: {JSON_FILE}")
    print(f"API Endpoints:")
    print(f"  - http://0.0.0.0:4500/create")
    print(f"  - http://0.0.0.0:4500/check/<token>")
    print(f"  - http://0.0.0.0:4500/history")
    print("=" * 60)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=4500, debug=False)
