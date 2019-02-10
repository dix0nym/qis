import requests
from bs4 import BeautifulSoup as bs
import pickle
import os
from tabulate import tabulate
import schedule
import datetime
import time
import json
from sendmail import SendMail
from types import SimpleNamespace as Namespace
from user_agent import generate_user_agent

headers = {
    'User-Agent': generate_user_agent(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':'en-US,en;q=0.5'
}

url = "https://qis.hs-albsig.de/qisserver/rds?state=user&type=0"
logout_url = "https://qis.hs-albsig.de/qisserver/rds?state=user&amp;type=4&amp;re=last&amp;category=auth.logout&amp;breadCrumbSource=portal&amp;topitem=functions"
login_url = 'https://qis.hs-albsig.de/qisserver/rds?state=user&type=1&category=auth.login&startpage=portal.vm'
verwaltung = 'https://qis.hs-albsig.de/qisserver/rds?state=change&type=1&moduleParameter=studyPOSMenu&nextdir=change&next=menu.vm&subdir=applications&xml=menu&purge=y&navigationPosition=functions%2CstudyPOSMenu&breadcrumb=studyPOSMenu&topitem=functions&subitem=studyPOSMenu'
    
class grade:
    def __init__(self, nummer,text, semester, note, status, ects, art, pv, vs, datum):
        self.nummer = int(nummer)
        self.text = text
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
        return (isinstance(obj, self.__class__) and self.__dict__ == obj.__dict__)
    
    def __ne__(self, obj):
        return not self.__eq__(obj)
    
    def __gt__(self, obj):
        return self.nummer > obj.nummer
    
    def __lt__(self, obj):
        return self.nummer < obj.nummer
    
    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
    
    def __str__(self):
        return "{} {} {} {} {} {} {}".format(self.nummer, self.text, self.semester, self.note, self.status, self.ects, self.datum)

    def __repr__(self):
        return self.__str__()

def parse_data(soup):
    content = soup.find('div', attrs={'class' :'content'})
    table = content.find_all('table')
    data = []
    for tr in table[1].find_all('tr')[2:]:
        cells = tr.find_all('td', attrs={'class':'qis_records'})
        args = [cell.get_text().strip().replace('&nbsp', '') for cell in cells]
        data.append(grade(*args))
    return sorted(list(set(data)))

def handle_status_code(resp):
    if resp.status_code != 200:
        print(resp.status_code, resp.text)

def get_notenspiegel_url(source):
    soup = bs(source, 'html.parser')
    notenspiegel_url = [k for k in soup.find_all('a', attrs={'class':'auflistung'}) if 'Notenspiegel' == k.text]
    if not notenspiegel_url:
        exit("smth went wrong, couldnt find notenspiegel_url")
    return notenspiegel_url[0]['href']

def get_leistungen_url(source):
    soup = bs(source, 'html.parser')
    leistungen = soup.select('li.treelist > a[title*=Leistungen]')
    if not leistungen:
        exit("smth went wrong, couldnt find leistungen")
    return leistungen[0]['href']

def get_table(grades):
    table = []
    for grade in grades:
        table.append(grade.get_as_list())
    return table

def check_notes(grades, config):
    session = requests.session()
    session.get(url, headers=headers)
    payload = {'asdf': config.qisLogin.username, 'submit': 'Ok', 'fdsa': config.qisLogin.password}
    resp = session.post(login_url, payload, headers=headers)
    handle_status_code(resp)
    if logout_url not in resp.text:
        print(resp.text)
        exit("login failed")
    print("login successfull")
    # navigate to leistungen
    resp = session.get(verwaltung)
    resp = session.get(get_notenspiegel_url(resp.text))
    resp = session.get(get_leistungen_url(resp.text))

    new_grades = parse_data(bs(resp.text, 'html.parser'))
    if grades:
        diff = list(set(new_grades) - set(grades))
        if diff:
            table = tabulate(get_table(grades), headers=["Nr", "Modul", "Semester", "Note", "Status", "ECTS", "Art", "pv", "vs", "Datum"])
            if config.sendMail:
                print("sent email to {}".format(config.receiveMail))
                s = SendMail(config.senderMail.username, config.senderMail.password)
                if not s.sendMail(config.receiveMail, "Veränderung im QIS", table):
                    print("failed to sent email")
            else:
                print(table)
    grades = new_grades
    return grades

def job(config):
    print(datetime.datetime.now())
    grades = None
    ofile = 'grades.pickle'
    if os.path.isfile(ofile):
        with open(ofile, 'rb') as f:
            grades = pickle.load(f)
    grades = check_notes(grades, config)
    with open(ofile, 'wb') as f:
        pickle.dump(grades, f, pickle.HIGHEST_PROTOCOL)

def load_config():
    cfile = "config.json"
    if not os.path.isfile(cfile):
        exit("couldn't find config.json")
    return json.load(open(cfile, 'r'), object_hook=lambda d: Namespace(**d))

def main():
    config = load_config()
    job(config)
    schedule.every(config.schedule).hours.do(job, config=config)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()