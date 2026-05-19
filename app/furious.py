import time
import socket
import subprocess
import threading
import queue
import random
import struct
import sdl2
from .options import Options
from .server import Server
from .demuxer import Demuxer
from .decoder import Decoder
from .screen import Screen
from .audio_player import AudioPlayer
from .control_msg import ControlMsg, ControlMsgType, CopyKey
from .util.log import logger
from .util.msgbox import show_error, show_question
from .wireless import WirelessManager
from .adaptive import AdaptiveBitrateController

class FuriousMirror:
    def __init__(self, options: Options):
        self.options = options
        self.server = None
        self.screen = None
        self.video_demuxer = None
        self.video_decoder = None
        self.audio_demuxer = None
        self.audio_decoder = None
        self.audio_player = None
        self.stopped = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.control_queue = queue.Queue(maxsize=60)
        self.video_socket = None
        self.audio_socket = None
        self.control_socket = None
        self.mouse_down = False
        self.scid = random.randint(0, 0x7FFFFFFF)
        self._stop_event = threading.Event()
        self.reconnect_requested = False
        self.connection_lost = False
        self.wireless_mgr = None
        self._wireless_transition = False
        self.abr = None
        self._window_focused = True  # False quando janela esta em segundo plano

    def start(self):
        logger.info(f"Starting Furious Mirror Engine [id={self.scid:08x}]...")
        from run import debug_log
        
        # Inicializa a janela 50% menor para o loading (ela cresce sozinha depois)
        self.screen = Screen("Furious Mirror", 640, 360)
        if not self.screen.init_sdl():
            debug_log("Error: SDL initialization failed")
            self.stop()
            return
            
        self.screen.set_on_sdl_event_callback(self.on_sdl_event)
        self.screen.draw_loading_screen()
        
        debug_log("Step: Starting ADB server...")
        self.server = Server(self.options.serial, self.options)
        self.server.scid = self.scid
        
        server_status = None
        def run_server():
            nonlocal server_status
            server_status = self.server.start()
            
        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        
        # Keep screen alive while ADB connects
        frame = 0
        phases = [
            (0, "Sistema: INICIANDO NÚCLEO FURIOUS..."),
            (70, "Localizando: INTERFACE NEURAL USB..."),
            (140, "Autenticando: QUEBRANDO PROTOCOLO ADB..."),
            (210, "Injetando: CARGA DE DADOS FURIOUS..."),
            (280, "Conectando: ESTABELECENDO ROTA TCP..."),
            (350, "Sincronizando: CONSTRUÇÃO DO ESPELHO ATIVA")
        ]
        
        while server_thread.is_alive() and not self.stopped:
            if not self.screen.handle_events():
                self.stopped = True
                
            current_text = phases[-1][1]
            if getattr(self.server, 'is_wireless', False) and frame >= phases[-1][0]:
                current_text = "Sincronizando: ESPELHO WIRELESS ATIVO"
                
            for limit, text in reversed(phases):
                if frame >= limit:
                    if limit != phases[-1][0]:
                        current_text = text
                    break
                    
            self.screen.draw_loading_screen(frame, current_text)
            frame += 1
            time.sleep(0.02)
            
        if self.stopped:
            self.stop()
            return
            
        if server_status != "OK":
            debug_log(f"Error: Server failed to start ({server_status})")
            if server_status == "NO_DEVICE":
                from .util.dialogs import ask_yes_no, ask_string
                quer_wifi = ask_yes_no(
                    "Furious Mirror - Nenhum Dispositivo",
                    "Nenhum celular encontrado via cabo USB.\n\n"
                    "Deseja conectar via Wi-Fi digitando o IP do celular?\n\n"
                    "• SIM  ->  Digitar o IP para conexao sem fio\n"
                    "• NAO  ->  Conectar o cabo USB e tentar novamente"
                )
                if quer_wifi:
                    ip_input = ask_string(
                        "Furious Mirror - Conexao sem fio",
                        "Digite o endereco IP do celular:\n"
                        "(Exemplo: 192.168.1.15  ou  192.168.1.15:5555)"
                    )
                    if ip_input and ip_input.strip():
                        ip = ip_input.strip()
                        if ":" not in ip:
                            ip += ":5555"
                        # Tenta conectar via ADB wireless
                        adb_path = self.server._get_adb_path()
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        res = subprocess.run(
                            [adb_path, "connect", ip],
                            capture_output=True, text=True,
                            startupinfo=startupinfo, timeout=10.0
                        )
                        
                        if not ("connected to" in res.stdout.lower() or "already connected" in res.stdout.lower()):
                            debug_log("[Wireless] Falha na primeira tentativa. Reiniciando ADB server...")
                            subprocess.run([adb_path, "kill-server"], capture_output=True, startupinfo=startupinfo, timeout=5.0)
                            subprocess.run([adb_path, "start-server"], capture_output=True, startupinfo=startupinfo, timeout=15.0)
                            res = subprocess.run(
                                [adb_path, "connect", ip],
                                capture_output=True, text=True,
                                startupinfo=startupinfo, timeout=10.0
                            )

                        if "connected to" in res.stdout.lower() or "already connected" in res.stdout.lower():
                            debug_log(f"[Wireless] Conectado via IP manual: {ip}")
                            self.options.serial = ip
                            self.server.skip_kill_server = True
                            self.reconnect_requested = True
                            self.stop()
                            return
                        else:
                            show_error("Furious Mirror", f"Nao foi possivel conectar ao IP '{ip}'.\n\nVerifique se:\n• O celular esta na mesma rede Wi-Fi\n• O modo de depuracao sem fio esta ativo")
                    else:
                        # Usuário cancelou o input — volta para esperar cabo
                        self.reconnect_requested = True
                else:
                    # Usuário quer usar o cabo — pede para conectar e tenta de novo
                    show_error("Furious Mirror",
                               "Conecte o cabo USB ao celular,\nactive a 'Depuracao USB' e abra o app novamente.")
            elif server_status == "UNAUTHORIZED":
                show_error("Furious Mirror", "Dispositivo nao autorizado.\n\nPor favor, aceite a permissao de depuracao USB na tela do seu celular e tente novamente.")
            else:
                show_error("Furious Mirror", f"Falha ao iniciar o servidor ADB: {server_status}")
            self.stop()
            return

        adb_path = self.server._get_adb_path()
        socket_name = f"scrcpy_{self.scid:08x}"
        
        debug_log(f"Step: Setting up ADB forward for {socket_name}...")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        serial_args = ["-s", self.server.serial] if self.server.serial else []
        subprocess.run([adb_path] + serial_args + ["forward", "--remove", "tcp:27183"], capture_output=True, startupinfo=startupinfo)
        try:
            subprocess.run([adb_path] + serial_args + ["forward", "tcp:27183", f"localabstract:{socket_name}"], check=True, startupinfo=startupinfo)
        except Exception as e:
            debug_log(f"Error: ADB forward failed: {e}")
            self.stop()
            return

        debug_log("Step: Connecting to sockets...")
        time.sleep(1.5) 
        
        try:
            if self.options.video:
                self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.video_socket.connect(("127.0.0.1", 27183))
                dummy = self.video_socket.recv(1)
                logger.debug("Video stream connected")
            
            if self.options.audio:
                self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.audio_socket.connect(("127.0.0.1", 27183))
                logger.debug("Audio stream connected")
                
            if self.options.control:
                self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.control_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.control_socket.connect(("127.0.0.1", 27183))
                logger.debug("Control stream connected")
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.stop()
            return

        if self.video_socket:
            self.video_demuxer = Demuxer("video", self.video_socket)
            self.video_demuxer.daemon = True
            self.video_decoder = Decoder("video")
            self.video_decoder.open("h264")
            self.video_demuxer.add_on_packet_callback(self.video_decoder.push)
            
            def on_frame(frame):
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass  # run_event_loop vai descartar excedentes com pacing correto

            
            self.video_decoder.add_on_frame_callback(on_frame)
            self.video_demuxer.add_on_error_callback(self.on_connection_error)
            self.video_demuxer.start()

        if self.audio_socket:
            self.audio_demuxer = Demuxer("audio", self.audio_socket)
            self.audio_demuxer.daemon = True
            self.audio_decoder = Decoder("audio")
            self.audio_decoder.open("opus")
            self.audio_player = AudioPlayer()
            self.audio_player.open(48000, 2)
            
            self.audio_demuxer.add_on_packet_callback(self.audio_decoder.push)
            self.audio_decoder.add_on_frame_callback(self.audio_player.play)
            self.audio_demuxer.add_on_error_callback(self.on_connection_error)
            self.audio_demuxer.start()

        if self.control_socket:
            threading.Thread(target=self.control_worker, daemon=True).start()
            threading.Thread(target=self.control_receiver, daemon=True).start()

        # Iniciar tray icon de Wi-Fi em background
        try:
            self.wireless_mgr = WirelessManager(
                adb_path=self.server._get_adb_path(),
                on_reconnect_callback=self._on_wireless_reconnect,
                on_transition_start=self._on_wireless_transition_start
            )
            self.wireless_mgr.start_tray(
                usb_serial=self.server.serial or "",
                is_wireless=getattr(self.server, 'is_wireless', False)
            )

        except Exception as e:
            debug_log(f"Wireless tray warning: {e}")

        # Ativar o monitor de performance para todas as conexões (USB e Wi-Fi)
        from .adaptive import AdaptiveBitrateController
        self.abr = AdaptiveBitrateController(lambda x: None)
        
        # Define o bitrate inicial no monitor para o log ficar correto
        if getattr(self.server, 'is_wireless', False):
            self.abr.current_bitrate = 6_000_000
        else:
            self.abr.current_bitrate = 8_000_000
            
        self.abr.start(is_wireless=True) # Ativa logs

        try:
            self.run_event_loop()
        finally:
            self.stop()
            if self.connection_lost:
                is_wifi = getattr(self.server, 'is_wireless', False)
                msg_texto = "A conexão com o dispositivo foi perdida.\n\nVerifique a rede Wi-Fi." if is_wifi else "A conexão com o dispositivo foi perdida.\n\nVerifique o cabo USB."
                if show_question("Furious Mirror", f"{msg_texto}\n\nDeseja tentar reconectar?"):
                    self.reconnect_requested = True

    def control_worker(self):
        while not self.stopped:
            try:
                msg = self.control_queue.get(timeout=0.5)
                if msg is None: break
                self.control_socket.sendall(msg.serialize())
            except queue.Empty: continue
            except Exception as e:
                logger.error(f"Control error: {e}")
                self.on_connection_error()
                break

    def control_receiver(self):
        while not self.stopped:
            try:
                data = self.control_socket.recv(4096)
                if not data:
                    self.on_connection_error()
                    break
            except Exception:
                self.on_connection_error()
                break

    def on_connection_error(self):
        # Durante troca para Wi-Fi, a desconexão USB é ESPERADA. Ignorar.
        if self._wireless_transition:
            return
        if getattr(self, '_is_stopping', False):
            return
        if not self.connection_lost:
            self.connection_lost = True
            self.stopped = True

    def _on_wireless_transition_start(self, undo=False):
        """
        Chamado ANTES do adb tcpip rodar para suprimir o on_connection_error
        que vai disparar quando a sessao USB cair intencionalmente.
        """
        self._wireless_transition = not undo

    def _on_wireless_reconnect(self, new_ip):
        """
        Callback chamado pelo WirelessManager quando muda o modo de conexão.
        new_ip = string -> reconectar via Wi-Fi
        new_ip = None   -> voltar para cabo USB
        """
        from run import debug_log
        if new_ip:
            debug_log(f"[Wireless] Reconectando com novo IP: {new_ip}")
            # Preserva o ADB daemon (não mata o servidor)
            if self.server:
                self.server.skip_kill_server = True
            self.options.serial = new_ip
        else:
            debug_log("[Wireless] Voltando para cabo USB...")
            # Ao voltar para USB, reset do serial (auto-detecção)
            self.options.serial = None
        self.reconnect_requested = True
        self.stopped = True

    def on_sdl_event(self, event):
        msg = None
        if event.type in [sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP, sdl2.SDL_MOUSEMOTION]:
            msg = self.process_mouse_event(event)
        elif event.type == sdl2.SDL_MOUSEWHEEL:
            msg = self.process_scroll_event(event)
        elif event.type in [sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP]:
            msg = self.process_key_event(event)
        elif event.type == sdl2.SDL_WINDOWEVENT:
            we = event.window.event
            if we == sdl2.SDL_WINDOWEVENT_MINIMIZED:
                self._window_focused = False
                if self.abr:
                    self.abr.set_paused(True)
            elif we == sdl2.SDL_WINDOWEVENT_RESTORED:
                self._window_focused = True
                if self.abr:
                    self.abr.set_paused(False)
                    self.abr.pause(duration=2.0)

            elif we in (
                sdl2.SDL_WINDOWEVENT_MOVED,
                sdl2.SDL_WINDOWEVENT_RESIZED,
                sdl2.SDL_WINDOWEVENT_SIZE_CHANGED,
                sdl2.SDL_WINDOWEVENT_MINIMIZED,
            ):
                pass





        if msg:
            try:
                self.control_queue.put_nowait(msg)
            except queue.Full:
                if msg.type == ControlMsgType.INJECT_TOUCH_EVENT and event.type == sdl2.SDL_MOUSEMOTION:
                    pass 
                else:
                    try: 
                        self.control_queue.get_nowait()
                        self.control_queue.put_nowait(msg)
                    except: pass

    def process_mouse_event(self, event):
        action = 0
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            action = 0 
            self.mouse_down = True
        elif event.type == sdl2.SDL_MOUSEBUTTONUP:
            action = 1 
            self.mouse_down = False
        elif event.type == sdl2.SDL_MOUSEMOTION:
            if not self.mouse_down:
                return None
            action = 2 
        
        # Usa a area real do video (com offset de letterboxing)
        # Isso corrige o deslocamento de cliques quando ha barras pretas
        vx, vy, vw, vh = self.screen._video_rect
        x = event.button.x if event.type != sdl2.SDL_MOUSEMOTION else event.motion.x
        y = event.button.y if event.type != sdl2.SDL_MOUSEMOTION else event.motion.y
        # Clip dentro da area do video
        x = max(vx, min(vx + vw, x))
        y = max(vy, min(vy + vh, y))
        # Mapeia de coordenadas da janela para coordenadas do celular
        real_x = int((x - vx) * self.screen.width / vw)
        real_y = int((y - vy) * self.screen.height / vh)
        return ControlMsg(
            type=ControlMsgType.INJECT_TOUCH_EVENT,
            action=action,
            pointer_id=-2,
            x=real_x,
            y=real_y,
            width=self.screen.width,
            height=self.screen.height,
            pressure=1.0 if self.mouse_down else 0.0,
            buttons=1
        )

    def process_scroll_event(self, event):
        import ctypes
        mx, my = ctypes.c_int(0), ctypes.c_int(0)
        sdl2.SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
        
        vx, vy, vw, vh = self.screen._video_rect
        x = max(vx, min(vx + vw, mx.value))
        y = max(vy, min(vy + vh, my.value))
        real_x = int((x - vx) * self.screen.width / vw)
        real_y = int((y - vy) * self.screen.height / vh)
        
        hscroll = float(event.wheel.x)
        # Em SDL, scroll do mouse no Windows: y > 0 = rodou para frente (subir na pagina). Android rola na mesma direção.
        vscroll = float(event.wheel.y)
        
        msg = ControlMsg(
            type=ControlMsgType.INJECT_SCROLL_EVENT,
            x=real_x,
            y=real_y,
            width=self.screen.width,
            height=self.screen.height,
            hscroll=hscroll,
            vscroll=vscroll,
            buttons=0
        )
        return msg

    def process_key_event(self, event):
        action = 0 if event.type == sdl2.SDL_KEYDOWN else 1
        sym = event.key.keysym.sym
        
        # Mapping SDL keys to Android Keycodes
        # Standard: https://developer.android.com/reference/android/view/KeyEvent
        keycode = 0
        if sym == sdl2.SDLK_ESCAPE: keycode = 4 
        elif sym == sdl2.SDLK_HOME: keycode = 3 
        elif sym == sdl2.SDLK_BACKSPACE: keycode = 67
        elif sym == sdl2.SDLK_SPACE: keycode = 62
        elif sym == sdl2.SDLK_RETURN or sym == sdl2.SDLK_KP_ENTER: keycode = 66
        elif sym >= sdl2.SDLK_a and sym <= sdl2.SDLK_z:
            keycode = 29 + (sym - sdl2.SDLK_a) # A=29 to Z=54
        elif sym >= sdl2.SDLK_0 and sym <= sdl2.SDLK_9:
            keycode = 7 + (sym - sdl2.SDLK_0) # 0=7 to 9=16
        elif sym == sdl2.SDLK_BACKQUOTE: keycode = 68 # Use for special symbols or keep simple
        
        if keycode == 0:
            return None
            
        return ControlMsg(
            type=ControlMsgType.INJECT_KEYCODE,
            action=action,
            keycode=keycode,
            repeat=0,
            metastate=0
        )

    def run_event_loop(self):
        while not self.stopped:
            if not self.screen.handle_events():
                self.stopped = True

            frame = None
            try:
                frame = self.frame_queue.get_nowait()
                # Drena excedentes (mini-buffer de 4 frames para evitar engasgos de rede)
                while self.frame_queue.qsize() > 4:
                    frame = self.frame_queue.get_nowait()
                    if self.abr and self._window_focused:
                        self.abr.report_frame_drop()
            except queue.Empty:
                pass

            # So renderiza quando a janela nao esta minimizada
            if frame and self._window_focused:
                self.screen.update_frame(frame)
                if self.abr:
                    self.abr.report_frame_ok()


            time.sleep(0.001)




    def stop(self):
        if getattr(self, '_is_stopping', False): return
        self._is_stopping = True
        self.stopped = True
        logger.info("Stopping Furious Mirror Engine...")
        
        # 1. Kill sockets first to unblock threads
        for sock in [self.video_socket, self.audio_socket, self.control_socket]:
            if sock:
                try: 
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except: pass
        
        # 2. Stop demuxers
        if self.video_demuxer: self.video_demuxer.stop()
        if self.audio_demuxer: self.audio_demuxer.stop()
        
        # 3. Clean up ADB in a separate thread if needed (to not block UI)
        def cleanup_adb():
            try:
                # Use the already optimized path method from server
                adb_path = self.server._get_adb_path()
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run([adb_path, "forward", "--remove", "tcp:27183"], capture_output=True, startupinfo=startupinfo, timeout=1.0)
            except: pass
            
        threading.Thread(target=cleanup_adb, daemon=True).start()
        
        if self.server: self.server.stop()
        if self.screen: self.screen.close()
        if self.audio_player: self.audio_player.close()
        if self.wireless_mgr: self.wireless_mgr.stop_tray()
        if self.abr: self.abr.stop()
