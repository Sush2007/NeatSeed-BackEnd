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

    if not sender_email or not sender_password:
        print("!!! ERROR: Missing MAIL_USERNAME or MAIL_PASSWORD in .env file !!!")
        return False

    subject = "Your NeatSeed Sign-Up Verification Code"
    
    # Professional HTML Template
    body = f"""
    <div style="font-family: Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #10b981; text-align: center;">NeatSeed Security</h2>
        <p style="color: #333; font-size: 16px;">Hello,</p>
        <p style="color: #555; font-size: 16px; line-height: 1.5;">
            Please use the verification code below to complete your sign-up. 
            This code allows you to verify your email address securely.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <span style="display: inline-block; font-size: 32px; font-weight: bold; color: #10b981; letter-spacing: 5px; background: #ecfdf5; padding: 15px 30px; border-radius: 8px; border: 1px solid #10b981;">
                {otp}
            </span>
        </div>
        <p style="color: #888; font-size: 12px; text-align: center;">
            This code will expire in 10 minutes. If you didn't request this, please ignore this email.
        </p>
    </div>
    """

    msg = MIMEMultipart()
    msg['From'] = f"NeatSeed Support <{sender_email}>" # Professional Header
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Use SMTP_SSL for port 465
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print(f"SUCCESS: OTP sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"!!! EMAIL ERROR: {str(e)}")
        return False