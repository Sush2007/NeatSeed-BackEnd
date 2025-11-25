import hashlib
import smtplib
import random
import string
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def hash_password(password):
    """Simple password hashing using SHA256"""
    if not password:
        return None
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    """Generates a random 6-digit numeric OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(recipient_email, otp):
    """
    Sends a 6-digit OTP to the specified email using Gmail SMTP.
    Requires MAIL_USERNAME and MAIL_PASSWORD (App Password) in .env
    """
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("Error: Missing email credentials in .env file.")
        return False

    subject = "NeatSeed Verification Code"
    
    # improved HTML email body for better presentation
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
          <h2 style="color: #16a34a; text-align: center;">NeatSeed Verification</h2>
          <p>Hello,</p>
          <p>Thank you for signing up with NeatSeed. Please use the following One-Time Password (OTP) to verify your email address:</p>
          <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #16a34a; background-color: #f0fdf4; padding: 10px 20px; border-radius: 5px; border: 1px solid #bbf7d0;">
              {otp}
            </span>
          </div>
          <p>This code is valid for <strong>5 minutes</strong>.</p>
          <p style="font-size: 12px; color: #777; text-align: center; margin-top: 30px;">
            If you did not request this code, please ignore this email.
          </p>
        </div>
      </body>
    </html>"""

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"SUCCESS: OTP sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to send email. Reason: {e}")
        return False