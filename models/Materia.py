class Materia():

    def __init__(self, *args):
        self.id: str = None
        self.name: str = None
        
        if len(args) > 1:
            self.id = args[0]
            self.name = args[1]
        elif len(args) == 1 and isinstance(args[0], dict):
            sbj_dict = args[0]
            if "id" in sbj_dict: self.id = sbj_dict["id"]
            if "Nombre" in sbj_dict: self.name = sbj_dict["Nombre"]
        else:
            sbj_tuple = args[0]
            self.id = sbj_tuple[0]
            self.name = sbj_tuple[1]

    def to_dict(self):
        subject_dict = dict()
        if self.id: subject_dict["id"] = self.id
        if self.name: subject_dict["name"] = self.name
        return subject_dict
