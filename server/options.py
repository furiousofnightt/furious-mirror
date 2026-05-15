from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from .video.codec import VideoCodec
from .audio.codec import AudioCodec
from .sources import VideoSource, AudioSource

class LogLevel(Enum):
    VERBOSE = "verbose"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"

@dataclass
class Options:
    log_level: LogLevel = LogLevel.DEBUG
    scid: int = -1
    video: bool = True
    audio: bool = True
    max_size: int = 0
    video_codec: VideoCodec = VideoCodec.H264
    audio_codec: AudioCodec = AudioCodec.OPUS
    video_source: VideoSource = VideoSource.DISPLAY
    audio_source: AudioSource = AudioSource.OUTPUT
    audio_dup: bool = False
    video_bit_rate: int = 8000000
    audio_bit_rate: int = 128000
    max_fps: float = 0.0
    angle: float = 0.0
    tunnel_forward: bool = False
    control: bool = True
    display_id: int = 0
    show_touches: bool = False
    stay_awake: bool = False
    screen_off_timeout: int = -1
    cleanup: bool = True
    power_on: bool = True
    send_device_meta: bool = True
    send_frame_meta: bool = True
    send_dummy_byte: bool = True
    send_codec_meta: bool = True

    @classmethod
    def parse(cls, args: List[str]):
        if not args:
            raise ValueError("Missing client version")
        
        # client_version = args[0]
        # In a real replication, we'd check the version here.
        
        options = cls()
        for arg in args[1:]:
            if '=' not in arg:
                continue
            key, value = arg.split('=', 1)
            
            if key == "scid":
                options.scid = int(value, 16)
            elif key == "log_level":
                options.log_level = LogLevel(value.lower())
            elif key == "video":
                options.video = value.lower() == "true"
            elif key == "audio":
                options.audio = value.lower() == "true"
            elif key == "video_codec":
                options.video_codec = VideoCodec.find_by_name(value)
            elif key == "audio_codec":
                options.audio_codec = AudioCodec.find_by_name(value)
            elif key == "video_source":
                options.video_source = VideoSource.find_by_name(value)
            elif key == "audio_source":
                options.audio_source = AudioSource.find_by_name(value)
            elif key == "max_size":
                options.max_size = int(value) & ~7
            elif key == "video_bit_rate":
                options.video_bit_rate = int(value)
            elif key == "audio_bit_rate":
                options.audio_bit_rate = int(value)
            elif key == "max_fps":
                options.max_fps = float(value)
            elif key == "tunnel_forward":
                options.tunnel_forward = value.lower() == "true"
            elif key == "control":
                options.control = value.lower() == "true"
            elif key == "display_id":
                options.display_id = int(value)
            elif key == "show_touches":
                options.show_touches = value.lower() == "true"
            elif key == "stay_awake":
                options.stay_awake = value.lower() == "true"
            elif key == "cleanup":
                options.cleanup = value.lower() == "true"
            # Add more keys as needed...
            
        return options
