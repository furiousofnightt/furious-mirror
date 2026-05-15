import socket
import os
from typing import Optional
from ..control.channel import ControlChannel

class DesktopConnection:
    DEVICE_NAME_FIELD_LENGTH = 64
    SOCKET_NAME_PREFIX = "scrcpy"

    def __init__(self, video_socket=None, audio_socket=None, control_socket=None):
        self.video_socket = video_socket
        self.audio_socket = audio_socket
        self.control_socket = control_socket
        
        self.control_channel = ControlChannel(control_socket) if control_socket else None

    @staticmethod
    def get_socket_name(scid: int) -> str:
        if scid == -1:
            return DesktopConnection.SOCKET_NAME_PREFIX
        return f"{DesktopConnection.SOCKET_NAME_PREFIX}_{scid:08x}"

    @staticmethod
    def connect(socket_name: str):
        # On Android, this is a LocalSocket (Unix Domain Socket)
        # In Python, we can use socket.AF_UNIX if on Linux/Android
        # For a general replication, we'll assume it's available or mock it.
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # Abstract namespace is indicated by leading \0 in Python
        sock.connect(f"\0{socket_name}")
        return sock

    @classmethod
    def open(cls, scid: int, tunnel_forward: bool, video: bool, audio: bool, control: bool, send_dummy_byte: bool):
        socket_name = cls.get_socket_name(scid)
        
        video_sock = None
        audio_sock = None
        control_sock = None
        
        # This implementation assumes we are running on the Android device (the server)
        # or that we can access the unix sockets.
        
        if tunnel_forward:
            # Server creates the socket and waits for connections
            # This is complex in Python on Windows, but on Linux/Android:
            server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_sock.bind(f"\0{socket_name}")
            server_sock.listen(5)
            
            if video:
                video_sock, _ = server_sock.accept()
                if send_dummy_byte:
                    video_sock.send(b"\x00")
                    send_dummy_byte = False
            
            if audio:
                audio_sock, _ = server_sock.accept()
                if send_dummy_byte:
                    audio_sock.send(b"\x00")
                    send_dummy_byte = False
                    
            if control:
                control_sock, _ = server_sock.accept()
                if send_dummy_byte:
                    control_sock.send(b"\x00")
                    send_dummy_byte = False
            
            server_sock.close()
        else:
            # Server connects to the client (which is already listening)
            if video:
                video_sock = cls.connect(socket_name)
            if audio:
                audio_sock = cls.connect(socket_name)
            if control:
                control_sock = cls.connect(socket_name)
                
        return cls(video_sock, audio_sock, control_sock)

    def send_device_meta(self, device_name: str):
        buffer = bytearray(self.DEVICE_NAME_FIELD_LENGTH)
        name_bytes = device_name.encode("utf-8")[:self.DEVICE_NAME_FIELD_LENGTH-1]
        buffer[:len(name_bytes)] = name_bytes
        
        sock = self.video_socket or self.audio_socket or self.control_socket
        if sock:
            sock.sendall(buffer)

    def close(self):
        if self.video_socket:
            self.video_socket.close()
        if self.audio_socket:
            self.audio_socket.close()
        if self.control_socket:
            self.control_socket.close()
