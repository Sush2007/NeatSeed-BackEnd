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

    # 1. Check if variables exist
    if not sender_email or not sender_password:
        print(f"!!! ERROR: Creds missing. OTP for {recipient_email} is {otp}")
        return False 
    

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "NeatSeed Verification"
    msg.attach(MIMEText(f"Your OTP is: {otp}", 'html'))

    try:
        # 2. Try to send (Catch crashes)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"SUCCESS: Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"!!! EMAIL ERROR (Ignored): {str(e)}")
        # Return False so the app keeps running and redirects the user
        return False