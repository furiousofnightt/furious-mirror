from dataclasses import dataclass

@dataclass
class Options:
    max_size: int = 0
    video_bit_rate: int = 8000000
    audio_bit_rate: int = 128000
    max_fps: float = 0.0
    video: bool = True
    audio: bool = True
    control: bool = True
    tunnel_forward: bool = True
    serial: str = ""
    force_usb: bool = False
