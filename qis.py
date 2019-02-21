import json
import logging
import logging.config
import os
import pickle
from types import SimpleNamespace as Namespace

import requests
from bs4 import BeautifulSoup as bs
from tabulate import tabulate

from lib.grade import Grade
from lib.mailhelper import MailHelper
from lib.plot import create_plot
from lib.util import clean, get_token

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36"
headers = {
    'User-Agent': USER_AGENT,
    'Accept':
    'modul/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.5'
}

logger = logging.getLogger(__name__)


def setup_logging(default_path='logging.json', default_level=logging.INFO):
    """Setup logging configuration"""
    if not os.path.isdir("logs"):
        os.makedirs("logs")
    path = default_path
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
        url = cells[3].select('a')
        url = url[0]['href'] if url else None
        data.append(Grade(*args, url=url))
    return sorted(list(set(data)))

def get_graph_data(session, url):  
    resp = session.get(url, headers={'User-Agent': USER_AGENT})
    soup = bs(resp.text, 'html.parser')
    table = soup.select('.content > form > table')[-1]
    trs = table.select('tr')[3:]
    data = {}
    data['average'] = float(clean(trs[-1].select('td')[1].text.strip()).replace(',', '.'))
    data['participants'] = int(clean(trs[-2].select('td')[1].text.strip()))
    data['names'] = []
    data['values'] = []
    for tr in trs[:-2]:
        cols = tr.select('td')
        desc = clean(cols[0].text.strip())
        desc = desc[desc.find('(')+1:-1]
        value = int(clean(cols[1].text.replace("(inklusive Ihrer Leistung)", "").strip()))
        data['names'].append(desc)
        data['values'].append(value)
    return data

def create_plots(session, diff):
    fnames = []
    for entry in diff:
        if not entry.url:
            continue
        data = get_graph_data(session, entry.url)
        fname = create_plot(entry.modul, data['names'], data['values'], data['participants'], data['average'])
        fnames.append(fname)
    return fnames

def create_table(diff, header, fmt=None):
    values = [ [entry.get_attr(k.lower()) for k in header] for entry in diff]
    table = tabulate(values, header, tablefmt=fmt)
    return table

def cleanup(fnames):
    for fname in fnames:
        os.remove(fname)
    
def notify(diff, config, fnames):
    """notify as defined in config"""
    if config.sendMail:
        fulltable = create_table(diff, ["Nr", "Modul", "Semester", "Note"], fmt="html")
        mailhelper = MailHelper(config)
        logger.info("sending email to {}".format(config.receiveMail))
        if not mailhelper.send_mail(config.receiveMail, "Veränderung im QIS", fulltable, fnames=fnames):
            logger.error("failed to sent email to {}".format(
                config.receiveMail))
        for email in config.notifyEmails:
            table = create_table(diff, ["Nr", "Modul"], fmt="html")
            imgs = fnames if config.notify_graph else None
            logger.info("sending email to {}".format(email))
            if not mailhelper.send_mail(email, "Veränderung im QIS", table, fnames=imgs):
                logger.error("failed to sent email to {}".format(email))
            cleanup(fnames)
    else:
        logger.info(create_table(diff, ["Nr", "Modul", "Semester", "Note"], fmt="simple"))

def get_data(grades, config):
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
    return session, parse_data(bs(resp.text, 'html.parser'))

def compare(grades, new_grades, config, session):
    if grades:
        diff = sorted(list(set(new_grades) - set(grades)))
        if diff:
            logger.info("Change on qis")
            if config.sendMail:
                fnames = create_plots(session, diff)
            notify(diff, config, fnames)
        else:
            logger.info("no change")
    return new_grades

def logout(session, config):
    resp = session.get(config.url.logout_url)
    if "angemeldet" in resp.text:
        logger.warn("failed to logout")
        logger.debug(resp.text)

def job(config):
    """job"""
    grades = None
    ofile = 'grades.pickle'
    if os.path.isfile(ofile):
        with open(ofile, 'rb') as f:
            grades = pickle.load(f)
    session, new_grades = get_data(grades, config)
    grades = compare(grades, new_grades, config, session)
    logout(session, config)
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
