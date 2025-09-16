# support_form.py
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
from venv import logger
from db import Database
from config import (DISABLED_FIELDS, 
                    LIST_TOKEN, 
                    REQUIRED_FIELDS, 
                    SHEET_TO_TABLE, 
                    TOKEN_MAPPING, 
                    FIELDS,
                )
from error_handler import handle_exception

REASONS_FILE = 'reasons.json'

def load_reasons():
    if os.path.exists(REASONS_FILE):
        with open(REASONS_FILE, 'r', encoding='utf-8') as f:
            reasons = json.load(f)
    else:
        reasons = ["Причина 1", "Причина 2"]  # стартовые причины
    return reasons


class SupportForm:
    """
    Класс представляет форму поддержки для ввода и обработки данных.
    
    Атрибуты:
        parent (tk.Widget): Родительский виджет.
        db (Database): Объект базы данных для выполнения операций с данными.
        reasons (list): Список причин, загруженных из файла reasons.json.
        sheet_options (list): Список опций листов.
        frame (ttk.Frame): Основной контейнер формы.
        fields (list): Список названий полей формы.
        entries (dict): Словарь соответствия полей и виджетов ввода.
        current_table (str): Название текущей выбранной таблицы.
    """
    def __init__(self, parent, db):
        """
        Инициализирует объект формы поддержки.
        
        Args:
            parent (tk.Widget): Родительский виджет.
            db (Database): Объект базы данных.
        """
        super().__init__()
        self.parent = parent
        self.reasons = load_reasons()
        self.sheet_options = []
        self.db = db

        # Поля ввода
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(padx=10, pady=10, fill='both', expand=True)

        self.fields = FIELDS
        self.entries = {}
        for i, text in enumerate(self.fields):
            ttk.Label(self.frame, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            
            if text == "Токен":
                entry = tk.Entry(self.frame, width=50, state='readonly')
                entry.grid(row=i, column=1, padx=10, pady=5)
                self.entries[text] = entry
            elif text in ["ХЭШ ВОЗВРАТА", "Возврат сделан (+)"]:
                entry = tk.Entry(self.frame, width=50, state='readonly')
                entry.grid(row=i, column=1, padx=10, pady=5)
                self.entries[text] = entry
            elif text == "Причина возврата":
                combobox = ttk.Combobox(self.frame, values=self.reasons, width=48)
                combobox.grid(row=i, column=1, padx=10, pady=5)
                self.entries[text] = combobox
                btn_add_reason = tk.Button(self.frame, text="Добавить причину", command=lambda c=combobox: self.add_reason(c))
                btn_add_reason.grid(row=i, column=2, padx=5)
            elif text == "Статус":
                entry = tk.Entry(self.frame, width=50, state='readonly')
                entry.grid(row=i, column=1, padx=10, pady=5)
                entry.insert(0, "Возврат не сделан")
                self.entries[text] = entry
            else:
                entry = tk.Entry(self.frame, width=50)
                entry.grid(row=i, column=1, padx=10, pady=5)
                self.entries[text] = entry

        self.btn_add = tk.Button(self.frame, text="Добавить данные", command=self.submit_data)
        self.btn_add.grid(row=len(self.fields)+2, columnspan=2, padx=10, pady=10)

        # Лист выбора
        ttk.Label(self.frame, text="Выберите лист").grid(row=len(self.fields)+1, column=0, padx=10, pady=5, sticky="e")
        self.combo_sheet_name = ttk.Combobox(self.frame, values=LIST_TOKEN)
        self.combo_sheet_name.grid(row=len(self.fields)+1, column=1, padx=10, pady=5)
        if LIST_TOKEN:
            self.combo_sheet_name.current(0)
        self.combo_sheet_name.bind("<<ComboboxSelected>>", self.on_support_select)

        self.current_table = None
        self.update_fields_for_sheet()

    def update_fields_for_sheet(self):
        """
        Обновляет поля формы в зависимости от выбранного листа.
        Добавляет или удаляет поле "Мемо" при необходимости.
        """
        selected_sheet = self.get_selected_sheet()
        if selected_sheet in ["USDT (TON)", "TON"]:
            if not hasattr(self, 'memo_label'):
                self.fields.append("Мемо")
                row_idx = len(self.fields) - 1  
                self.memo_label = ttk.Label(self.frame, text="Мемо")
                self.memo_label.grid(row=row_idx, column=0, padx=10, pady=5, sticky="e")
            if not hasattr(self, 'memo_entry'):
                self.memo_entry = tk.Entry(self.frame, width=50)
                row_idx = self.fields.index("Мемо")
                self.memo_entry.grid(row=row_idx, column=1, padx=10, pady=5)
                self.entries["Мемо"] = self.memo_entry
        else:
            if hasattr(self, 'memo_label'):
                self.memo_label.destroy()
                del self.memo_label
            if hasattr(self, 'memo_entry'):
                self.memo_entry.destroy()
                del self.entries["Мемо"]
                self.fields.remove("Мемо")
                del self.memo_entry

    def get_selected_sheet(self):
        """
        Возвращает текущий выбранный лист.
        
        Returns:
            str: Название выбранного листа.
        """
        return self.combo_sheet_name.get()

    def on_support_select(self, event):
        """
        Обработчик события выбора листа.
        
        Args:
            event: Событие выбора.
        """
        sheet_name = self.get_selected_sheet()
        token_map = TOKEN_MAPPING
        token_value = token_map.get(sheet_name, "")
        token_entry = self.entries.get("Токен")
        self.current_table = sheet_name
        if token_entry:
            token_entry.configure(state='normal')
            token_entry.delete(0, tk.END)
            token_entry.insert(0, token_value)
            token_entry.configure(state='readonly')
        self.update_fields_for_sheet()

    def submit_data(self):
        """
        Собирает данные из формы и сохраняет их в базе данных.
        Проверяет обязательные поля и выводит сообщения об ошибках при необходимости.
        """
        try:
            missing_fields = []
            for key, entry in self.entries.items():
                if key not in DISABLED_FIELDS:
                    value = entry.get().strip()
                    if not value:
                        missing_fields.append(key)
            if missing_fields:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните следующие поля:\n" + "\n".join(missing_fields))
                return

            data = {}
            for key, entry in self.entries.items():
                data[key] = entry.get().strip()

            if self.get_selected_sheet() in ["USDT (TON)", "TON"]:
                memo_value = self.entries.get("Мемо")
                if memo_value:
                    data["Мемо"] = memo_value.get().strip()

            for field in REQUIRED_FIELDS:
                if not data.get(field):
                    messagebox.showerror("Ошибка", f"Поле '{field}' обязательно для заполнения")
                    return

            data["ХЭШ ВОЗВРАТА"] = ""
            data["Возврат сделан (+)"] = ""
            data["Статус"] = "Возврат не сделан"

            table_name = SHEET_TO_TABLE.get(self.current_table)
            if table_name:
                if not self.db.is_connected():
                    self.db.connect()
                self.db.insert_support_data(table_name, data)
                messagebox.showinfo("Успех", "Данные успешно добавлены.")
            else:
                messagebox.showerror("Ошибка", f"Таблица для листа '{self.current_table}' не найдена")
                return
        except Exception:
            handle_exception(*sys.exc_info())

    def clear_form(self):
        """
        Очищает все поля формы и сбрасывает токен в соответствии с выбранным листом.
        """
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        support_name = self.support_list_var.get()
        token_value = TOKEN_MAPPING.get(support_name, "")
        self.entries["Токен"].delete(0, tk.END)
        self.entries["Токен"].insert(0, token_value)

    def save_reasons(self, reasons):
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

    def add_reason(self, combobox):
        """
        Открывает окно для добавления новой причины и обновляет список причин.
        
        Args:
            combobox (ttk.Combobox): Комбобокс для выбора причины.
        """
        reason_window = tk.Toplevel(self.frame)
        reason_window.title("Добавить причину")
        reason_window.geometry("400x200")
        tk.Label(reason_window, text="Введите новую причину:").pack(pady=10)
        reason_text = tk.Text(reason_window, width=48, height=5)
        reason_text.pack(padx=10, pady=5)

        def save_reason():
            new_reason = reason_text.get("1.0", tk.END).strip()
            if new_reason:
                current_values = list(combobox['values'])
                if new_reason not in current_values:
                    current_values.append(new_reason)
                    combobox['values'] = current_values
                    combobox.set(new_reason)
                    self.reasons_list = current_values
                    self.save_reasons(self.reasons_list)
            reason_window.destroy()

        tk.Button(reason_window, text="Добавить", command=save_reason).pack(pady=10)
