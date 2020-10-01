from bs4 import BeautifulSoup as bs
import re
import itertools

def clean(str):
    return re.sub(r"\s+", " ", str)

class QisParser:
    def __init__(self):
        pass

    def is_module(self, module):
        """derrive type of entry from number"""
        tmp = str(module)[-3:]
        return tmp == '000'
    
    def get_module_id(self, module):
        """derrive parent module id from exam id"""
        return str(module)[:-3] + '000'
        
    def parse_modules(self, data):
        """parse online table into list of grade"""
        # PNr, Prüfungstext, PO, Sem, PK, PArt, VS, Note, Status, ECTS, Verm
        soup = bs(src, 'html.parser')
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
            if cols and len(cols) > 3:
                url = cols[3].select('a')
                url = url[0]['href'] if url else None
            module = {'nr': int(args[0]), 'module':  args[1], 'po': int(args[2]), 'sem': args[3],
                    'note': float(args[7]), 'status': args[8] == 'bestanden', 'ects': float(args[9]}
            module['is_module'] = self.is_module(self, module['module')
            data.append(module)
        return data
    
    def parse_module(self, data):
        soup = bs(data, 'html.parser')
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
        