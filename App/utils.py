import hashlib
import smtplib
import random
import string
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv # Ensure you have python-dotenv installed

# Explicitly load .env file
load_dotenv()

def hash_password(password):
    if not password:
        return None
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(recipient_email, otp):
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    # 1. Check if credentials exist
    if not sender_email or not sender_password:
        print("!!! EMAIL ERROR: Missing MAIL_USERNAME or MAIL_PASSWORD in .env !!!")
        return False

    subject = "NeatSeed Verification Code"
    body = f"Your OTP is: {otp}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # 2. Use safe connection block
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print(f"SUCCESS: Email sent to {recipient_email}")
        return True
    except Exception as e:
        # 3. Print the actual error so you can see it in your terminal
        print(f"!!! SMTP ERROR: {str(e)}")
        return False