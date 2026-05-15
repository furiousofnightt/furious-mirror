import subprocess
import os
import time
import threading
import sys
import shutil
from .util.log import logger
from .options import Options

class Server:
    def __init__(self, serial: str, options: Options):
        self.serial = serial
        self.options = options
        self.process = None
        self.scid = 0 
        self.is_wireless = False
        self.skip_kill_server = False  # Setado True durante transição wireless

    def _get_base_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _ensure_portables(self):
        from run import debug_log
        base_dir = self._get_base_path()
        target_adb_dir = os.path.join(base_dir, "portables", "adb")
        
        if getattr(sys, 'frozen', False) and not os.path.exists(target_adb_dir):
            debug_log("Extracting ADB to local folder...")
            try:
                os.makedirs(target_adb_dir, exist_ok=True)
                mei_dir = sys._MEIPASS
                # Extrair ADB
                src_adb_dir = os.path.join(mei_dir, "portables", "adb")
                if os.path.exists(src_adb_dir):
                    for item in os.listdir(src_adb_dir):
                        shutil.copy2(os.path.join(src_adb_dir, item), os.path.join(target_adb_dir, item))
                
                # Extrair IMAGES
                target_img_dir = os.path.join(base_dir, "portables", "images")
                os.makedirs(target_img_dir, exist_ok=True)
                src_img_dir = os.path.join(mei_dir, "portables", "images")
                if os.path.exists(src_img_dir):
                    for item in os.listdir(src_img_dir):
                        shutil.copy2(os.path.join(src_img_dir, item), os.path.join(target_img_dir, item))

            except Exception as e:
                debug_log(f"Extraction error: {e}")

    def _get_adb_path(self):
        base_dir = self._get_base_path()
        return os.path.abspath(os.path.join(base_dir, "portables", "adb", "adb.exe"))

    def _get_server_path(self):
        base_dir = self._get_base_path()
        return os.path.abspath(os.path.join(base_dir, "portables", "adb", "furious-core.jar"))

    def start(self) -> str:
        from run import debug_log
        self._ensure_portables()
        adb_path = self._get_adb_path()
        server_path = self._get_server_path()
        
        def run_adb(args, timeout=15.0):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return subprocess.run([adb_path] + args, capture_output=True, text=True, startupinfo=startupinfo, timeout=timeout)

        debug_log("Checking current ADB status...")
        try:
            res = run_adb(["devices"])
            if 'device' not in res.stdout and 'unauthorized' not in res.stdout:
                debug_log("No devices active. Resetting ADB server...")
                run_adb(["kill-server"], timeout=5.0)
                time.sleep(1.0)
                run_adb(["start-server"], timeout=15.0)
        except Exception as e:
            debug_log(f"ADB initialization warning: {e}")

        debug_log("Searching for authorized device...")
        last_status = "NO_DEVICE"
        for i in range(10):
            try:
                res = run_adb(["devices"])
                output = res.stdout.strip()
                debug_log(f"Attempt {i+1}: {output}")
                
                lines = output.split('\n')[1:]
                devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
                
                if devices:
                    # Prioriza o serial já configurado (ex: via Wi-Fi já conectado antes)
                    if self.serial and self.serial in devices:
                        pass  # mantém o self.serial configurado
                    else:
                        self.serial = devices[0]
                    debug_log(f"Connected to {self.serial}")
                    last_status = "OK"
                    
                    # Detecta automaticamente se já é uma conexão IP (sem cabo)
                    if "." in self.serial and ":" in self.serial:
                        self.is_wireless = True
                        debug_log(f"Wireless mode detected (IP: {self.serial})")
                    break
                
                if 'unauthorized' in output:
                    last_status = "UNAUTHORIZED"
                    debug_log("Waiting for user authorization...")
                else:
                    last_status = "NO_DEVICE"
                
                time.sleep(1.5)
            except Exception as e:
                debug_log(f"Attempt {i+1} failed: {e}")
                time.sleep(1.0)

        if last_status != "OK":
            return last_status

        debug_log(f"Pushing Furious Engine to {self.serial}...")
        try:
            run_adb(["-s", self.serial, "push", server_path, "/data/local/tmp/furious-core.jar"])
        except Exception as e:
            debug_log(f"Push error: {e}")
            return "PUSH_FAILED"

        # Bitrates fixos para máxima estabilidade sem reinícios
        if self.is_wireless:
            video_bitrate = 6_000_000 # 6 Mbps (Ideal para Wi-Fi)
        else:
            video_bitrate = 8_000_000 # 8 Mbps (Ideal para Cabo)

        debug_log(f"[Server] Bitrate definido: {video_bitrate // 1_000_000} Mbps ({'Wi-Fi' if self.is_wireless else 'USB'})")

        cmd = [adb_path, "-s", self.serial, "shell", "CLASSPATH=/data/local/tmp/furious-core.jar",
               "app_process", "/", "com.genymobile.scrcpy.Server", "3.3.4",
               f"scid={self.scid:08x}", "log_level=info", "video=true", "audio=true",
               "control=true", "tunnel_forward=true", "send_dummy_byte=true",
               "send_device_meta=false", "send_codec_meta=true", "send_frame_meta=true",
               f"video_bit_rate={video_bitrate}", "audio_bit_rate=128000", "stay_awake=true"]
            
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        
        def consume(stream, prefix):
            try:
                for line in stream:
                    l = line.decode("utf-8", "ignore").strip()
                    if l: logger.info(f"[{prefix}] {l}")
            except: pass

        threading.Thread(target=consume, args=(self.process.stdout, "SERVER-OUT"), daemon=True).start()
        threading.Thread(target=consume, args=(self.process.stderr, "SERVER-ERR"), daemon=True).start()
        
        time.sleep(2.5)
        if self.process.poll() is not None:
            debug_log("Error: Server process died unexpectedly")
            return "SERVER_START_FAILED"
            
        return "OK"

    def stop(self):
        if self.process: self.process.terminate()
        if not self.skip_kill_server:
            try:
                adb_path = self._get_adb_path()
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run([adb_path, "kill-server"], capture_output=True, startupinfo=startupinfo, timeout=3.0)
            except Exception:
                pass

