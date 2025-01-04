from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

class Email:
    @staticmethod
    def send_template():
        # TODO: Stop this from being possible to spam and add a try/catch block
        from_addr = os.getenv('TBT_EMAIL_ADDRESS')
        to_addr = 'luke.m.hanna@gmail.com'

        

        # Set up the email headers
        message = MIMEMultipart()
        message['To'] = to_addr
        message['From'] = from_addr
        message['Subject'] = 'Your password reset link for TheBurnTracker' 

        # Attach the email message
        reset_url = 'hi'
        message_text = MIMEText(f'To reset your password go to this link: {reset_url}')
        message.attach(message_text)

        # Send the email
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()

        server.login(
            os.getenv('TBT_EMAIL_ADDRESS'),
            os.getenv('TBT_EMAIL_PASSWORD')
        )
        server.sendmail(from_addr, [to_addr], message.as_string())
        server.quit()

        print('emailed')

if __name__ == '__main__':
    load_dotenv()
    Email.send_template()
