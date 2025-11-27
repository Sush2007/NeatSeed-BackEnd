import hashlib
import random
import string
import os
import requests 
from dotenv import load_dotenv

load_dotenv()

def hash_password(password):
    if not password: return None
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(recipient_email, otp):
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("SENDER_EMAIL")

    if not api_key:
        print("!!! ERROR: BREVO_API_KEY missing.")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"email": sender_email, "name": "NeatSeed App"},
        "to": [{"email": recipient_email}],
        "subject": "NeatSeed Verification Code",
        "htmlContent": f"""
            <div style="font-family: Arial; padding: 20px;">
                <h2>Verify your Account</h2>
                <p>Your OTP is: <strong style="font-size: 24px; color: green;">{otp}</strong></p>
            </div>
        """
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 201:
            print(f"SUCCESS: Email sent to {recipient_email}")
            return True
        else:
            print(f"!!! BREVO ERROR: {response.text}")
            return False
    except Exception as e:
        print(f"!!! NETWORK ERROR: {str(e)}")
        return False