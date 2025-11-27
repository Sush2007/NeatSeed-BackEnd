import smtplib
import os
import random
import string
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 1. FORCE LOAD ENV VARIABLES
load_dotenv()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(recipient_email, otp):
    # 2. DEBUGGING: Print credentials to terminal (Check your terminal when you run this!)
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")
    
    print(f"DEBUG: Attempting to send email from {sender_email}...")

    if not sender_email or not sender_password:
        print("!!! ERROR: MAIL_USERNAME or MAIL_PASSWORD is missing in .env !!!")
        return False

    subject = "Your NeatSeed Verification Code"
    
    # Professional HTML Template
    body = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2E7D32;">Verify your NeatSeed Account</h2>
        <p>Hello,</p>
        <p>Your verification code is:</p>
        <h1 style="background-color: #f1f8e9; padding: 10px; display: inline-block; color: #1b5e20; letter-spacing: 5px;">{otp}</h1>
        <p>This code expires in 10 minutes.</p>
    </div>
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # 3. USE SSL (Port 465) - More reliable for Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print(f"SUCCESS: Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"!!! EMAIL FAILED: {str(e)}")
        return False