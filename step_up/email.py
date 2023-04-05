import smtplib
import ssl
from email.message import EmailMessage
from email.mime.text import MIMEText

from flask import url_for

from step_up.database import get_database

EMAIL_PASSWORD = 'Pm6AFaRevudSt5N'
SENDER = 'noreply.stepup.ksu@gmail.com'
SITE_URL = ''


def send_email(to, subject, message):
    # Create empty email object
    email = EmailMessage()
    # Set email info
    email['From'] = SENDER
    email['Subject'] = subject
    # Set the content of the email
    email.set_content(MIMEText(message, 'html'))
    # Set the email destination
    email['To'] = to

    # Create SSL context
    context = ssl.create_default_context()
    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(SENDER, EMAIL_PASSWORD)
        smtp.sendmail(SENDER, email["To"], email.as_string())

    # Reference:
    # https://towardsdatascience.com/how-to-easily-automate-emails-with-python-8b476045c151#bc59
    # User: noreply.stepup.ksu@gmail.com   Pass: Pm6AFaRevudSt5N


def send_approval(userid):
    # Get a handle on the DB
    db = get_database()
    # Get user info
    user = db.execute(
        "SELECT * FROM users WHERE userid = ?", (userid,)
    ).fetchone()

    # Email subject
    subject = 'Account created!'

    # Craft endpoint to be linked in the email
    endpoint = url_for('auth.login')
    # Content to be sent in the email
    message = f"Hello {user['username']},<br><br>Your new account on Step Up has been activated!" \
              f"<br><br><a href='{SITE_URL}{endpoint}'>Click here to log in.</a>" \
              f"<br><br>Regards," \
              f"<br><br>Step Up Team"

    send_email(user["email_address"], subject, message)

