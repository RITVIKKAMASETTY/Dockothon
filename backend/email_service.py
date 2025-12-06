import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Email configuration
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)


def send_email(to_email: str, subject: str, body: str, html_body: str = None) -> bool:
    """
    Send an email using SMTP Gmail.
    Returns True if successful, False otherwise.
    Only sends if EMAIL_ENABLED is true.
    """
    if not EMAIL_ENABLED:
        print("Email notifications are disabled")
        return False
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("SMTP credentials not configured")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        
        # Add plain text part
        part1 = MIMEText(body, "plain")
        msg.attach(part1)
        
        # Add HTML part if provided
        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        
        print(f"Email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_new_entry_notification(doctor_email: str, doctor_name: str, patient_name: str, entry_time: str) -> bool:
    """Send notification to doctor about a new entry from a patient."""
    subject = f"New Patient Entry - {patient_name}"
    
    body = f"""
Dear Dr. {doctor_name},

You have a new patient entry from {patient_name}.

Entry Time: {entry_time}

Please log in to Dockothon to view the details.

Best regards,
Dockothon Team
"""
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">🏥 Dockothon</h1>
        </div>
        <div style="background: #fff; padding: 20px; border: 1px solid #eee; border-radius: 0 0 10px 10px;">
            <h2 style="color: #667eea;">New Patient Entry</h2>
            <p>Dear Dr. <strong>{doctor_name}</strong>,</p>
            <p>You have a new patient entry from <strong>{patient_name}</strong>.</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Entry Time:</strong> {entry_time}</p>
            </div>
            <p>Please log in to Dockothon to view the details.</p>
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Best regards,<br>
                <strong>Dockothon Team</strong>
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return send_email(doctor_email, subject, body, html_body)
