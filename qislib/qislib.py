import logging
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup as bs

from .dbhelper import DBhelper
from .parser import Parser
from .plotter import Plotter
from .util import get_token

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36"
headers = {
    'User-Agent': USER_AGENT,
    'Accept':
    'modul/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.5'
}


class QisLib():
    def __init__(self, config, logger=None):
        self.config = config
        self.session = requests.session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.logger = logger or logging.getLogger(__name__)
        self.parser = Parser()
        self.db = DBhelper()
        self.token = None
        self.loggedin = False

    def login(self):
        self.request(self.config.url.home_url)
        payload = {
            'asdf': self.config.qisLogin.username,
            'submit': 'Ok',
            'fdsa': self.config.qisLogin.password
        }
        response = self.session.post(
            self.config.url.login_url, payload, headers=headers)
        if "angemeldet" not in response.text:
            self.logger.error("login failed")
            self.writeErrorLog("login failed", response.text)
            self.loggedin = False
            return False
        self.logger.debug("login successfull")
        self.loggedin = True
        return True

    def create_plots(self, records):
        plotter = Plotter(self.db, records)
        names = plotter.create()
        return names

    def logout(self):
        if not self.loggedin:
            self.logger.warn(
                "you are not loggedin - logging out ist not possible")
            return
        response = self.request(self.config.url.logout_url)
        if "angemeldet" in response:
            self.logger.error("failed to logout")
            self.writeErrorLog("failed to logout", response)
            return
        self.loggedin = False

    def getSession(self):
        return self.session

    def request(self, url):
        response = self.session.get(url, headers={'User-Agent': USER_AGENT})
        if response.status_code != 200:
            err = f"failed to get {url} with {response.status_code}"
            self.logger.error(err)
            self.writeErrorLog(err, response.text)
            return None
        return response.text

    def list_modules(self):
        response = self.request(self.config.url.verwaltung_url)
        self.token = get_token(response)
        if not self.token:
            self.logger.error("failed to list modules - couldnt regex token")
            return None
        response = self.request(
            self.config.url.notenspiegel_url.format(self.token))
        return self.parser.parse_modules(response)

    def get_exam_data(self, url):
        response = self.request(url)
        data = self.parser.parse_module(response)
        return data

    def update_exam_details(self, exam_data):
        url = exam_data['url']
        if not url:
            self.logger.debug(f"no detail-url found for {exam_data['nr']}")
            return
        exam_details = self.get_exam_data(url.format(self.token))
        if not exam_details:
            self.logger.debug(
                f"no details to exam {exam_data['nr']} found")
            return
        self.db.add_data(exam_data['nr'], exam_details)

    def check(self):
        parsed_modules = self.list_modules()
        modules = filter(lambda x: x['is_module'], parsed_modules)
        exams = filter(lambda x: x['is_module']
                       is False and x['nr'] > 10000, parsed_modules)
        # adding modules
        for module_data in modules:
            db_module = self.db.module_exists(module_data['nr'])
            if db_module:
                self.db.update_module(db_module, module_data)
            else:
                self.db.add_module(module_data)
        # adding exams
        for exam_data in exams:
            module_id = self.parser.get_module_id(exam_data['nr'])
            db_exam = self.db.exam_exists(exam_data['nr'])
            if not db_exam:
                # add exam data and details
                self.db.add_exam(module_id, exam_data)
                self.update_exam_details(exam_data)
                continue
            # exam exists -> update if necessary
            changed = self.db.update_exam(db_exam, exam_data)
            # exam changed? -> update details
            if changed:
                self.update_exam_details(exam_data)
        return list(self.db.get_updated())

    def writeErrorLog(self, title, msg):
        filename = time.strftime("%Y%m%d-%H%M%S")
        with Path("errors", filename).open('w+') as f:
            f.write(f"{title}\n{msg}")
