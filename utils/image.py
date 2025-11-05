from werkzeug.datastructures.file_storage import FileStorage
from PIL import Image
from utils.exceptions import UploadFileError
import io

def resize(file: FileStorage, new_witdh: int = 500) -> Image:
    img = Image.open(io.BytesIO(file.read()))
    new_height = int(new_witdh * 3 / 2)
    return img.resize((new_witdh, new_height))

def get_format(filename: str):
    return filename.split(".")[-1]

def img_size(image:FileStorage):
    img = Image.open(io.BytesIO(image.read()))
    width, height = img.size 

    if width > height:
        raise UploadFileError("El ancho de la imagen no puede ser superior al alto")
    elif width > 1500:
        raise UploadFileError("La imagen es demasiado ancha")
    elif height > 1875:
        raise UploadFileError("La imagen es demasiado alta")
    
    return width, height
