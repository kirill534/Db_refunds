# main.py
import sys
from config import CONN_DB
from search_tab import SearchEditTab
import support_form
from db import Database
from error_handler import handle_exception
import tkinter as tk
from tkinter import ttk
import support_form

from traders_tab import TradersTab


sys.excepthook = handle_exception

def CopyPaste(e):
    # Используем keycode и keysym для определения комбинации
    if e.keycode == 86 and e.keysym.lower() != 'v':  # Ctrl+V
        e.widget.event_generate('<<Paste>>')
    elif e.keycode == 67 and e.keysym.lower() != 'c':  # Ctrl+C
        e.widget.event_generate('<<Copy>>')
    elif e.keycode == 88 and e.keysym.lower() != 'x':  # Ctrl+X
        e.widget.event_generate('<<Cut>>')
    elif e.keycode == 65 and e.keysym.lower() != 'a':  # Ctrl+A
        try:
            e.widget.focus_set()
            # Для Text
            if isinstance(e.widget, tk.Text):
                e.widget.tag_add('sel', '1.0', 'end')
            # Для Entry и Combobox
            elif isinstance(e.widget, (tk.Entry, ttk.Combobox)):
                e.widget.select_range(0, 'end')
                e.widget.focus_set()
        except:
            pass
        return 'break'

def bind_copy_paste(widget):
    # Обеспечим работу для всех нужных виджетов
    widget.bind('<Control-Key>', CopyPaste)


def main():
    """
    Инициализация и запуск основного окна приложения.
    
    - Создает соединение с базой данных.
    - Создает главное окно и вкладки: поддержку, трейдеров, поиск и редактирование.
    - Обеспечивает корректное закрытие базы данных при выходе.
    
    Исключения внутри функции обрабатываются глобальным обработчиком `handle_exception`.
    """
    dsn = CONN_DB
    db = Database(dsn)
    try:
        db.connect()
        root = tk.Tk()
        root.title("Добавление данных в PostgreSQL")
        root.geometry("1150x650")

        bind_copy_paste(root)

        notebook = ttk.Notebook(root) 
        notebook.pack(fill='both', expand=True)

        support_form_obj = support_form.SupportForm(notebook, db)
        notebook.add(support_form_obj.frame, text="Саппорт 🤘")

        traders_tab = TradersTab(notebook, db)
        notebook.add(traders_tab.frame, text="Трейдеры")

        search_tab = SearchEditTab(notebook, db)
        notebook.add(search_tab.frame, text="Поиск и редактирование")

        root.mainloop()
    except Exception as e:
        print("Ошибка:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()