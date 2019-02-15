import json
import logging
import logging.config
import os
import pickle
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import SimpleNamespace as Namespace

import requests
from bs4 import BeautifulSoup as bs
from prettytable import PrettyTable

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36"
headers = {
    'User-Agent': USER_AGENT,
    'Accept':
    'modul/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.5'
}

logger = logging.getLogger(__name__)


class grade:
    """grade class"""
    def __init__(self, nummer, modul, semester, note):
        self.nummer = int(nummer)
        self.modul = modul
        self.semester = semester
        self.note = float(note.replace(',', '.')) if note else note

    def get_as_list(self):
        """return attributes as ordered list"""
        return [self.nummer, self.modul, self.semester, self.note]

    def __eq__(self, obj):
        return (isinstance(obj, self.__class__)
                and self.__dict__ == obj.__dict__)

    def __gt__(self, obj):
        return self.nummer > obj.nummer

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __str__(self):
        return "{} {} {} {}".format(self.nummer, self.modul, self.semester,
                                    self.note)

    def __repr__(self):
        return self.__str__()


def setup_logging(default_path='logging.json',
                  default_level=logging.INFO,
                  env_key='LOG_CFG'):
    """Setup logging configuration"""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as config_file:
            config = json.load(config_file)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def parse_data(soup):
    """parse online table into list of grade"""
    content = soup.find('div', attrs={'class': 'content'})
    table = content.find_all('table')
    data = []
    for tr in table[1].find_all('tr')[2:]:
        cells = tr.find_all('td', attrs={'class': 'qis_records'})
        args = [
            cell.get_text().strip().replace('&nbsp', '') for cell in cells
        ][:4]
        data.append(grade(*args))
    return sorted(list(set(data)))

def createTable(data, cols):
    """create table with prettyTable from list"""
    x = PrettyTable()
    x.field_names = cols
    x.align["Modul"] = "l"
    for row in data:
        x.add_row(row)
    return x

def notify(diff, config):
    """notify as defined in config"""
    fulltable = createTable([entry.get_as_list() for entry in diff], ["Nr", "Modul", "Semester", "Note"])
    if config.sendMail:
        server = get_mail_server(config)
        logger.info("sent email to {}".format(config.receiveMail))
        if not send_mail(server, config.senderMail.username, config.receiveMail,
                        "Veränderung im QIS", str(fulltable)):
            logger.error("failed to sent email to {}".format(
                config.receiveMail))
        for email in config.notifyEmails:
            table = createTable([[entry.nummer, entry.modul] for entry in diff], ["Nr", "Modul"])
            logger.info("sent email to {}".format(email))
            if not send_mail(server, config.senderMail.username, email,
                            "Veränderung im QIS", str(table)):
                logger.error("failed to sent email to {}".format(email))
    else:
        logger.info(fulltable)


def get_mail_server(config):
    """create mail server and login"""
    try:
        server = smtplib.SMTP("smtp.web.de", 587)
        server.starttls()
        server.login(config.senderMail.username, config.senderMail.password)
        return server
    except Exception as e:
        logger.error("failed to get mailserver: %s", e)
    return None


def send_mail(server, sender_email, receiver, subject, message):
    """send mail to receiver with mailserver server"""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server.sendmail(sender_email, receiver, msg.as_string())
    except Exception as e:
        logger.error("failed to send email: %s", e)
        return False
    return True


def get_token(html):
    """return regexed token from website source"""
    pattern = r";asi=(.+?)\""
    matches = re.findall(pattern, html)
    return matches[0] if matches else None


def check_grades(grades, config):
    """check for update on qis"""
    session = requests.session()
    session.get(config.url.home_url, headers=headers)
    payload = {
        'asdf': config.qisLogin.username,
        'submit': 'Ok',
        'fdsa': config.qisLogin.password
    }
    resp = session.post(config.url.login_url, payload, headers=headers)
    if "angemeldet" not in resp.text:
        logger.error("login failed")
        logger.debug(resp.text)
        exit(1)
    logger.debug("login successfull")
    resp = session.get(config.url.verwaltung_url, headers={'User-Agent': USER_AGENT})
    token = get_token(resp.text)
    if not token:
        logger.error("Couldnt regex token. exiting")
        logger.debug(resp.text)
        exit(1)
    resp = session.get(config.url.notenspiegel_url.format(token), headers={'User-Agent': USER_AGENT})
    new_grades = parse_data(bs(resp.text, 'html.parser'))
    if grades:
        diff = sorted(list(set(new_grades) - set(grades)))
        if diff:
            logger.info("Change on qis")
            notify(diff, config)
        else:
            logger.info("no change")
    grades = new_grades
    resp = session.get(config.url.logout_url)
    if "angemeldet" in resp.text:
        logger.warn("failed to logout")
        logger.debug(resp.text)
    return grades


def job(config):
    """job"""
    grades = None
    ofile = 'grades.pickle'
    if os.path.isfile(ofile):
        with open(ofile, 'rb') as f:
            grades = pickle.load(f)
    grades = check_grades(grades, config)
    with open(ofile, 'wb') as f:
        pickle.dump(grades, f, pickle.HIGHEST_PROTOCOL)


def load_config():
    """load json_config file"""
    config_file = "config.json"
    if not os.path.isfile(config_file):
        exit("couldn't find config.json")
    return json.load(open(config_file, 'r'), object_hook=lambda d: Namespace(**d))


def main():
    """main"""
    setup_logging(default_level=logging.DEBUG)
    config = load_config()   
    job(config)


if __name__ == "__main__":
    main()
