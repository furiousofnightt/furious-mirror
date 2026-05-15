import os
import sys
import ctypes
import traceback

# Get the path where the EXE is located (not the temp folder)
def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

_log_cleared = False

# DEBUG: Create a small log file in the EXE directory
def debug_log(msg):
    global _log_cleared
    try:
        log_path = os.path.join(get_exe_dir(), "furious_debug.log")
        mode = "a" if _log_cleared else "w"
        with open(log_path, mode, encoding='utf-8') as f:
            f.write(f"{msg}\n")
        _log_cleared = True
    except: pass

# SDL2 DLL CONFIGURATION - MUST BE FIRST
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    sdl2_path = os.path.join(base_path, 'sdl2_bins')
    os.environ["PYSDL2_DLL_PATH"] = sdl2_path
    debug_log(f"EXE mode: Setting PYSDL2_DLL_PATH to {sdl2_path}")
    
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(sdl2_path)
        except Exception as e:
            debug_log(f"Error adding DLL directory: {e}")

from app.main import main

if __name__ == "__main__":
    try:
        if os.name == 'nt':
            try:
                winmm = ctypes.WinDLL('winmm')
                winmm.timeBeginPeriod(1)
            except Exception:
                pass
        
        debug_log("Starting main application...")
        main()
        debug_log("Application exited normally.")
        
    except Exception as e:
        error_msg = traceback.format_exc()
        debug_log("\n--- CRITICAL ERROR ---")
        debug_log(error_msg)
        debug_log("----------------------\n")
        
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(0, f"Critical Error:\n{e}\n\nCheck furious_debug.log for details.", "Furious Mirror Error", 0x10)
