import itertools
import logging
import re

from bs4 import BeautifulSoup as bs

from .util import clean, remove_token, to_float


class Parser:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def is_module(self, module):
        """derrive type of entry from number"""
        tmp = str(module)[-2:]
        return tmp == '00' and int(module) > 10000

    def get_module_id(self, module):
        """derrive parent module id from exam id"""
        return str(module)[:-2] + '00'

    def parse_modules(self, data):
        """parse online table into list of grade"""
        # PNr, Prüfungstext, PO, Sem, PK, PArt, VS, Note, Status, ECTS, Verm
        soup = bs(data, 'html.parser')
        content = soup.select_one('div.content')
        table = content.select('table')
        if not table or len(table) != 2:
            return
        table = table[1]
        rows = table.select('tr')
        data = []
        for row in rows[2:]:
            cols = row.select('td')
            args = [
                bytes(c.text, 'utf-8').decode('utf-8', 'ignore').strip().replace('&nbsp', '') for c in cols
            ]
            url = ""
            if cols and len(cols) > 7:
                url = cols[7].select_one('a')
                url = remove_token(url['href']) if url and url.has_attr(
                    'href') else None
            module = {'nr': int(args[0]), 'module':  args[1], 'po': int(args[2]), 'sem': args[3], 'part': args[5], 'vs': int(args[6]),
                      'note': to_float(args[7]), 'status': args[8] == 'bestanden', 'ects': to_float(args[9]), 'url': url}
            module['is_module'] = self.is_module(module['nr'])
            data.append(module)
        return data

    def parse_module(self, data):
        soup = bs(data, 'html.parser')
        tables = soup.select('.content > form > table')
        if len(tables) != 3:
            self.logger.debug("no grading details found")
            return None
        trs = tables[2].select('tr')[3:]
        data = {}
        data['average'] = float(
            clean(trs[-1].select('td')[1].text.strip()).replace(',', '.'))
        data['participants'] = int(clean(trs[-2].select('td')[1].text.strip()))
        data['values'] = []
        for tr in trs[:-2]:
            cols = tr.select('td')
            desc = clean(cols[0].text.strip())
            desc = desc[desc.find('(')+1:-1]
            value = int(clean(cols[1].text.replace(
                "(inklusive Ihrer Leistung)", "").strip()))
            data['values'].append(value)
        return data
