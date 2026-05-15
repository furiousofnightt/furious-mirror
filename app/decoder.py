import av
from .util.log import logger

class Decoder:
    def __init__(self, name: str):
        self.name = name
        self.codec_context = None
        self.on_frame_callbacks = []
        self.resampler = None

    def add_on_frame_callback(self, callback):
        self.on_frame_callbacks.append(callback)

    def open(self, codec_name: str):
        logger.info(f"Decoder '{self.name}': opening {codec_name}...")
        codec = av.CodecContext.create(codec_name, "r")
        self.codec_context = codec
        
        if self.name == "audio":
            self.resampler = av.AudioResampler(
                format='flt',
                layout='stereo',
                rate=48000
            )

    def push(self, data: bytes, pts: int, is_config: bool, is_key_frame: bool):
        if not self.codec_context:
            return

        try:
            packet = av.Packet(data)
            packet.pts = pts
            
            frames = self.codec_context.decode(packet)
            for frame in frames:
                if self.resampler:
                    # Resample audio to standard format for SDL
                    # Resampler returns a list of frames
                    resampled_frames = self.resampler.resample(frame)
                    for f in resampled_frames:
                        for cb in self.on_frame_callbacks:
                            cb(f)
                else:
                    for cb in self.on_frame_callbacks:
                        cb(frame)
        except Exception as e:
            if is_config:
                logger.warning(f"Decoder '{self.name}': failed to decode config packet, but it might be normal.")
            else:
                logger.error(f"Decoder '{self.name}': decode error: {e}")
