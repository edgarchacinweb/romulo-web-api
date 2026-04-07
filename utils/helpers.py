from typing import Union
from datetime import date, time, datetime

def str_to_date(date_str: Union[str, date]) -> date:
    if isinstance(date_str, date): return date_str
    else: return datetime.strptime(date_str, "%Y-%m-%d").date()

def date_to_str(date_object: date) -> str:
    return date_object.strftime("%Y-%m-%d")

def str_to_time(tm: Union[str, time]):
    return datetime.strptime(tm, "%H:%M").time() if isinstance(tm, str) else tm

def time_to_str(tm: time):
    return tm.strftime("%H:%M")

def str_to_datetime(datetime_str: Union[str, datetime]) -> datetime:
    if isinstance(datetime_str, datetime): return datetime_str
    else: return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

def datetime_to_str(datetime_object: datetime) -> str:
    return datetime_object.strftime("%Y-%m-%d %I:%M:%S %p")

def capitalize(string: str) -> str:
    return " ".join([w.capitalize() for w in string.split(" ")])

def number_to_letter(number: Union[int, None]) -> str:
    if not number or number == 0:
        return "Por asignar"
    letters = ["A", "B", "C", "D", "E", "F", "G"]
    try:
        return letters[number - 1]
    except (IndexError, TypeError):
        return "A"
