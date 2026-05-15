import sdl2
import ctypes
from .util.log import logger

class AudioPlayer:
    def __init__(self):
        self.device = None
        self.opened = False
        self.sample_rate = 48000
        self.channels = 2

    def open(self, sample_rate=48000, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Use positional arguments and correct names as requested by the error message
        # aformat instead of format
        spec = sdl2.SDL_AudioSpec(
            self.sample_rate,
            sdl2.AUDIO_F32SYS,
            self.channels,
            1024
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
            
        # Push decoded samples to SDL audio queue
        data = frame.to_ndarray().tobytes()
        sdl2.SDL_QueueAudio(self.device, data, len(data))

    def close(self):
        if self.device:
            sdl2.SDL_CloseAudioDevice(self.device)
            self.device = None
        self.opened = False
