import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
import datetime
from config import FIELDS_TS_ENG, FIELDS_TS_RU, LIST_TOKEN, SHEET_TO_TABLE
import db
import logging
from psycopg2 import sql

logger = logging.getLogger(__name__)

class SearchEditTab:
    """
    Класс представляет вкладку для поиска и редактирования данных таблиц.
    
    Атрибуты:
        parent (tk.Widget): Родительский виджет.
        db (db.Database): Объект базы данных.
        selected_sheet (tk.StringVar): Переменная для выбранного листа.
        search_var (tk.StringVar): Переменная для строки поиска.
        base_field_names (list): Исходные имена полей на английском.
        base_field_titles (list): Заголовки колонок на русском.
        title_to_field (dict): Соответствие заголовка и внутреннего имени поля.
        columns (list): Названия колонок текущей таблицы.
        all_data (list): Полные данные, загруженные из базы.
        frame (ttk.Frame): Основной контейнер вкладки.
        sheet_combo (ttk.Combobox): Выпадающий список листов.
        tree (ttk.Treeview): Таблица для отображения данных.
    """
    def __init__(self, parent, db: db.Database):
        """
        Инициализация вкладки поиска и редактирования.
        
        Args:
            parent (tk.Widget): Родительский виджет.
            db (db.Database): Объект базы данных.
        """
        self.parent = parent
        self.db = db

        self.selected_sheet = tk.StringVar()
        self.search_var = tk.StringVar()

        self.base_field_names = FIELDS_TS_ENG
        self.base_field_titles = FIELDS_TS_RU  

        self.title_to_field = dict(zip(self.base_field_titles, self.base_field_names))

        self.columns = []
        self.all_data = []

        self.setup_ui()

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

    def setup_ui(self):
        """
        Создает пользовательский интерфейс вкладки, включая поля для выбора листа, поиска и таблицу.
        """
        self.frame = ttk.Frame(self.parent)

        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(top_frame, text="Выберите лист:").pack(side='left', padx=5)
        self.sheet_combo = ttk.Combobox(top_frame, values=list(SHEET_TO_TABLE.keys()), state='readonly', width=30)
        self.sheet_combo.pack(side='left', padx=5)
        self.sheet_combo.bind('<<ComboboxSelected>>', self.load_data_and_update_fields)

        ttk.Label(top_frame, text="Поиск:").pack(side='left', padx=5)
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var)
        search_entry.pack(side='left', padx=5)
        if LIST_TOKEN:
            self.sheet_combo.current(0)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_data())

        #btn_frame = ttk.Frame(self.frame)
        #btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(top_frame, text="Обновить данные", command=self.load_data).pack(side='left', padx=15)

        self.tree = ttk.Treeview(self.frame, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor='w')
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Скроллы
        h_scrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(fill='x')

        self.tree.bind('<Double-1>', self.on_double_click)

        # Добавляем кнопку удаления
        delete_button = ttk.Button(self.frame, text="Удалить выбранную строку", command=self.delete_selected_row)
        delete_button.pack(pady=5)

        self.all_data = []
        self.load_data_and_update_fields()

    def get_current_fields(self):
        """
        Получает текущие поля и заголовки колонок в зависимости от выбранного листа.
        
        Returns:
            tuple: (список полей, список заголовков)
        """
        selected_sheet = self.sheet_combo.get()
        fields = self.base_field_names.copy()
        titles = self.base_field_titles.copy()
        if selected_sheet in ["USDT (TON)", "TON"]:
            fields.append("memo")
            titles.append("Мемо")
        return fields, titles

    def load_data_and_update_fields(self, event=None):
        # 1. Сохраняем текущие ширины
        current_widths = {col: self.tree.column(col, option='width') for col in self.columns}
        # 2. Получаем новые колонки
        fields, titles = self.get_current_fields()
        # 3. Обновляем колонны
        self.tree.config(columns=titles)
        # 4. Восстанавливаем ширины и задаем названия
        for col in self.tree['columns']:
            width = current_widths.get(col, 100)
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, stretch=True)

        self.title_to_field = dict(zip(titles, fields))
        self.load_data()

    def load_data(self, event=None):
        """
        Загружает данные из базы данных и отображает их в таблице.
        """
        sheet_name = self.sheet_combo.get()
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
                query = sql.SQL("SELECT {} FROM {} ORDER BY id DESC").format(
                    sql.SQL(', ').join(map(sql.Identifier, fields)),
                    sql.Identifier(table_name)
                )
                cur.execute(query)
                rows = cur.fetchall()
                self.all_data = rows
                self.tree.delete(*self.tree.get_children())
                for row in rows:
                    self.tree.insert('', 'end', values=row)
                self.auto_adjust_column_widths()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            logger.exception("Ошибка при загрузке данных таблицы")

    def filter_data(self):
        """
        Фильтрует загруженные данные по строке поиска и отображает их.
        """
        search_text = self.search_var.get().lower()

        filtered = []

        for row in self.all_data:
            match_search = search_text in ' '.join(map(str, row)).lower()

            date_in_range = True  # Можно добавить фильтр по дате, если нужно

            if match_search and date_in_range:
                filtered.append(row)

        self.populate_table(filtered)

    def populate_table(self, data):
        """
        Обновляет таблицу отображением переданных данных.
        """
        self.tree.delete(*self.tree.get_children())
        for row in data:
            self.tree.insert('', 'end', values=row)

    def get_entry_value(self, entry_widget):
        """
        Получает значение из виджета редактирования.
        
        Args:
            entry_widget (ttk.Widget or tuple): Виджет или кортеж (переменная, виджет).
        
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
        Обрабатывает двойной клик по строке таблицы для редактирования данных.
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
                combobox.set(values[i])
                combobox.grid(row=i, column=1, padx=10, pady=5)
                entries[col] = combobox
            else:
                ttk.Label(edit_win, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='e')
                var = tk.StringVar(value=values[i])
                entry = ttk.Entry(edit_win, textvariable=var, width=50)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entries[col] = (var, entry)

        def save():
            """
            Сохраняет изменения в базе данных и обновляет таблицу.
            """
            current_columns = self.tree["columns"]
            updated_data = {}
            for col in current_columns:
                widget = entries[col]
                value = self.get_entry_value(widget)
                updated_data[self.title_to_field[col]] = value.strip()

            selected_id = self.tree.focus()
            if not selected_id:
                messagebox.showwarning("Выбор", "Выберите строку для редактирования")
                return
            row = self.tree.item(selected_id, 'values')
            record_id = row[0]
            table_name = SHEET_TO_TABLE.get(self.sheet_combo.get())
            if not table_name:
                messagebox.showerror("Ошибка", f"Таблица для листа '{self.sheet_combo.get()}' не найдена")
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
                messagebox.showinfo("Успех", "Данные сохранены")
                self.load_data()
                edit_win.destroy()
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("Ошибка", str(e))
                logger.exception("Ошибка при сохранении изменений")

        ttk.Button(edit_win, text="Сохранить", command=save).grid(row=len(columns), column=0, columnspan=2, pady=10)

    def delete_selected_row(self):
        """
        Удаляет выбранную строку из базы данных и таблицы.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Удаление", "Пожалуйста, выберите строку для удаления")
            return
        row_values = self.tree.item(selected_item, 'values')
        record_id = row_values[0]  # предполагается, что id в первом столбце
        table_name = SHEET_TO_TABLE.get(self.sheet_combo.get())

        if not table_name:
            messagebox.showerror("Ошибка", "Таблица для текущего листа не найдена")
            return

        confirm = messagebox.askyesno("Подтвердите удаление", "Вы действительно хотите удалить выбранную строку?")
        if not confirm:
            return

        try:
            if not self.db.is_connected():
                self.db.connect()
            with self.db.conn.cursor() as cur:
                query = sql.SQL("DELETE FROM {} WHERE id=%s").format(sql.Identifier(table_name))
                cur.execute(query, (record_id,))
            self.db.conn.commit()
            messagebox.showinfo("Удалено", "Строка успешно удалена")
            self.load_data()
        except Exception as e:
            self.db.conn.rollback()
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")
            logger.exception("Ошибка при удалении строки")