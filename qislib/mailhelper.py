import logging
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class MailHelper:
    def __init__(self, creds, logger=None):
        # {username: "", password: ""}
        self.creds = creds
        self.logger = logger or logging.getLogger(__name__)
        self.server = self.get_mail_server()

    def get_mail_server(self):
        """create mail server and login"""
        try:
            server = smtplib.SMTP("smtp.web.de", 587)
            server.starttls()
            server.login(self.creds.username, self.creds.password)
            return server
        except Exception as e:
            self.logger.error("failed to get mailserver: %s", e)
        return None

    def send_mail(self, receiver, subject, table, fnames=None):
        """send mail to receiver with mailserver server"""
        if not self.server:
            self.logger.error('mail server not specified!')
            return False
        try:
            msg = MIMEMultipart('related')
            msg['From'] = self.creds.username
            msg['To'] = receiver
            msg['Subject'] = subject
            html = """<head>
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>html title</title>
                        <style type="text/css" media="screen">
                            table {border-collapse: collapse;}
                            table, tr, td, th {border: 1px solid black;}
                        </style>
                    </head>
                    <body>
                    """ + table
            if fnames:
                for i in range(len(fnames)):
                    html += '<p><img src="cid:image{}"></p>'.format(i)
            html += "</body>"
            msgHtml = MIMEText(html, 'html')
            msg.attach(msgHtml)
            if fnames:
                for i, fname in enumerate(fnames):
                    img = open(fname, 'rb').read()
                    msgImg = MIMEImage(img, 'png')
                    msgImg.add_header('Content-ID', '<image{}>'.format(i))
                    msg.attach(msgImg)
            self.server.sendmail(self.creds.username,
                                 receiver, msg.as_string())
        except Exception as e:
            self.logger.error("failed to send email: %s", str(e))
            return False
        return True
