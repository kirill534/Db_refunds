from sys import platform
import platform
import tkinter as tk
from tkinter import ttk

def CopyPaste(e):
    # Проверка на комбинации Ctrl+ или Command+
    # Для Windows/Linux - Ctrl
    # Для macOS - Command
    is_mac = platform.system() == 'Darwin'  # Проверка наличия модификатора Command
    key = e.keysym.lower()
    if is_mac:
        char = e.char
        key = e.keysym.lower()
        # Обработка Command + клавиши
        if char.lower() == 'v':
            e.widget.event_generate('<<Paste>>')
            return 'break'
        elif char.lower() == 'c':
            e.widget.event_generate('<<Copy>>')
            return 'break'
        elif char.lower() == 'x':
            e.widget.event_generate('<<Cut>>')
            return 'break'
        elif char.lower() == 'a':
            try:
                e.widget.focus_set()
                if isinstance(e.widget, tk.Text):
                    e.widget.tag_add('sel', '1.0', 'end')
                elif isinstance(e.widget, (tk.Entry, ttk.Combobox)):
                    e.widget.select_range(0, 'end')
                    e.widget.focus_set()
            except:
                pass
            return 'break'
    else:
        # Обработка для Windows/Linux (Ctrl+)
        if e.keycode == 86 and e.keysym.lower() != 'v':  # Ctrl+V
            e.widget.event_generate('<<Paste>>')
            return 'break'
        elif e.keycode == 67 and e.keysym.lower() != 'c':  # Ctrl+C
            e.widget.event_generate('<<Copy>>')
            return 'break'
        elif e.keycode == 88 and e.keysym.lower() != 'x':  # Ctrl+X
            e.widget.event_generate('<<Cut>>')
            return 'break'
        elif e.keycode == 65 and e.keysym.lower() != 'a':  # Ctrl+A
            try:
                e.widget.focus_set()
                if isinstance(e.widget, tk.Text):
                    e.widget.tag_add('sel', '1.0', 'end')
                elif isinstance(e.widget, (tk.Entry, ttk.Combobox)):
                    e.widget.select_range(0, 'end')
                    e.widget.focus_set()
            except:
                pass
            return 'break'

def bind_copy_paste(widget):
    # Обеспечим работу для всех нужных виджетов
    widget.bind('<Key>', CopyPaste)
