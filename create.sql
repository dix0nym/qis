
CREATE TABLE IF NOT EXISTS module (
    nr INTEGER PRIMARY KEY,
    module TEXT,
    po INTEGER,
    sem TEXT,
    note REAL,
    status INTEGER,
    ects REAL
);

CREATE TABLE IF NOT EXISTS exam (
    nr INTEGER PRIMARY KEY,
    module TEXT,
    part TEXT,
    vs TEXT,
    note REAL,
    status INTEGER,
    ects REAL,
    url TEXT,
    module_id INTEGER,
    created INTEGER,
    updated INTEGER,
    FOREIGN KEY (module_id) REFERENCES module(nr)
);

CREATE TABLE IF NOT EXISTS exam_details (
    exam_nr INTEGER PRIMARY KEY,
    average REAL,
    participants INTEGER,
    FOREIGN KEY (exam_nr) REFERENCES exam(nr)
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

CREATE TABLE IF NOT EXISTS details2groups (
    group_id INTEGER,
    exam_nr INTEGER,
    count INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (exam_nr) REFERENCES exam_details(exam_nr),
    PRIMARY KEY (group_id, exam_nr)
);

-- insert groups
INSERT INTO groups (name) values ("1 - 1,3");
INSERT INTO groups (name) values ("1,7 - 2,3");
INSERT INTO groups (name) values ("2,7 - 3,3");
INSERT INTO groups (name) values ("3,7 - 4");
INSERT INTO groups (name) values ("4,7 - 5");