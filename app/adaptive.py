"""
adaptive.py — Monitor de Performance e Bitrate do Furious Mirror.

Monitora a saúde do stream de vídeo em tempo real através da taxa de frames 
DESCARTADOS (dropped frames) e calcula o FPS.

Nota de Design: Originalmente concebido como um Adaptive Bitrate (ABR) ativo, 
atualmente opera de forma PASSIVA (apenas telemetria/logs). O bitrate foi 
fixado em 6 Mbps (Wi-Fi) e 8 Mbps (Cabo), pois alterações dinâmicas causam 
reconectividade no stream, prejudicando a fluidez da experiência do usuário.
"""
import time
import threading
from collections import deque
from .util.log import logger


class AdaptiveBitrateController:
    # Configurações de bitrate Wi-Fi
    BITRATE_HIGH = 6_000_000   # 6 Mbps — qualidade total
    BITRATE_LOW  = 4_000_000   # 4 Mbps — estabilidade

    # Thresholds de decisão
    DROP_WINDOW_SEC     = 5.0   # Janela de observação de drops (segundos)
    DROP_THRESHOLD      = 8     # Nº de drops nessa janela para acionar downgrade
    RECOVERY_WINDOW_SEC = 30.0  # Segundos sem drops para tentar upgrade
    COOLDOWN_SEC        = 20.0  # Tempo mínimo entre trocas (evita flapping)

    def __init__(self, on_bitrate_change):
        """
        on_bitrate_change(new_bitrate: int) -> callback chamado quando decide trocar.
        """
        self.on_bitrate_change = on_bitrate_change
        self.current_bitrate   = self.BITRATE_HIGH
        self.enabled           = False  # Só ativo em modo Wi-Fi

        self._drop_times    = deque()
        self._frame_times   = deque()
        self._last_drop     = 0.0
        self._last_switch   = 0.0
        self._lock          = threading.Lock()
        self._total_drops   = 0
        self._last_status_log    = 0.0
        self._burst_ignore_until = 0.0
        self._paused             = False  # Pausa indefinida (janela sem foco)

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._running = False

    def start(self, is_wireless: bool):
        """Inicia o monitor. Só age em modo Wi-Fi."""
        self.enabled = is_wireless
        self._running = True
        self._monitor_thread.start()
        if is_wireless:
            logger.info("[MONITOR] Sistema de monitoramento de performance iniciado.")


    def pause(self, duration: float = 3.0):
        """Pausa por `duration` segundos (para eventos de janela breves como move/resize)."""
        with self._lock:
            self._burst_ignore_until = max(self._burst_ignore_until, time.time() + duration)

    def set_paused(self, paused: bool):
        """Pausa/retoma o ABR indefinidamente (para perda/ganho de foco da janela)."""
        with self._lock:
            self._paused = paused
        if paused:
            logger.debug("[ABR] Pausado (janela sem foco)")
        else:
            logger.debug("[ABR] Retomado (janela em foco)")
            # Limpa drops acumulados durante a pausa
            with self._lock:
                self._drop_times.clear()
                self._burst_ignore_until = 0.0
    def stop(self):
        self._running = False

    def report_frame_drop(self):
        if not self.enabled:
            return
        now = time.time()
        with self._lock:
            # Pausa indefinida por foco perdido
            if self._paused:
                return
            # Pausa temporaria por burst/move de janela
            if now < self._burst_ignore_until:
                return
            # Filtro de burst: 4+ drops em < 300ms = pausa de rendering
            recent_burst = sum(1 for t in self._drop_times if now - t < 0.30)
            if recent_burst >= 4:
                if self._burst_ignore_until < now:
                    logger.debug("[ABR] Burst de rendering detectado — ignorando drops")
                    self._burst_ignore_until = now + 3.0
                return
            self._drop_times.append(now)
            self._last_drop = now
            self._total_drops += 1
            count = len(self._drop_times)
        logger.debug(f"[ABR] Drop de rede detectado (janela atual: {count} drops)")

    def report_frame_ok(self):
        """Chamado a cada frame exibido com sucesso. Usado para calculo de FPS."""
        now = time.time()
        with self._lock:
            self._frame_times.append(now)
            # Mante apenas o ultimo segundo
            cutoff = now - 1.0
            while self._frame_times and self._frame_times[0] < cutoff:
                self._frame_times.popleft()

    def _monitor_loop(self):
        """Thread de monitoramento passivo (apenas logs)."""
        while self._running:
            time.sleep(1.0)
            if not self.enabled:
                continue

            # Limpa drops antigos da janela de 5s para o log ser preciso
            now = time.time()
            with self._lock:
                cutoff = now - self.DROP_WINDOW_SEC
                while self._drop_times and self._drop_times[0] < cutoff:
                    self._drop_times.popleft()

            self._log_status()

    def _log_status(self):
        """Log de status a cada 10 segundos."""
        now = time.time()
        if (now - self._last_status_log) < 10.0:
            return
        self._last_status_log = now

        with self._lock:
            recent_drops = len(self._drop_times)
            fps = len(self._frame_times)
        
        mbps = self.current_bitrate // 1_000_000
        since_drop = now - self._last_drop if self._last_drop > 0 else 0

        logger.info(
            f"[MONITOR] {mbps} Mbps | "
            f"FPS: {fps} | "
            f"Drops/5s: {recent_drops}/{self.DROP_THRESHOLD} | "
            f"Sem drops há: {since_drop:.0f}s"
        )

