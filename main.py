# main.py
import sys
from tkinter import messagebox
from config import CONN_DB
from copypaste import bind_copy_paste
from export_to_excel import ExportToExcelTab
from search_tab import SearchEditTab
import support_form
from db import Database
from error_handler import handle_exception
import tkinter as tk
from tkinter import ttk
import support_form

from traders_tab import TradersTab


sys.excepthook = handle_exception


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
        root.geometry("1150x700")

        bind_copy_paste(root)

        notebook = ttk.Notebook(root) 
        notebook.pack(fill='both', expand=True)

        support_form_obj = support_form.SupportForm(notebook, db)
        notebook.add(support_form_obj.frame, text="Саппорт 🤘")

        traders_tab = TradersTab(notebook, db)
        notebook.add(traders_tab.frame, text="Трейдеры")

        search_tab = SearchEditTab(notebook, db)
        notebook.add(search_tab.frame, text="Поиск и редактирование")

        export_tab = ExportToExcelTab(notebook, db, CONN_DB)
        notebook.add(export_tab.frame, text="Экспорт в Excel")

        root.mainloop()
    except Exception as e:
        messagebox.showerror("Ошибка при запуске", f"Произошла ошибка: {e}")
        # Можно дополнительно логировать ошибку или выводить traceback
        import traceback
        traceback.print_exc()
    finally:
        db.close()
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Создаем скрышее окно, чтобы показать сообщение
        root = tk.Tk()
        root.withdraw()  # скрыть основное окно
        messagebox.showerror("Критическая ошибка", f"Программа не может запуститься: {e}")
        root.destroy()
        sys.exit(1)
