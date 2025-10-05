# export_to_excel.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pandas as pd
from psycopg2 import sql
from config import SHEET_TO_TABLE
from db import Database

COLUMN_NAME_MAP = {
    "id": "№",
    "fio": "ФИО",
    "number": "Номер",
    "date": "Дата",
    "user_id": "ID",
    "application_amount": "Сумма заявки",
    "token": "Токен",
    "receipt_amount": "Сумма поступления",
    "hash": "Хэш",
    "sender_address": "Адрес отправителя",
    "return_address": "Адрес возврата",
    "return_hash": "ХЭШ ВОЗВРАТА",
    "return_done": "Дата возврата",
    "return_reason": "Причина возврата",
    "status": "Статус",
    "memo": "Мемо"  # добавляем, если есть
}

class ExportToExcelTab:
    def __init__(self, notebook, db, dsn, excel_path='Возвраты 2025.xlsx'):
        self.notebook = notebook
        self.db = db
        self.dsn = dsn
        self.excel_path = excel_path
        self.frame = ttk.Frame(self.notebook)
        self.create_widgets()
        

    def create_widgets(self):
        self.export_button = ttk.Button(self.frame, text="Выгрузить все данные в Excel", command=self.export_data)
        self.export_button.pack(pady=20)

    # Предположим, что у вас есть класс или функция, где реализован экспорт:
    def export_data(self):
        self.db.connect()
        try:
            with pd.ExcelWriter(self.excel_path, engine='xlsxwriter') as writer:
                for sheet_name, table_name in SHEET_TO_TABLE.items():
                    try:
                        # Загружаем таблицу из базы
                        query = f'SELECT * FROM "{table_name}"'
                        df = pd.read_sql_query(query, self.db.engine)

                        # Проверяем наличие колонки 'memo' и добавляем её в словарь отображений
                        if 'memo' in df.columns:
                            COLUMN_NAME_MAP['memo'] = 'Мемо'

                        # Переименовываем колонки
                        df.rename(columns=COLUMN_NAME_MAP, inplace=True)

                        # Сортируем по первой колонке (обычно это "№")
                        # Предполагаем, что первая колонка — это "№" после переименования
                        first_col = list(COLUMN_NAME_MAP.values())[0]
                        df.sort_values(by=first_col, ascending=True, inplace=True)

                        # Записываем в Excel
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception as e:
                        print(f"Ошибка при экспорте таблицы {table_name} для листа {sheet_name}: {e}")
                messagebox.showinfo("Успех", f"Успешно выгрузились данные в {self.excel_path}")
        finally:
            self.db.close()
