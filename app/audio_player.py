import sdl2
import ctypes
from .util.log import logger

# --- Limites do buffer de áudio ---
# 48000 samples/s * 2 canais * 4 bytes (float32) = 384000 bytes/s
#
# Zona mínima (segurança anti-underrun): ~40ms = 15360 bytes
#   Nunca descarta se a fila estiver abaixo disso, garantindo continuidade.
#
# Zona máxima (anti-delay em Wi-Fi): ~250ms = 96000 bytes
#   Acima disso, frames novos são descartados até a fila normalizar.
_MIN_AUDIO_QUEUE_BYTES = 15_360   # 40ms  — zona de segurança
_MAX_AUDIO_QUEUE_BYTES = 96_000   # 250ms — limite de descarte

class AudioPlayer:
    def __init__(self):
        self.device = None
        self.opened = False
        self.sample_rate = 48000
        self.channels = 2

    def open(self, sample_rate=48000, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels

        spec = sdl2.SDL_AudioSpec(
            self.sample_rate,
            sdl2.AUDIO_F32SYS,
            self.channels,
            4096  # Buffer maior (85ms) → menos underruns e ruídos
        )

        self.device = sdl2.SDL_OpenAudioDevice(
            None, 0, spec, None, 0
        )

        if self.device == 0:
            logger.error(f"SDL_OpenAudioDevice Error: {sdl2.SDL_GetError()}")
            return False

        sdl2.SDL_PauseAudioDevice(self.device, 0)
        self.opened = True
        logger.info(f"AudioPlayer: opened {sample_rate}Hz, {channels} channels")
        return True

    def play(self, frame):
        if not self.opened:
            return

        queued = sdl2.SDL_GetQueuedAudioSize(self.device)

        # Zona de segurança: fila baixa → enfileira sempre (evita underrun/ruído)
        if queued < _MIN_AUDIO_QUEUE_BYTES:
            pass
        # Zona de descarte: fila alta → descarta o frame (evita delay em Wi-Fi)
        elif queued > _MAX_AUDIO_QUEUE_BYTES:
            return

        data = frame.to_ndarray().tobytes()
        sdl2.SDL_QueueAudio(self.device, data, len(data))

    def close(self):
        if self.device:
            sdl2.SDL_CloseAudioDevice(self.device)
            self.device = None
        self.opened = False
