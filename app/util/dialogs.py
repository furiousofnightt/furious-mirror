import ctypes
from typing import Optional

def ask_yes_no(title: str, message: str) -> bool:
    """
    Mostra uma caixa de diálogo nativa do Windows (Sim/Não).
    Retorna True se o usuário clicar em Sim, False caso contrário.
    """
    # 0x04 = MB_YESNO, 0x20 = MB_ICONQUESTION, 0x100 = MB_DEFBUTTON2
    result = ctypes.windll.user32.MessageBoxW(0, message, title, 0x04 | 0x20)
    return result == 6  # 6 is IDYES

def ask_string(title: str, message: str, initial_value: str = "") -> Optional[str]:
    """
    Mostra uma caixa de entrada (Input) pedindo um texto.
    Usamos tkinter injetado para não depender de pacotes de terceiros pesados.
    O campo já abre preenchido com `initial_value` se fornecido.
    """
    try:
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal

        # Faz a janela popup aparecer na frente de tudo
        root.attributes("-topmost", True)

        result = simpledialog.askstring(title, message, parent=root, initialvalue=initial_value)

        root.destroy()
        return result
    except Exception as e:
        print(f"Erro ao abrir InputBox: {e}")
        return None
