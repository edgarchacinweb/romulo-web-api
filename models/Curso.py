class Curso():

    def __init__(self, *args):
        self.id: str = None
        self.grado: int = None
        
        if len(args) > 1:
            self.id = args[0]
            self.grado = args[1]
        elif len(args) == 1 and isinstance(args[0], dict):
            course_dict = args[0]
            if "id" in course_dict: self.id = course_dict["id"]
            if "Grado" in course_dict: self.grado = course_dict["Grado"]
        else:
            course_tuple = args[0]
            self.id = course_tuple[0]
            self.grado = course_tuple[1]

    def to_dict(self):
        course = dict()
        if self.id: course["CursoId"] = self.id
        if self.grado: course["Grado"] = self.grado
        return course

    def to_tuple(self):
        return (self.grado,)
