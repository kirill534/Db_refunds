import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from psycopg2 import sql
from copypaste import bind_copy_paste, limit_entry_length
from db import Database
from config import FIELDS_TS_ENG, FIELDS_TS_RU, SHEET_TO_TABLE, LIST_TOKEN
from venv import logger

from telegram_sender import send_telegram_message


def find_duplicates(seq):
    from collections import defaultdict
    count = defaultdict(list)
    for i, item in enumerate(seq):
        count[item].append(i)
    # оставляем только те, что встречаются более одного раза
    return {k: v for k, v in count.items() if len(v) > 1}


class TradersTab:
    """
    Класс представляет вкладку для работы с трейдерами, отображает данные и позволяет редактировать их.
    
    Атрибуты:
        parent (tk.Widget): Родительский виджет.
        db (Database): Объект базы данных.
        base_field_names (list): Исходные названия полей на английском.
        base_field_titles (list): Заголовки колонок на русском.
        title_to_field (dict): Соответствие заголовка колонки и внутреннего имени поля.
        frame (ttk.Frame): Основной контейнер вкладки.
        sheet_var (tk.StringVar): Переменная для выбранного листа.
        combo_sheet (ttk.Combobox): Выпадающий список листов.
        tree (ttk.Treeview): Таблица для отображения данных.
    """
    def __init__(self, parent, db: Database):
        """
        Инициализация вкладки трейдеров.
        
        Args:
            parent (tk.Widget): Родительский виджет.
            db (Database): Объект базы данных.
        """
        self.db = db
        self.parent = parent

        self.base_field_names = FIELDS_TS_ENG
        self.base_field_titles = FIELDS_TS_RU  

        self.title_to_field = dict(zip(self.base_field_titles, self.base_field_names))

        self.frame = ttk.Frame(self.parent)

        ttk.Label(self.frame, text="Выберите лист:").pack(padx=5, pady=5)
        self.sheet_var = tk.StringVar()
        self.combo_sheet = ttk.Combobox(self.frame, values=LIST_TOKEN, textvariable=self.sheet_var)
        self.combo_sheet.pack(padx=5, pady=5)
        if LIST_TOKEN:
            self.combo_sheet.current(0)
        self.combo_sheet.bind("<<ComboboxSelected>>", self.load_data_and_update_fields)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(padx=5, pady=15)

        # Внутри этого фрейма размещаем кнопку
        ttk.Button(btn_frame, text="Обновить данные", command=self.load_data).pack(padx=5, pady=15)

        self.info_label = ttk.Label(self.frame, text="", foreground="red")
        self.info_label.pack(padx=5, pady=5)

        self.tree = ttk.Treeview(self.frame, columns=self.base_field_titles, show='headings')
        for col in self.base_field_titles:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=1)
        self.tree.pack(fill='both', expand=True)

        h_scrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(fill='x')

        self.tree.bind("<Double-1>", self.on_double_click)

        self.load_data_and_update_fields()

    def auto_adjust_column_widths(self):
        font = tkFont.Font()  # Можно указать шрифт, если есть
        for col in self.tree['columns']:
            max_width = 0
            # Проходим по всем строкам в колонке
            for item in self.tree.get_children():
                cell_value = self.tree.set(item, col)
                width = font.measure(str(cell_value))
                if width > max_width:
                    max_width = width
            # добавляем небольшой запас
            self.tree.column(col, width=max_width + 10, minwidth=max_width+10)

    def get_current_fields(self):
        """
        Получает текущие поля и заголовки в зависимости от выбранного листа.
        
        Returns:
            tuple: (список полей, список заголовков)
        """
        selected_sheet = self.sheet_var.get()
        fields = self.base_field_names.copy()
        titles = self.base_field_titles.copy()

        if selected_sheet in ["USDT (TON)", "TON"]:
            fields.append("memo")
            titles.append("Мемо")
        return fields, titles

    def load_data_and_update_fields(self, event=None):
        """
        Загружает данные из базы и обновляет таблицу и заголовки колонок.
        """
        fields, titles = self.get_current_fields()

        self.tree.config(columns=titles)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

        self.title_to_field = dict(zip(titles, fields))
        self.load_data()

    def load_data(self, event=None):
        """
        Загружает данные из выбранной таблицы базы данных и отображает их в таблице.
        Также проверяет наличие одинаковых ID среди отображаемых данных.
        """
        sheet_name = self.sheet_var.get()
        table_name = SHEET_TO_TABLE.get(sheet_name)
        if not table_name:
            messagebox.showerror("Ошибка", f"Таблица для листа '{sheet_name}' не найдена")
            return
        try:
            if not self.db.is_connected():
                logger.info("Выбрал лист и не было подключения")
                self.db.connect()
            with self.db.conn.cursor() as cur:
                fields, _ = self.get_current_fields()
                query = sql.SQL("SELECT {} FROM {} WHERE status = %s").format(
                    sql.SQL(', ').join(map(sql.Identifier, fields)),
                    sql.Identifier(table_name)
                )
                cur.execute(query, ("Возврат не сделан",))
                rows = cur.fetchall()
                self.tree.delete(*self.tree.get_children())
                id_list = []
                for row in rows:
                    self.tree.insert('', 'end', values=row)
                    # Предполагаем, что ID в первой колонке
                    id_list.append(row[4])
                self.auto_adjust_column_widths()

                self.loaded_rows = rows

                # Проверка на одинаковые ID
                duplicates = find_duplicates(id_list)
                if duplicates:
                    msg = "Обнаружены одинаковые ID клиентов в выбраном листе:\n"
                    for id_value, indices in duplicates.items():
                        row_values = [self.loaded_rows[i][0] for i in indices]
                        row_values_str = ', '.join(str(v) for v in row_values)
                        msg += f"ID {id_value} встречается в строках: {row_values_str}\n"
                    self.info_label.config(text=msg)
                else:
                    self.info_label.config(text="")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            logger.exception("Ошибка при загрузке данных трейдеров")

    def get_entry_value(self, entry_widget):
        """
        Получает значение из виджета ввода.
        
        Args:
            entry_widget (tk.Widget or tuple): Виджет или кортеж (переменная, виджет).
        
        Returns:
            str: Значение из виджета.
        """
        if isinstance(entry_widget, ttk.Combobox):
            return entry_widget.get()
        elif isinstance(entry_widget, tuple):
            var, _ = entry_widget
            return var.get()
        else:
            return ''

    def on_double_click(self, event):
        """
        Обработчик двойного клика по строке таблицы для редактирования.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            return
        values = self.tree.item(selected_item, 'values')
        columns = self.tree["columns"]
        edit_win = tk.Toplevel(self.parent)
        edit_win.title("Редактировать данные")
        entries = {}
        for i, col in enumerate(columns):
            if col == "Статус":
                combobox = ttk.Combobox(edit_win, text=col, values=["Возврат не сделан", "Возврат сделан"], width=48, state='readonly')
                #combobox.set(values[i])
                combobox.set("Возврат сделан")
                combobox.grid(row=i, column=1, padx=10, pady=5)
                entries[col] = combobox
                bind_copy_paste(combobox)
            else:
                ttk.Label(edit_win, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='e')
                var = tk.StringVar(value=values[i])
                entry = ttk.Entry(edit_win, textvariable=var, width=50)
                limit_entry_length(entry, 125)
                if i == 0:
                    entry.config(state='readonly')
                entry.grid(row=i, column=1, padx=5, pady=5)
                entries[col] = (var, entry)
                bind_copy_paste(entry)

        def save():
            """
            Сохраняет изменения в выбранной записи в базе данных.
            """
            current_columns = self.tree["columns"]
            updated_data = {}
            for col in current_columns:
                widget = entries[col]
                value = self.get_entry_value(widget)
                updated_data[self.title_to_field[col]] = value.strip()
            hash_value = self.get_entry_value(entries["ХЭШ ВОЗВРАТА"])
            return_done_value = self.get_entry_value(entries["Дата возврата"])

            if not hash_value or not return_done_value:
                messagebox.showerror("Ошибка", "Поля 'ХЭШ ВОЗВРАТА' и 'Дата возврата' не могут быть пустыми.")
                return
                    # Обновляем в базе
            selected_id = self.tree.focus()
            if not selected_id:
                messagebox.showwarning("Выбор", "Выберите строку для редактирования")
                return
            row = self.tree.item(selected_id, 'values')
            record_id = row[0]
            table_name = SHEET_TO_TABLE.get(self.sheet_var.get())
            if not table_name:
                messagebox.showerror("Ошибка", f"Таблица для листа '{self.sheet_var.get()}' не найдена")
                return
            try:
                if not self.db.is_connected():
                    self.db.connect()
                with self.db.conn.cursor() as cur:
                    set_clauses = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in updated_data.keys()]
                    query = sql.SQL("UPDATE {} SET {} WHERE id=%s").format(
                        sql.Identifier(table_name),
                        sql.SQL(', ').join(set_clauses)
                    )
                    cur.execute(query, list(updated_data.values()) + [record_id])
                self.db.conn.commit()
                if updated_data.get('status') == 'Возврат сделан':
                    # Получаем выбранную строку
                    #row = self.tree.item(selected_id, 'values')
                    # ФИО во второй колонке (индекс 1)
                    fio = updated_data.get('fio')
                    return_hash = updated_data.get('return_hash')
                    number = updated_data.get('number')
                    user_id = updated_data.get('user_id')
                    if fio:
                        message = (
                            f"Возврат выполнен ✅:\n"
                            f"@{fio}\n"
                            f"ID клиента: {user_id}\n"
                            f"Заявка: {number}\n"
                            f"Хэш возврата: {return_hash}"
                        )
                        send_telegram_message(message)
                messagebox.showinfo("Успех", "Данные сохранены")
                self.load_data()
                edit_win.destroy()
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("Ошибка", str(e))
                logger.exception("Ошибка при сохранении изменений")

        ttk.Button(edit_win, text="Сохранить", command=save).grid(row=len(columns), column=0, columnspan=2, pady=10)
