"""
core/logger/logger.py
Logger simples para persistência de logs em arquivo.
"""
import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), '../../logs/layout_engine.log')

class Logger:
    def __init__(self, log_path: str = LOG_PATH):
        self.log_path = os.path.abspath(log_path)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, level: str, message: str):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"{now} | {level.upper():5} | {message}\n")

    def info(self, message: str):
        self.log('INFO', message)

    def warn(self, message: str):
        self.log('WARN', message)

    def error(self, message: str):
        self.log('ERROR', message)
