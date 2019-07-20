class Grade:
    """grade class"""
    def __init__(self, nr, modul, semester, note, url=None):
        self.nr = int(nr)
        self.modul = modul
        self.semester = semester
        self.note = float(note.replace(',', '.')) if note else note
        self.url = url

    def get_as_list(self):
        """return attributes as ordered list"""
        return [self.nr, self.modul, self.semester, self.note]

    def get_attr(self, key):
        return self.__dict__[key] if key in self.__dict__ else None

    def get_comparable_dict(self):
        attr = self.__dict__.copy()
        if "url" in attr:
            del attr["url"]
        return attr

    def __eq__(self, obj):
        if not isinstance(obj, self.__class__):
            return False
        selfattr = self.get_comparable_dict()
        objattr = obj.get_comparable_dict()
        return (selfattr == objattr)

    def __gt__(self, obj):
        return self.nr > obj.nr

    def __hash__(self):
        return hash(tuple(sorted(self.get_comparable_dict().items())))

    def __str__(self):
        return "{} {} {} {}".format(self.nr, self.modul, self.semester,
                                    self.note)

    def __repr__(self):
        return self.__str__()