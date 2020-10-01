from sqlalchemy import Column, Integer, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
 

Base = declarative_base()

class Module(Base):
    __tablename__ = 'module'
    nr = Column('nr', Integer, primary_key=True)
    module = Column('module', Text)
    po = Column('po', Integer)
    sem = Column('semester', Text)
    note = Column('note', Float)
    status = Column('status', Boolean)
    ects = Column('ects', Float)
    exams = relationship('exams')
    
    def __eq__(self, other):
        class_match = isinstance(other, self.__class__)
        a, b = deepcopy(self.__dict__), deepcopy(other.__dict__)
        print(a)
        print(b)
        a.pop('_sa_instance_state', None)
        b.pop('_sa_instance_state', None)
        attrs_match = (a == b)
        return classes_match and attrs_match

class Exam(Base):
    __tablename__ = 'exam'
    nr = Column('nr', Integer, primary_key=True)
    module = Column('module', Text)
    part = Column('part', Text)
    vs = Column('vs', Text)
    note = Column('note', Float)
    status = Column('status', Boolean)
    ects = Column('ects', Float)
    href = Column('href', Text)
    parent_id = Column(Integer, ForeignKey('module.nr'))
    
    def __eq__(self, other):
        class_match = isinstance(other, self.__class__)
        a, b = deepcopy(self.__dict__), deepcopy(other.__dict__)
        print(a)
        print(b)
        a.pop('_sa_instance_state', None)
        b.pop('_sa_instance_state', None)
        attrs_match = (a == b)
        return class_match and attrs_match

class Data(Base):
    __tablename__ = 'data'
    exam_id = Column(Integer, ForeignKey('exam.nr'))
    average = Column('average', Float)
    participants = Column('participants', Integer)
    groups = relationship(Group, secondary='data2groups')

class Group(Base):
    __tablename__ = 'group'
    id = Column('id', Integer, primary_key=True)
    name = Column('name', Text)
    data = relationship(Data, secondary='data2groups')
    
class data2groups(Base):
    __tablename__ = 'data2groups'
    group_id = Column('group_id', Integer, ForeignKey('group.id'))
    data_id = Column('data_id', Integer, ForeignKey('data.exam_id'))
    count = Column('count', Integer)
    group = relationship(Group, backref=backref('data_assoc'))
    data = relationship(Data, backref=backref('group_assoc'))

class DBhelper:
    def __init__(self):
        self.engine = create_engine('sqlite:////modules.db')
        self.session = sessionmaker(bind=self.engine)
        
    def create(self):
        Base.metadata.create_all(engine)
        groups = ['1 - 1,3', '1,7 - 2,3', '2,7 - 3,3', '3,7 - 4', '4,7 - 5']
        for group in groups:
            g = Group(name=group)
            self.session.add(g)
        self.session.commit()
    
    def exists_module(self, module_nr):
        module = self.session.query(Module, module_nr).first()
        if not module:
            return None
        return module
    
    def add_module(self, data):
        m = Module(nr=data['nr'], module=data['module'], po=data['po'],
                    sem=data['sem'], note=data['note'], status=data['status'],
                    ects=data['ects'])
        self.session.add(m)
        self.session.commit()
    
    def update_module(self, module, data):
        current_module = Module(nr=data['nr'], module=data['module'], po=data['po'],
                    sem=data['sem'], note=data['note'], status=data['status'],
                    ects=data['ects'])
        if module != current_module:
            module.update(current_module)
            self.commit()
            return True
        return False
    
    def exists_exam(self, exam_nr):
        exam = self.session.query(Exam, data.nr).first()
        if not exam:
            return None
        return module
        
    def add_exam(self, module_nr, data):
        module = self.session.query(module, module.nr).first()
        if not module:
            print("module not found")
            return
        exam = Exam(nr=data['nr'], module=data['module'], part=data['part'], vs=data['vs'], note=data['note'], status=data['status'], ects=data['ects'])
        module.exams.append(exam)
        self.session.add(module)
        self.session.commit()
    
    def update_exam(self, exam, data):
        current_exam = Exam(nr=data['nr'], module=data['module'], part=data['part'], vs=data['vs'], note=data['note'], status=data['status'], ects=data['ects'])
        if exam != current_exam:
            exam.update(current_exam)
            self.session.commit()
            return True
        return False
        
    def add_data(self, exam_id, data):
        exam = self.session.query(Exam, exam_id).first()
        if not exam:
            print(f"exam not found")
            return
        d = Data(exam_id=exam_id, average=data["average"], participants=data["participants"])
        # average, participants, groups, values
        for group, vlaue in zip(data['groups'], data['values']):
            g = self.session.query(Group, group)
            if not g:
                print("group not found")
                continue
            d2g = data2groups(group=g, data=d, count=value)
            self.session.add(d2g)
        self.session.commit()
             
            