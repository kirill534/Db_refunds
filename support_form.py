# support_form.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
from tkinter import filedialog
from venv import logger
from copypaste import limit_entry_length
from db import Database
from config import (DISABLED_FIELDS, 
                    LIST_TOKEN, 
                    REQUIRED_FIELDS, 
                    SHEET_TO_TABLE, 
                    TOKEN_MAPPING, 
                    FIELDS,
                )
from error_handler import handle_exception
from workjson import load_fio, load_reasons, save_fio, save_reasons


class SupportForm:
    """
    Класс представляет форму поддержки для ввода и обработки данных.
    """
    def __init__(self, parent, db):
        super().__init__()
        self.parent = parent
        self.reasons = load_reasons()
        self.sheet_options = []
        self.db = db

        self.frame = ttk.Frame(self.parent)
        self.frame.pack(padx=10, pady=10, fill='both', expand=True)

        self.fields = FIELDS.copy()
        self.entries = {}

        self.photos_paths = []
        self.videos_paths = []
        self.photos_listbox = None
        self.videos_listbox = None

        # Создание полей
        for i, text in enumerate(self.fields):
            ttk.Label(self.frame, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            
            if text == "Токен":
                entry = tk.Entry(self.frame, width=50, state='readonly')
                entry.grid(row=i, column=1, padx=10, pady=5)
                self.entries[text] = entry
            elif text in ["ХЭШ ВОЗВРАТА", "Дата возврата"]:
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
                limit_entry_length(entry, 125)
                entry.grid(row=i, column=1, padx=10, pady=5)
                self.entries[text] = entry

        # Загрузка ФИО
        self.fio_value = load_fio()
        if "ФИО" in self.entries:
            self.entries["ФИО"].insert(0, self.fio_value)

        # Фото
        #self.photo_path = None
        #self.btn_select_photo = tk.Button(self.frame, text="Добавить фото", command=self.select_photo)
        #self.btn_select_photo.grid(row=len(self.fields)+2, columnspan=2, padx=30, pady=10, sticky='w')

        #self.photo_label = ttk.Label(self.frame, text="Фотография не выбрана")
        #self.photo_label.grid(row=len(self.fields)+2, column=1, padx=10, pady=10, sticky='w')
        self.btn_open_media_window = tk.Button(self.frame, text="Добавить фото/видео", command=self.open_media_window)
        self.btn_open_media_window.grid(row=len(self.fields)+7, columnspan=2, padx=10, pady=10)
        # Чекбокс ручной отправки
        self.manual_send_var = tk.BooleanVar(value=False)
        self.chk_manual_send = tk.Checkbutton(
            self.frame,
            text="Ручная отправка",
            variable=self.manual_send_var,
            command=self.toggle_manual_send  # вызов при изменении
        )
        self.chk_manual_send.grid(row=len(self.fields)+3, column=0, padx=10, pady=5, sticky='w')

        # Кнопка добавления
        self.btn_add = tk.Button(self.frame, text="Добавить данные", command=self.submit_data)
        self.btn_add.grid(row=len(self.fields)+4, columnspan=2, padx=10, pady=10)

        # Лист выбора
        ttk.Label(self.frame, text="Выберите лист").grid(row=len(self.fields)+1, column=0, padx=10, pady=5, sticky="e")
        self.combo_sheet_name = ttk.Combobox(self.frame, values=LIST_TOKEN)
        self.combo_sheet_name.grid(row=len(self.fields)+1, column=1, padx=10, pady=5)
        if LIST_TOKEN:
            self.combo_sheet_name.current(0)
        self.combo_sheet_name.bind("<<ComboboxSelected>>", self.on_support_select)

        self.current_table = None
        self.update_fields_for_sheet()

        # Изначально вызываем управление состоянием
        self.toggle_manual_send()

    def open_media_window(self):
        media_window = tk.Toplevel(self.parent)
        media_window.title("Выбор фото или видео")
        media_window.geometry("600x400")
        self.media_type_var = tk.StringVar(value="photo")
        self.photos_frame = ttk.LabelFrame(media_window, text="Фотографии")
        self.photos_frame.grid(row=len(self.fields)+5, column=0, columnspan=3, padx=10, pady=10, sticky='ew')

        self.photos_listbox = tk.Listbox(self.photos_frame, height=4, width=50)
        self.photos_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        photos_buttons_frame = ttk.Frame(self.photos_frame)
        photos_buttons_frame.pack(side='right', fill='y', padx=5, pady=5)

        ttk.Button(photos_buttons_frame, text="Добавить фото", command=self.add_photo).pack(pady=2)
        ttk.Button(photos_buttons_frame, text="Удалить выбранное фото", command=self.delete_selected_photo).pack(pady=2)

        # Область для видео
        self.videos_frame = ttk.LabelFrame(media_window, text="Видео")
        self.videos_frame.grid(row=len(self.fields)+6, column=0, columnspan=3, padx=10, pady=10, sticky='ew')

        self.videos_listbox = tk.Listbox(self.videos_frame, height=4, width=50)
        self.videos_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        videos_buttons_frame = ttk.Frame(self.videos_frame)
        videos_buttons_frame.pack(side='right', fill='y', padx=5, pady=5)

        ttk.Button(videos_buttons_frame, text="Добавить видео", command=self.add_video).pack(pady=2)
        ttk.Button(videos_buttons_frame, text="Удалить выбранное видео", command=self.delete_selected_video).pack(pady=2)

        self.media_window = media_window


    def add_photo(self):
        # Проверка, есть ли уже видео
        if self.videos_paths:
            messagebox.showwarning("Недопустимо", "Удалите видео, чтобы добавить фото.")
            return
        file_paths = filedialog.askopenfilenames(
            title="Выберите фотографии",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        for path in file_paths:
            if path not in self.photos_paths:
                self.photos_paths.append(path)
                self.photos_listbox.insert(tk.END, path.split('/')[-1])  # отображаем только имя файла

    def delete_selected_photo(self):
        selected_indices = self.photos_listbox.curselection()
        for index in reversed(selected_indices):
            if index < len(self.photos_paths):
                del self.photos_paths[index]
            self.photos_listbox.delete(index)

    def add_video(self):
        # Проверка, есть ли уже фото
        if self.photos_paths:
            messagebox.showwarning("Недопустимо", "Удалите фотографии, чтобы добавить видео.")
            return
        file_path = filedialog.askopenfilename(
            title="Выберите видео",
            filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv")]
        )
        if file_path:
            if file_path not in self.videos_paths:
                self.videos_paths.append(file_path)
                self.videos_listbox.insert(tk.END, file_path.split('/')[-1])

    def delete_selected_video(self):
        selected_indices = self.videos_listbox.curselection()
        for index in reversed(selected_indices):
            if index < len(self.videos_paths):  # Проверка, что индекс в пределах списка
                del self.videos_paths[index]
            self.videos_listbox.delete(index)

    def send_files(self, window):
        # Можно добавить подтверждение или закрытие окна
        window.destroy()

    def toggle_manual_send(self):
        manual = self.manual_send_var.get()
        for text, widget in self.entries.items():
            if manual:
                widget.configure(state='normal')
            else:
                # Восстановление исходных значений
                widget.configure(state='normal')
                widget.delete(0, tk.END)
                # Восстановить значения по умолчанию
                if text == "Токен":
                    token_value = TOKEN_MAPPING.get(self.get_selected_sheet(), "")
                    widget.insert(0, token_value)
                    widget.configure(state='readonly')
                elif text == "Статус":
                    widget.insert(0, "Возврат не сделан")
                    widget.configure(state='readonly')
                elif text in ["ХЭШ ВОЗВРАТА", "Дата возврата"]:
                    # Пусть эти поля всегда readonly
                    widget.insert(0, "")
                    widget.configure(state='readonly')
                elif text == "ФИО":
                # Восстановить сохраненное значение
                    if hasattr(self, 'fio_value'):
                        widget.insert(0, self.fio_value)
                    else:
                        widget.insert(0, "")
                else:
                    # Для остальных можно оставить активными или тоже readonly
                    widget.configure(state='normal')

    def select_photo(self):
        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            self.photo_path = file_path
            self.photo_label.config(text=f"Выбрана: {file_path.split('/')[-1]}")
        else:
            self.photo_path = None
            self.photo_label.config(text="Фотография не выбрана")

    def update_fields_for_sheet(self):
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
        return self.combo_sheet_name.get()

    def on_support_select(self, event):
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
        try:
            if self.manual_send_var.get():
                # В ручной отправке поля могут быть пустыми
                pass
            else:
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

            # Получаем значения для проверки
            number_value = self.entries.get("Номер").get().strip()
            client_id_value = self.entries.get("ID Клиента").get().strip()
            hash_value = self.entries.get("Хэш").get().strip()

            # Проверка существования записи в базе
            if not self.db.is_connected():
                self.db.connect()

            # Здесь предполагается, что у вас есть метод для проверки существования записи
            # Например, self.db.check_record_exists(table_name, "Номер", number_value, "ID Клиента", client_id_value)
            table_name = SHEET_TO_TABLE.get(self.current_table)

            if table_name:
                exists = self.db.check_record_exists(table_name, 
                                                     "number", number_value, 
                                                     "user_id", client_id_value,
                                                     "receipt_amount", hash_value
                                                     )
                if exists:
                    messagebox.showerror("Ошибка", "Запись с таким Номером заявки, ID клиента и Хэш уже существует.")
                    return

                # Продолжаем вставку, если запись не существует
                if self.manual_send_var.get():
                    pass
                else:
                    data["ХЭШ ВОЗВРАТА"] = ""
                    data["Дата возврата"] = ""
                data["Статус"] = "Возврат не сделан"

                self.db.insert_support_data(self.photos_paths, self.videos_paths, table_name, data, self.manual_send_var)
                fio_input = self.entries.get("ФИО")
                if fio_input:
                    fio_text = fio_input.get().strip()
                    if fio_text:
                        save_fio(fio_text)
                        self.fio_value = fio_text
                messagebox.showinfo("Успех", "Данные успешно добавлены.")
                self.clear_form()
            else:
                messagebox.showerror("Ошибка", f"Таблица для листа '{self.current_table}' не найдена")
                return
        except Exception:
            handle_exception(*sys.exc_info())

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        support_name = self.get_selected_sheet()
        token_value = TOKEN_MAPPING.get(support_name, "")
        self.entries["Токен"].delete(0, tk.END)
        self.entries["Токен"].insert(0, token_value)
        self.entries["ФИО"].delete(0, tk.END)
        self.entries["ФИО"].insert(0, self.fio_value)
        self.entries["Статус"].delete(0, tk.END)
        self.entries["Статус"].insert(0, "Возврат не сделан")
        self.photos_paths.clear()
        self.videos_paths.clear()
        self.photos_listbox.delete(0, tk.END)
        self.videos_listbox.delete(0, tk.END)

    def add_reason(self, combobox):
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
                    save_reasons(self.reasons_list)
            reason_window.destroy()

        tk.Button(reason_window, text="Добавить", command=save_reason).pack(pady=10)
