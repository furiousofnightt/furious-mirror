"""
wireless.py — Gerenciador de conexão sem fio do Furious Mirror.
Este módulo é totalmente isolado do fluxo principal (USB).
Ele cria um ícone na bandeja do sistema Windows com opções de Wi-Fi.
"""
import subprocess
import threading
import time
import re
import ctypes
import ctypes.wintypes
import queue
from .util.log import logger


# --- Constantes Win32 para Tray Icon ---
WM_APP = 0x8000
WM_TRAY_MSG = WM_APP + 1
NIM_ADD = 0x00
NIM_DELETE = 0x02
NIM_MODIFY = 0x01
NIF_MESSAGE = 0x01
NIF_ICON = 0x02
NIF_TIP = 0x04
WM_RBUTTONUP = 0x0205
WM_LBUTTONDOWN = 0x0201
TPM_RIGHTBUTTON = 0x0002
MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MIIM_ID = 0x02
MIIM_STRING = 0x40

# IDs de menu do tray
MENU_WIFI_HYBRID    = 1001
MENU_WIFI_IP        = 1002
MENU_USB_RECONNECT  = 1003  # Volta para cabo USB
MENU_SEPARATOR      = 0
MENU_EXIT           = 1099


class WirelessManager:
    """
    Gerencia a conexão sem fio de forma isolada.
    O Tray Icon do Windows dá ao usuário o controle total sobre quando ativar o Wi-Fi.
    """
    def __init__(self, adb_path: str, on_reconnect_callback=None, on_transition_start=None):
        self.adb_path = adb_path
        self.on_reconnect_callback = on_reconnect_callback
        self.on_transition_start = on_transition_start  # Chamado ANTES da desconexão USB
        self.is_wireless = False
        self.connected_ip = None
        self._tray_thread = None
        self._tray_hwnd = None
        self._action_queue = queue.Queue()
        self._current_usb_serial = None
        self._running = False

    def _run_adb(self, args, timeout=15.0):
        from run import debug_log
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            return subprocess.run(
                [self.adb_path] + args,
                capture_output=True, text=True,
                startupinfo=startupinfo, timeout=timeout
            )
        except Exception as e:
            debug_log(f"ADB wireless error: {e}")
            return None

    def start_tray(self, usb_serial: str, is_wireless: bool = False):
        """Inicia o ícone de bandeja em uma thread separada."""
        self._current_usb_serial = usb_serial
        self.is_wireless = is_wireless

        self._running = True
        self._tray_thread = threading.Thread(target=self._tray_main_loop, daemon=True)
        self._tray_thread.start()
        # Thread de processamento de ações
        threading.Thread(target=self._process_actions, daemon=True).start()

    def stop_tray(self):
        """Remove o ícone da bandeja."""
        self._running = False

    def connect_direct_ip(self, ip_with_port: str) -> bool:
        """Conecta ao dispositivo diretamente via IP (sem cabo)."""
        from run import debug_log
        if ":" not in ip_with_port:
            ip_with_port += ":5555"

        debug_log(f"[Wireless] Tentando conexão direta ao IP: {ip_with_port}")
        res = self._run_adb(["connect", ip_with_port], timeout=10.0)
        if res and ("connected to" in res.stdout.lower() or "already connected" in res.stdout.lower()):
            self.is_wireless = True
            self.connected_ip = ip_with_port
            debug_log(f"[Wireless] Conectado com sucesso: {ip_with_port}")
            return True
        debug_log(f"[Wireless] Falha: {res.stdout if res else 'timeout'}")
        return False

    def activate_hybrid_mode(self, usb_serial: str) -> bool:
        """Ativa modo Wi-Fi a partir de uma conexão USB existente."""
        from run import debug_log
        debug_log(f"[Wireless] Ativando modo híbrido para {usb_serial}...")

        # 1. Ativar modo tcpip no celular
        self._run_adb(["-s", usb_serial, "tcpip", "5555"])
        time.sleep(2.0)

        # 2. Pegar o IP do celular (tentativa robusta)
        # Tenta primeiro via 'ip route' para pegar a interface principal
        ip = None
        res = self._run_adb(["-s", usb_serial, "shell", "ip", "route"])
        if res and res.stdout:
            # Procura por "src 192.168.x.x" ou "src 10.x.x.x"
            match = re.search(r'src\s+(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+)', res.stdout)
            if match:
                ip = match.group(1)

        if not ip:
            # Fallback: lista todas as interfaces e procura por um IP de rede local
            res = self._run_adb(["-s", usb_serial, "shell", "ip", "-f", "inet", "addr", "show"])
            if res and res.stdout:
                # Pega o primeiro IP que pareça ser de rede local (privado)
                matches = re.findall(r'inet\s+(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+)', res.stdout)
                if matches:
                    # matches é uma lista de tuplas devido aos grupos do regex, pegamos o primeiro IP da primeira tupla
                    ip = matches[0][0]

        if not ip:
            debug_log("[Wireless] Não foi possível encontrar um IP válido. O Wi-Fi do celular está ligado?")
            return False

        ip_with_port = f"{ip}:5555"
        debug_log(f"[Wireless] IP detectado com sucesso: {ip_with_port}. Conectando...")

        # 3. Conectar via IP
        connect_res = self._run_adb(["connect", ip_with_port])
        if connect_res and ("connected to" in connect_res.stdout.lower() or "already connected" in connect_res.stdout.lower()):
            self.is_wireless = True
            self.connected_ip = ip_with_port
            debug_log(f"[Wireless] Modo híbrido ativo! IP: {ip_with_port}")
            return True


        debug_log(f"[Wireless] Falha ao conectar: {connect_res.stdout if connect_res else 'timeout'}")
        return False

    def _process_actions(self):
        """Processa ações do menu da bandeja em background."""
        from run import debug_log
        while self._running:
            try:
                action = self._action_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if action == MENU_WIFI_HYBRID:
                serial = self._current_usb_serial
                if not serial or ("." in serial and ":" in serial):
                    self._show_msg("Modo Hibrido", "Nenhum cabo USB detectado.\nConecte o cabo e tente novamente.")
                    continue

                # CRITICO: sinaliza transicao ANTES de rodar o adb tcpip
                if self.on_transition_start:
                    self.on_transition_start()

                ok = self.activate_hybrid_mode(serial)
                if ok:
                    self._show_msg("Wi-Fi Ativado!", f"Conexao sem fio estabelecida!\nIP: {self.connected_ip}\n\nVoce pode remover o cabo agora.\nO app vai reconectar automaticamente.")
                    if self.on_reconnect_callback:
                        self.on_reconnect_callback(self.connected_ip)
                else:
                    if self.on_transition_start:
                        self.on_transition_start(undo=True)
                    self._show_msg("Erro", "Nao foi possivel ativar o Wi-Fi.\nVerifique se o celular esta conectado ao roteador.")

            elif action == MENU_WIFI_IP:
                from .util.dialogs import ask_string
                ip_input = ask_string(
                    "Furious Mirror - Conectar por IP",
                    "Digite o IP e porta do celular:\n(Exemplo: 192.168.1.15 ou 192.168.1.15:5555)"
                )
                if not ip_input:
                    continue
                if self.on_transition_start:
                    self.on_transition_start()
                ok = self.connect_direct_ip(ip_input.strip())
                if ok:
                    self._show_msg("Wi-Fi Ativado!", f"Conexao sem fio estabelecida!\nIP: {self.connected_ip}\n\nO espelho vai reconectar automaticamente.")
                    if self.on_reconnect_callback:
                        self.on_reconnect_callback(self.connected_ip)
                else:
                    if self.on_transition_start:
                        self.on_transition_start(undo=True)
                    self._show_msg("Erro", f"Nao foi possivel conectar ao IP '{ip_input}'.\nVerifique se o celular esta na mesma rede Wi-Fi.")

            elif action == MENU_USB_RECONNECT:
                debug_log("[Wireless] Voltando para modo cabo USB...")
                # Desconecta o IP wireless do ADB
                if self.connected_ip:
                    self._run_adb(["disconnect", self.connected_ip])
                self.is_wireless = False
                self.connected_ip = None
                # Sinaliza reconexao via USB (serial=None = auto-detect USB)
                if self.on_reconnect_callback:
                    self.on_reconnect_callback(None)

    def _show_msg(self, title: str, msg: str):
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)

    # --- Tray Icon Win32 nativo ---
    def _tray_main_loop(self):
        """Cria e gerencia o ícone de bandeja usando Win32 puro."""
        from run import debug_log
        try:
            shell32 = ctypes.windll.shell32
            user32  = ctypes.windll.user32

            # Tipos 64-bit corretos para Windows x64:
            # LRESULT  = c_ssize_t  (signed  pointer-sized)
            # WPARAM   = c_size_t   (unsigned pointer-sized)
            # LPARAM   = c_ssize_t  (signed  pointer-sized)
            WNDPROC = ctypes.WINFUNCTYPE(
                ctypes.c_ssize_t,          # LRESULT (retorno)
                ctypes.wintypes.HWND,
                ctypes.c_uint,             # UINT msg
                ctypes.c_size_t,           # WPARAM
                ctypes.c_ssize_t           # LPARAM
            )

            # Configurar argtypes do DefWindowProcW explicitamente
            user32.DefWindowProcW.restype  = ctypes.c_ssize_t
            user32.DefWindowProcW.argtypes = [
                ctypes.wintypes.HWND,
                ctypes.c_uint,
                ctypes.c_size_t,
                ctypes.c_ssize_t
            ]

            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == WM_TRAY_MSG:
                    if lparam in (WM_RBUTTONUP, WM_LBUTTONDOWN):
                        self._show_tray_menu(hwnd)
                    return 0
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

            proc = WNDPROC(wnd_proc)

            class WNDCLASS(ctypes.Structure):
                _fields_ = [("style", ctypes.c_uint), ("lpfnWndProc", WNDPROC),
                             ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                             ("hInstance", ctypes.wintypes.HANDLE), ("hIcon", ctypes.wintypes.HANDLE),
                             ("hCursor", ctypes.wintypes.HANDLE), ("hbrBackground", ctypes.wintypes.HANDLE),
                             ("lpszMenuName", ctypes.c_wchar_p), ("lpszClassName", ctypes.c_wchar_p)]

            wc = WNDCLASS()
            wc.lpfnWndProc = proc
            wc.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
            wc.lpszClassName = "FuriousMirrorTray"
            user32.RegisterClassW(ctypes.byref(wc))

            # Definir tipos para CreateWindowExW para evitar Overflow em 64-bit
            user32.CreateWindowExW.argtypes = [
                ctypes.c_ulong, ctypes.c_wchar_p, ctypes.c_wchar_p,
                ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                ctypes.wintypes.HWND, ctypes.wintypes.HMENU, ctypes.wintypes.HINSTANCE, ctypes.wintypes.LPVOID
            ]
            user32.CreateWindowExW.restype = ctypes.wintypes.HWND

            hwnd = user32.CreateWindowExW(
                0, wc.lpszClassName, wc.lpszClassName,
                0, 0, 0, 0, 0, 0, 0, wc.hInstance, 0
            )

            self._tray_hwnd = hwnd

            # Estrutura NOTIFYICONDATA (versão expandida para compatibilidade x64)
            class NOTIFYICONDATA(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_ulong),
                    ("hWnd", ctypes.wintypes.HWND),
                    ("uID", ctypes.c_uint),
                    ("uFlags", ctypes.c_uint),
                    ("uCallbackMessage", ctypes.c_uint),
                    ("hIcon", ctypes.wintypes.HANDLE),
                    ("szTip", ctypes.c_wchar * 128),
                    ("dwState", ctypes.c_ulong),
                    ("dwStateMask", ctypes.c_ulong),
                    ("szInfo", ctypes.c_wchar * 256),
                    ("uTimeoutOrVersion", ctypes.c_uint),
                    ("szInfoTitle", ctypes.c_wchar * 64),
                    ("dwInfoFlags", ctypes.c_ulong)
                ]

            nid = NOTIFYICONDATA()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
            nid.hWnd = hwnd
            nid.uID = 1
            nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
            nid.uCallbackMessage = WM_TRAY_MSG
            
            # Carrega o ícone customizado
            import sys, os as _os
            from run import debug_log
            
            debug_log("[Wireless] Iniciando criação da bandeja...")
            
            # Tenta primeiro a pasta ao lado do .exe (onde estao os portables)
            if getattr(sys, 'frozen', False):
                exe_dir = _os.path.dirname(sys.executable)
                mei_dir = sys._MEIPASS
                debug_log(f"[Wireless] Modo Frozen. EXE Dir: {exe_dir} | MEI Dir: {mei_dir}")
            else:
                exe_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
                mei_dir = exe_dir
                debug_log(f"[Wireless] Modo Dev. Base Dir: {exe_dir}")

            # Lista de tentativas (Prioridade: Pasta externa -> Pasta interna)
            attempts = [
                _os.path.join(exe_dir, "portables", "images", "furious-mirror.ico"),
                _os.path.join(mei_dir, "portables", "images", "furious-mirror.ico"),
                _os.path.join(exe_dir, "images", "furious-mirror.ico"),
                _os.path.join(mei_dir, "images", "furious-mirror.ico")
            ]
            
            ico_path = None
            for path in attempts:
                debug_log(f"[Wireless] Checando ícone em: {path}")
                if _os.path.exists(path):
                    ico_path = path
                    debug_log(f"[Wireless] Ícone encontrado: {path}")
                    break
            
            IMAGE_ICON    = 1
            LR_LOADFROMFILE = 0x00000010
            LR_DEFAULTSIZE  = 0x00000040
            
            if ico_path:
                hIcon = user32.LoadImageW(
                    None, ico_path, IMAGE_ICON,
                    0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                )
                debug_log(f"[Wireless] LoadImageW handle: {hIcon}")
            else:
                debug_log("[Wireless] Nenhum ícone encontrado. Usando fallback do Windows.")
                hIcon = user32.LoadIconW(0, 32516)  # fallback: ícone padrão do Windows

            nid.hIcon = hIcon
            nid.szTip = "Furious Mirror - Clique para opções Wi-Fi"

            res = shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
            debug_log(f"[Wireless] Shell_NotifyIconW (NIM_ADD) retorno: {res}")
            
            if res == 0:
                debug_log(f"[Wireless] ERRO CRÍTICO: Não foi possível adicionar o ícone à bandeja. Erro SDL/Win32: {ctypes.GetLastError()}")
            else:
                debug_log("[Wireless] Tray icon adicionado com sucesso à bandeja do Windows.")

            # Loop de mensagens Win32
            msg = ctypes.wintypes.MSG()
            while self._running:
                if user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                time.sleep(0.01)

            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            debug_log("[Wireless] Tray icon removido.")
        except Exception as e:
            debug_log(f"[Wireless] Erro no tray: {e}")

    def _show_tray_menu(self, hwnd):
        """Exibe o menu contextual inteligente baseado no modo de conexao atual."""
        user32 = ctypes.windll.user32
        hmenu = user32.CreatePopupMenu()
        MF_GRAYED = 0x00000001

        if self.is_wireless:
            # --- MODO WI-FI ATIVO ---
            user32.AppendMenuW(hmenu, MF_STRING | MF_GRAYED, 0, "Furious Mirror  |  Wi-Fi Ativo")
            user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)

            user32.AppendMenuW(hmenu, MF_STRING, MENU_USB_RECONNECT, "Voltar para Cabo USB")
            user32.AppendMenuW(hmenu, MF_STRING, MENU_WIFI_IP,       "Trocar endereco IP")
        else:
            # --- MODO USB ATIVO ---
            user32.AppendMenuW(hmenu, MF_STRING | MF_GRAYED, 0, "Furious Mirror  |  Cabo USB Ativo")
            user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
            user32.AppendMenuW(hmenu, MF_STRING, MENU_WIFI_HYBRID, "Ativar conexao Wi-Fi  (modo hibrido)")
            user32.AppendMenuW(hmenu, MF_STRING, MENU_WIFI_IP,     "Conectar por endereco IP")

        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(hmenu, MF_STRING, MENU_EXIT, "Encerrar Furious Mirror")

        pt = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(hwnd)
        cmd = user32.TrackPopupMenu(hmenu, TPM_RIGHTBUTTON | 0x0100, pt.x, pt.y, 0, hwnd, None)
        user32.DestroyMenu(hmenu)

        if cmd == MENU_WIFI_HYBRID:
            self._action_queue.put(MENU_WIFI_HYBRID)
        elif cmd == MENU_WIFI_IP:
            self._action_queue.put(MENU_WIFI_IP)
        elif cmd == MENU_USB_RECONNECT:
            self._action_queue.put(MENU_USB_RECONNECT)
        elif cmd == MENU_EXIT:
            import os, signal
            os.kill(os.getpid(), signal.SIGTERM)
