import ctypes

def show_error(title, message):
    """Shows a Windows Error Message Box."""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10) # 0x10 = MB_ICONERROR

def show_info(title, message):
    """Shows a Windows Info Message Box."""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40) # 0x40 = MB_ICONINFORMATION

def show_question(title, message):
    """Shows a Windows Question Message Box with Yes/No buttons. Returns True if Yes."""
    # 0x24 = MB_ICONQUESTION | MB_YESNO
    res = ctypes.windll.user32.MessageBoxW(0, message, title, 0x24)
    return res == 6 # 6 = IDYES
