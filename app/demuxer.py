import struct
import threading
import socket
from .util.log import logger

class Demuxer(threading.Thread):
    def __init__(self, name: str, sock: socket.socket):
        super().__init__(name=f"demuxer-{name}")
        self.name = name
        self.socket = sock
        self.stopped = False
        self.on_packet_callbacks = []
        self.on_error_callbacks = []

    def add_on_packet_callback(self, callback):
        self.on_packet_callbacks.append(callback)

    def add_on_error_callback(self, callback):
        self.on_error_callbacks.append(callback)

    def _recv_exact(self, n):
        data = b""
        try:
            while len(data) < n:
                chunk = self.socket.recv(n - len(data))
                if not chunk:
                    return None
                data += chunk
        except (socket.error, OSError):
            return None
        return data

    def run(self):
        logger.info(f"Demuxer '{self.name}': starting...")
        
        # Protocol Handshake (after dummy byte which is read in scrcpy.py)
        if self.name == "video":
            # Codec ID (4 bytes) + Width (4 bytes) + Height (4 bytes)
            # Total 12 bytes
            meta = self._recv_exact(12)
            if not meta:
                return
            
            codec_id = struct.unpack(">I", meta[0:4])[0]
            w = struct.unpack(">I", meta[4:8])[0]
            h = struct.unpack(">I", meta[8:12])[0]
            
            logger.info(f"Demuxer '{self.name}': codec ID 0x{codec_id:08x}")
            logger.info(f"Demuxer '{self.name}': video size {w}x{h}")
        
        elif self.name == "audio":
            # Audio meta: Codec ID (4 bytes)
            meta = self._recv_exact(4)
            if not meta:
                return
            codec_id = struct.unpack(">I", meta)[0]
            logger.info(f"Demuxer '{self.name}': codec ID 0x{codec_id:08x}")

        while not self.stopped:
            # Packet header: 12 bytes (8 pts/flags + 4 size)
            header = self._recv_exact(12)
            if not header:
                if not self.stopped:
                    for cb in self.on_error_callbacks: cb()
                break
            
            pts_flags = struct.unpack(">Q", header[0:8])[0]
            size = struct.unpack(">I", header[8:12])[0]
            
            # Flags: bit 63 = config, bit 62 = key frame
            is_config = bool(pts_flags & (1 << 63))
            is_key_frame = bool(pts_flags & (1 << 62))
            pts = pts_flags & 0x3FFFFFFFFFFFFFFF
            
            data = self._recv_exact(size)
            if data is None:
                if not self.stopped:
                    for cb in self.on_error_callbacks: cb()
                break
                
            for cb in self.on_packet_callbacks:
                cb(data, pts, is_config, is_key_frame)

        logger.info(f"Demuxer '{self.name}': stopped.")

    def stop(self):
        self.stopped = True
