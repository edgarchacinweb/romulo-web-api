import re
import uuid
from werkzeug.datastructures.file_storage import FileStorage
from PIL import Image

class Validations():
    @classmethod
    def is_occupation(self, occupation: str):
        pattern = r"^[a-zA-ZÀ-ÿ\u00f1\u00d1]+(\s?[a-zA-ZÀ-ÿ\u00f1\u00d1\.\-]+)*$"
        return bool(re.match(pattern, occupation))
    
    @classmethod
    def is_email(self, email:str):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    @classmethod
    def is_password(self, password:str):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&._-])[A-Za-z\d$@$!%*?&._-]{8,}$'
        return bool(re.match(pattern, password))
    
    @classmethod
    def is_uuid(self, id: str):
        try:
            obj = uuid.UUID(id, version=4)
            return str(obj) == id
        except ValueError:
            return False

    @classmethod
    def is_teacher_hours(self, hours: str) -> bool:
        return bool(re.match(r"\d[20-40]", hours))
        
    @classmethod
    def valid_format(self, filename:str):
        formats = (".png", ".jpeg", ".jpg", ".webp")
        return any(filename.endswith(f) for f in formats)
    
    @classmethod
    def is_ci(self, ci: str):
        return bool(re.match(pattern=r"^\d{7,9}$", string=ci))
    
    @classmethod
    def is_phone(self, phone: str):
        return bool(re.match(pattern=r"^(0412|0414|0416|0424|0426)-\d{7}$", string=phone))
    
    @classmethod
    def is_gender(self, gender: str):
        return gender in ("Masculino", "Femenino")
    
    @classmethod
    def is_name(self, name: str):
        return bool(re.match(pattern=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}(?: [A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})?$", string=name))
    
    @classmethod
    def is_lastname(self, last_name: str):
        return bool(re.match(pattern=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]{2,}(?: [A-Za-zÁÉÍÓÚáéíóÑñ]{2,})*$", string=last_name))
    
    @classmethod
    def is_date(self, date: str):
        return bool(re.match(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$", date))

    @classmethod
    def is_otp(self, otp: str):
        return bool(re.match(r"^\d{6}$", otp))

    @classmethod
    def is_subject(self, subject: str):
        return bool(re.match(r"^(?!\s)(?!.*\s$)(?=.*[a-zA-ZñáéíóúÁÉÍÓÚ]).{3,50}$", subject))
    
    @classmethod
    def is_grade(self, grade):
        return bool(re.match(r"^[1-5]$", str(grade)))
        
    @classmethod
    def is_section(self, section):
        return bool(re.match(r"^[1-9]\d*$", str(section)))
    
    @classmethod
    def is_time(self, time: str) -> bool:
        return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", time))
    
    @classmethod
    def is_activity(self, activity: str) -> bool:
        return bool(re.match(r"^(?!\s)[a-zA-ZñÑáéíóúÁÉÍÓÚ]+(?:\s[a-zA-ZñÑáéíóúÁÉÍÓÚ]+)*$", activity))

    @classmethod
    def is_qualification(self, qualification: str) -> bool:
        return bool(re.match(r"^(1[0-9]|20|[1-9])$", str(qualification)))
    
    @classmethod
    def is_lapse(self, lapse: str) -> bool:
        return bool(re.match(r"^[1-3]$", str(lapse)))
    
    @classmethod
    def is_pdf(self, file: FileStorage) -> bool:
        return file and file.filename.endswith(".pdf")

    @classmethod
    def is_capacity(self, capacity: str) -> bool:
        return bool(re.match(r"^(1[5-9]|[2-9]\d|[1-9]\d{2,})$", str(capacity)))
    
    @classmethod
    def is_valid_image(cls, file: FileStorage) -> bool:
        if not file or file.filename == "":
            return False

        # 1. Validar extensión
        ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg' }
        filename = file.filename.lower()
        if '.' not in filename or filename.rsplit('.', 1)[1] not in ALLOWED_EXTENSIONS:
            return False

        # 2. Validar tamaño (máximo 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB en bytes
        file.seek(0, 2)  # Mover al final del archivo para obtener el tamaño
        file_size = file.tell()
        file.seek(0)  # Resetear el puntero al inicio
        if file_size > MAX_FILE_SIZE:
            return False

        try:
            # 3. Validar que sea una imagen real y verificar aspect ratio
            image = Image.open(file)
            image.verify()  # Verifica integridad del archivo (no decodifica todo)
            
            # Reabrir para chequear dimensiones (verify puede cerrar o limpiar datos)
            file.seek(0)
            image = Image.open(file) 
            width, height = image.size
            
            # 4. Validar relación de aspecto 4:3
            # Se permite un margen de error pequeño por redondeos
            TARGET_RATIO = 4 / 3
            current_ratio = width / height
            tolerance = 0.05  # Tolerancia ajustada

            if not (TARGET_RATIO - tolerance <= current_ratio <= TARGET_RATIO + tolerance):
                return False
                
            return True
            
        except Exception:
            return False

    
