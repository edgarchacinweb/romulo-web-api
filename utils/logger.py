from colorama import Fore
import time
import os

class Logger():
    def __init__(self, filename = "logs.txt"):
        self.filename = filename

    def start(self):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        self._write(f"========== {current_time} ==========", "init", Fore.LIGHTYELLOW_EX)

    def success(self, message):
        self._write(message, "success", Fore.GREEN)

    def info(self, message):
        self._write(message, "info", Fore.LIGHTBLACK_EX)

    def error(self, message):
        self._write(message, "error", Fore.LIGHTRED_EX)

    def warning(self, message):
        self._write(message, "warning", Fore.YELLOW)

    def debug(self, message: str, type = "Debug"):
        if os.getenv("mode") == "debug":
            self._write(message, type, Fore.LIGHTBLACK_EX)

    def _write(self, message, status, color):
        with open(os.path.join(os.getcwd(), self.filename), "a") as log_file:
            log_file.write(f"{status} > {message}\n")
            print(color + f"{status} > {message}")
