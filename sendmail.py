import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class SendMail:
    def __init__(self, sender_email, password):
        self.sender_email = sender_email
        self.password = password
        self.server = None
    
    def login(self):
        if self.server:
            print("Already logged in")
            return
        try:
            self.server = smtplib.SMTP("smtp.web.de", 587)
            self.server.starttls()
            self.server.login(self.sender_email, self.password)
        except Exception:
            return False
        return True

    def sendMail(self, receiver, subject, message):
        if not self.server:
            if not self.login():
                return False
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = receiver
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            self.server.sendmail(self.sender_email, receiver, msg.as_string())
        except Exception:
            return False
        return True
    
    def logout(self):
        self.server.quit()