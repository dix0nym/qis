import datetime
import json
import logging
import logging.config
import os
import pickle
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import SimpleNamespace as Namespace

import requests
from bs4 import BeautifulSoup as bs
from tabulate import tabulate
from user_agent import generate_user_agent

headers = {
    'User-Agent':
    generate_user_agent(),
    'Accept':
    'modul/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.5'
}

logger = logging.getLogger(__name__)
url = "https://qis.hs-albsig.de/qisserver/rds?state=user&type=0"
logout_url = "https://qis.hs-albsig.de/qisserver/rds?state=user&type=4&re=last&category=auth.logout&breadCrumbSource=&topitem=functions"
login_url = 'https://qis.hs-albsig.de/qisserver/rds?state=user&type=1&category=auth.login&startpage=portal.vm'
verwaltung = 'https://qis.hs-albsig.de/qisserver/rds?state=change&type=1&moduleParameter=studyPOSMenu&nextdir=change&next=menu.vm&subdir=applications&xml=menu&purge=y&navigationPosition=functions%2CstudyPOSMenu&breadcrumb=studyPOSMenu&topitem=functions&subitem=studyPOSMenu'


class grade:
    def __init__(self, nummer, modul, semester, note, status, ects, art, pv,
                 vs, datum):
        self.nummer = int(nummer)
        self.modul = modul
        self.semester = semester
        self.note = float(note.replace(',', '.')) if note else note
        self.status = status
        self.ects = float(ects.replace(',', '.'))
        self.art = art
        self.pv = pv
        self.vs = int(vs)
        self.datum = datum

    def get_as_list(self):
        return list(self.__dict__.values())

    def __eq__(self, obj):
        return (isinstance(obj, self.__class__)
                and self.__dict__ == obj.__dict__)

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __gt__(self, obj):
        return self.nummer > obj.nummer

    def __lt__(self, obj):
        return self.nummer < obj.nummer

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __str__(self):
        return "{} {} {} {} {} {} {}".format(
            self.nummer, self.modul, self.semester, self.note, self.status,
            self.ects, self.datum)

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
    content = soup.find('div', attrs={'class': 'content'})
    table = content.find_all('table')
    data = []
    for tr in table[1].find_all('tr')[2:]:
        cells = tr.find_all('td', attrs={'class': 'qis_records'})
        args = [cell.get_text().strip().replace('&nbsp', '') for cell in cells]
        data.append(grade(*args))
    return sorted(list(set(data)))


def get_notenspiegel_url(source):
    soup = bs(source, 'html.parser')
    notenspiegel_url = [
        k for k in soup.find_all('a', attrs={'class': 'auflistung'})
        if 'Notenspiegel' == k.text
    ]
    if not notenspiegel_url:
        logger.error("couldnt find notenspiegel_url\n%s", soup.prettify())
        exit(1)
    return notenspiegel_url[0]['href']


def get_leistungen_url(source):
    soup = bs(source, 'html.parser')
    leistungen = soup.select('li.treelist > a[title*=Leistungen]')
    if not leistungen:
        logger.error("couldnt find leistungen_url\n%s", soup.prettify())
        exit(1)
    return leistungen[0]['href']


def notify(diff, config):
    fulltable = tabulate(
        [entry.get_as_list() for entry in diff],
        headers=[
            "Nr", "Modul", "Semester", "Note", "Status", "ECTS", "Art", "pv",
            "vs", "Datum"
        ])
    if config.sendMail:
        server = getMailServer(config.senderMail.username,
                               config.senderMail.password)
        logger.info("sent email to {}".format(config.receiveMail))
        if not sendMail(server, config.senderMail.username, config.receiveMail,
                        "Veränderung im QIS", fulltable):
            logger.error("failed to sent email to {}".format(
                config.receiveMail))
        for email in config.notifyEmails:
            table = tabulate(
                [[entry.nummer, entry.modul] for entry in diff],
                headers=["Nr", "Modul"])
            logger.info("sent email to {}".format(email))
            if not sendMail(server, config.senderMail.username, email,
                            "Veränderung im QIS", table):
                logger.error("failed to sent email to {}".format(email))
    else:
        logger.info(fulltable)


def getMailServer(username, password):
    try:
        server = smtplib.SMTP("smtp.web.de", 587)
        server.starttls()
        server.login(username, password)
        return server
    except Exception as e:
        logger.error("failed to get mailserver: %s", e)
    return None


def sendMail(server, sender_email, receiver, subject, message):
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


def check_grades(grades, config):
    session = requests.session()
    session.get(url, headers=headers)
    payload = {
        'asdf': config.qisLogin.username,
        'submit': 'Ok',
        'fdsa': config.qisLogin.password
    }
    resp = session.post(login_url, payload, headers=headers)
    if "angemeldet" not in resp.text:
        logger.error("login failed\n%s", resp.text)
        exit(1)
    logger.debug("login successfull")
    resp = session.get(verwaltung)
    resp = session.get(get_notenspiegel_url(resp.text))
    resp = session.get(get_leistungen_url(resp.text))

    new_grades = parse_data(bs(resp.text, 'html.parser'))
    if grades:
        diff = sorted(list(set(new_grades) - set(grades)))
        if diff:
            logger.info("Change on qis")
            notify(diff, config)
        else:
            logger.info("no change")
    grades = new_grades
    resp = session.get(logout_url)
    if "angemeldet" in resp.text:
        logger.warn("failed to logout")
        logger.debug(resp.text)
    return grades


def job(config):
    grades = None
    ofile = 'grades.pickle'
    if os.path.isfile(ofile):
        with open(ofile, 'rb') as f:
            grades = pickle.load(f)
    grades = check_grades(grades, config)
    with open(ofile, 'wb') as f:
        pickle.dump(grades, f, pickle.HIGHEST_PROTOCOL)


def load_config():
    cfile = "config.json"
    if not os.path.isfile(cfile):
        exit("couldn't find config.json")
    return json.load(open(cfile, 'r'), object_hook=lambda d: Namespace(**d))


def main():
    setup_logging(default_level=logging.DEBUG)
    config = load_config()
    job(config)


if __name__ == "__main__":
    main()
