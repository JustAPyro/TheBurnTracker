from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

class Email:
    @staticmethod
    def send_template(template: str, target_email: str, format: dict):
        # TODO: Stop this from being possible to spam and add a try/catch block

        # Set up the email headers
        message = MIMEMultipart()
        message['To'] = target_email
        message['From'] = os.getenv('TBT_EMAIL_ADDRESS')
        message['Subject'] = 'Your password reset link for TheBurnTracker' 

        # Load the html template
        with open('app/communications/email_pwd_reset.html', 'r') as file:
            html = file.read()

        # Populate the formatting
        for key, value in format.items():
            html = html.replace('{{'+key+'}}', value)

        # Attach the email message
        message_text = MIMEText(html, 'html')
        message.attach(message_text)

        # Send the email
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()

        server.login(
            os.getenv('TBT_EMAIL_ADDRESS'),
            os.getenv('TBT_EMAIL_PASSWORD')
        )
        server.sendmail(os.getenv('TBT_EMAIL_ADDRESS'), [target_email], message.as_string())
        server.quit()

        print('emailed')

if __name__ == '__main__':
    load_dotenv()
    Email.send_template('email_pwd_reset.html', 'luke.m.hanna@gmail.com', {
        'username': 'Luka'
    })
