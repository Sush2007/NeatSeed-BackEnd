import hashlib
import smtplib
import random
import string
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def hash_password(password):
    if not password: return None
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(recipient_email, otp):
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    # 1. Check Variables
    if not sender_email or not sender_password:
        print(f"!!! ERROR: Creds missing. OTP for {recipient_email} is {otp}")
        return False 

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "NeatSeed Verification"
    msg.attach(MIMEText(f"Your OTP is: {otp}", 'html'))

    try:
        # 2. CONNECT WITH TIMEOUT (The Fix)
        # We use Port 587 with STARTTLS (Better for Cloud Servers)
        # timeout=5 ensures it fails FAST if it gets stuck, preventing Worker Timeout
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=5) as server:
            server.ehlo() # Identify ourselves
            server.starttls() # Secure the connection
            server.ehlo() # Re-identify as encrypted
            
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            
        print(f"SUCCESS: Email sent to {recipient_email}")
        return True

    except Exception as e:
        # 3. Catch the error (now that we have a timeout, this will actually run!)
        print(f"!!! EMAIL ERROR (Ignored): {str(e)}")
        return False