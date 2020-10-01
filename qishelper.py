import requests
import logging
from lib import util
import time
from pathlib import Path
from bs4 import BeautifulSoup as bs

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36"
headers = {
    'User-Agent': USER_AGENT,
    'Accept':
    'modul/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.5'
}

class QisHelper():
    def __init__(self, config, logger=None):
        self.config = config
        self.session = requests.session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.logger = logger or logging.getLogger(__name__)
        self.parser = QisParser()
        self.db = DBhelper()
        self.loggedin = False

    def login(self):
        self.request(self.config.url.home_url)
        payload = {
            'asdf': self.config.qisLogin.username,
            'submit': 'Ok',
            'fdsa': self.config.qisLogin.password
        }
        response = self.session.post(self.config.url.login_url, payload, headers=headers)
        if "angemeldet" not in response.text:
            self.logger.error("login failed")
            self.writeErrorLog("login failed", response.text)
            self.loggedin = False
            return
        self.logger.debug("login successfull")
        self.loggedin = True
    
    def logout(self):
        if not self.loggedin:
            self.logger.warn("you are not loggedin - logging out ist not possible")
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

    def list_modules():
        response = self.session.get(config.url.verwaltung_url)
        token = get_token(resp.text)
        if not token:
            logger.error("failed to list modules - couldnt regex token")
            return None
        return self.parser.parse_modules(response.text)
       
    def get_module(self, url):
        response = session.get(url)
        data = self.qis.parse_module(response.text)
    
    def check(self):
        modules = self.list_modules()
        for module in modules:
            if module['is_module']:
            m = self.db.module_exists(data['nr'])
                if ):
                    self.update_module(
                self.db.add_module(data)
            else:
                self.db.add_exam(self.get_module_id(data['module']), data)
         

    def writeErrorLog(self, title, msg):
        filename = time.strftime("%Y%m%d-%H%M%S")
        with Path("errors", filename).open('w+') as f:
            f.write(f"{title}\n{msg}")
        
    def get_data(self):
        response = self.request(self.config.url.verwaltung_url)
        token = util.get_token(response)
        if not token:
            self.logger.error("Couldnt regex token. exiting")
            return None
        return self.request(self.config.url.notenspiegel_url.format(token))
