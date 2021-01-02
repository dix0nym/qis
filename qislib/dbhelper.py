import logging
from pathlib import Path

import pugsql

logging.basicConfig(
    format='%(asctime)s  %(name)s  %(levelname)s: %(message)s', level=logging.DEBUG)


class DBhelper:
    def __init__(self, logger=None):
        self.queries = pugsql.module('queries/')
        self.path = Path('module.db')
        self.logger = logger or logging.getLogger('[DB]')
        self.connect()

    def connect(self):
        if not self.path.exists():
            exit(f"db is not found: {self.path}")
        self.queries.connect('sqlite:///module.db')

    def module_exists(self, module_nr):
        module = self.queries.get_module(nr=module_nr)
        if not module:
            return False
        return module

    def add_module(self, data):
        module = self.queries.create_module(data)
        self.logger.info(f"module {data['nr']} {data['module']} created")
        return module

    def update_module(self, module, data):
        if module['note'] != data['note'] or module['status'] != data['status']:
            module = self.queries.update_module(data)
            self.logger.info(f"module {data['nr']} updated")
            return True
        return False

    def exam_exists(self, exam_nr):
        exam = self.queries.get_exam(nr=exam_nr)
        if not exam:
            return False
        return exam

    def add_exam(self, module_nr, data):
        # print(data)
        module = self.module_exists(module_nr)
        if not module:
            self.logger.error(f"module {module_nr} not found - cant add exam")
            return None
        data['module_id'] = module_nr
        exam = self.queries.create_exam(data)
        self.logger.info(f"exam  {data['nr']} created")
        return exam

    def update_exam(self, exam, data):
        if exam['note'] != data['note'] or exam['status'] != data['status']:
            self.queries.update_exam(data)
            return True
        return False

    def data_exists(self, exam_nr):
        data = self.queries.get_data(exam_nr=exam_nr)
        if not data:
            return False
        return data

    def get_grades(self, exam_nr):
        grades = []
        for i in range(1, 6):
            d2g = self.queries.get_d2g(exam_nr=exam_nr, group_id=i)
            grades.append(d2g['count'])
        return grades

    def get_data(self, exam_nr):
        data = self.queries.get_data(exam_nr=exam_nr)
        if not data:
            self.logger.debug(f'data for exam {exam_nr} not found')
            return None
        data['count'] = self.get_grades(exam_nr)
        return data

    def add_data(self, exam_nr, data):
        # data = {exam_nr, average, participants, values}
        exam = self.exam_exists(exam_nr)
        if not exam:
            self.logger.error(f'exam {exam_nr} not found - cant add data')
            return False
        data_obj = self.data_exists(exam_nr)
        data['exam_nr'] = exam_nr
        if not data_obj:
            data_obj = self.queries.create_data(data)
            self.logger.info(f"data {exam_nr} created")
        # average, participants, groups, values
        for gid, value in zip(list(range(1, 6)), data['values']):
            group = self.queries.get_group(name="", id=gid)
            if not group:
                self.logger.error(f"group {group} not found -> skip")
                continue
            # check if relation already exists
            rel = self.queries.get_d2g(group_id=group['id'], exam_nr=exam_nr)
            if rel:
                # rel already exists => update
                # self.logger.info(f"relation {group['id']} -> {exam_nr} already exists => update count {value}")
                self.queries.update_d2g(
                    group_id=group['id'], exam_nr=exam_nr, count=value)
            else:
                # self.logger.info(f"create relation {group['id']} -> {exam_nr} => count: {value}")
                self.queries.create_d2g(
                    group_id=group['id'], exam_nr=exam_nr, count=value)
