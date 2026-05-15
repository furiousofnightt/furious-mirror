import os
import sys
import logging

logger = logging.getLogger("furious")
logger.setLevel(logging.INFO)

# Formato de log
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# Handler para Console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler para Arquivo (furious_debug.log)
try:
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    log_path = os.path.join(log_dir, "furious_debug.log")
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception:
    pass
