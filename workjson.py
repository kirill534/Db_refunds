import json
import os
from venv import logger


REASONS_FILE = 'reasons.json'
FIO_FILE = "fio.json"

def load_fio():
    if os.path.exists(FIO_FILE):
        with open(FIO_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("fio", "")
    return ""

def save_fio(fio_value):
    try:
        with open(FIO_FILE, 'w', encoding='utf-8') as f:
            json.dump({"fio": fio_value}, f, ensure_ascii=False)
    except Exception as e:
        # Можно логировать ошибку или выводить сообщение
        logger.error(f"Ошибка при сохранении причин: {e}")

def load_reasons():
    if os.path.exists(REASONS_FILE):
        with open(REASONS_FILE, 'r', encoding='utf-8') as f:
            reasons = json.load(f)
    else:
        reasons = ["MTS:MTSB ERROR: REJECTED (3006)."]  # стартовые причины
    return reasons

def save_reasons(reasons):
    """
    Сохраняет список причин в файл reasons.json.
    
    Args:
        reasons (list): Список причин.
    """
    filename = "reasons.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(reasons, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при сохранении причин: {e}")
