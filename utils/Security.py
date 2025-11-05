from datetime import datetime, timedelta
from models.Usuario import Usuario
from utils.logger import Logger
from utils.exceptions import Unauthorized
from utils.validations import Validations
import jwt
import os
import pytz
import string
import random

class Security():

    tz=pytz.timezone("America/Caracas")

    @classmethod
    def generateToken(cls, authenticated_user: Usuario):
        access = {
            "iat": datetime.now(tz=cls.tz),
            "exp": datetime.now(tz=cls.tz) + timedelta(weeks=3),
            "id": authenticated_user.id,
            "role": authenticated_user.role.name, 
        }

        access_token = jwt.encode(payload=access, key=os.getenv("jwt_password"), algorithm="HS256")
        return access_token
    
    @classmethod
    def verify_token(cls, headers):
        if "Authorization" in headers.keys():
            authorization:str = headers["Authorization"]
            Logger().debug(authorization)
            encoded_token = authorization.split(" ")[1]
            
            if not encoded_token:
                raise Unauthorized("Falta el token de autorización")

            try:
                payload = jwt.decode(encoded_token, os.getenv("jwt_password"), algorithms=["HS256"])
                return payload
            except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
                return None

        return None
    
    @classmethod
    def generate_otp(cls, length=6):
        numbers = "0123456789"
        return ''.join(random.choice(numbers) for _ in range(length))
    
    @classmethod
    def generate_password(cls):
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#@$"
        length = random.randint(8, 15)
        generated = ""

        while not Validations.is_password(generated):
            for _ in range(length):
                random_index = random.randint(0, len(characters) - 1)
                generated += characters[random_index]

        return generated