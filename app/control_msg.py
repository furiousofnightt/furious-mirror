import struct
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Union
from .options import Options
from .util.log import logger

class ControlMsgType(IntEnum):
    INJECT_KEYCODE = 0
    INJECT_TEXT = 1
    INJECT_TOUCH_EVENT = 2
    INJECT_SCROLL_EVENT = 3
    BACK_OR_SCREEN_ON = 4
    EXPAND_NOTIFICATION_PANEL = 5
    EXPAND_SETTINGS_PANEL = 6
    COLLAPSE_PANELS = 7
    GET_CLIPBOARD = 8
    SET_CLIPBOARD = 9
    SET_DISPLAY_POWER = 10
    ROTATE_DEVICE = 11
    UHID_CREATE = 12
    UHID_INPUT = 13
    UHID_DESTROY = 14
    OPEN_HARD_KEYBOARD_SETTINGS = 15
    START_APP = 16
    RESET_VIDEO = 17

class CopyKey(IntEnum):
    NONE = 0
    COPY = 1
    CUT = 2

def float_to_u16fp(f: float) -> int:
    if f >= 1.0:
        return 0xFFFF
    if f <= 0.0:
        return 0x0000
    return int(f * 65536.0)

def float_to_i16fp(f: float) -> int:
    if f >= 1.0:
        return 0x7FFF
    if f <= -1.0:
        return -0x8000
    return int(f * 32768.0)

@dataclass
class ControlMsg:
    type: ControlMsgType
    
    # Keycode fields
    action: int = 0
    keycode: int = 0
    repeat: int = 0
    metastate: int = 0
    
    # Text fields
    text: Optional[str] = None
    
    # Touch/Scroll fields
    pointer_id: int = 0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    pressure: float = 0.0
    action_button: int = 0
    buttons: int = 0
    hscroll: float = 0.0
    vscroll: float = 0.0
    
    # Clipboard fields
    copy_key: CopyKey = CopyKey.NONE
    sequence: int = 0
    paste: bool = False
    
    # Other
    on: bool = False
    id: int = 0
    vendor_id: int = 0
    product_id: int = 0
    name: Optional[str] = None
    data: Optional[bytes] = None

    def serialize(self) -> bytes:
        buf = bytearray()
        buf.append(self.type)
        
        if self.type == ControlMsgType.INJECT_KEYCODE:
            buf.append(self.action)
            buf.extend(struct.pack(">III", self.keycode, self.repeat, self.metastate))
            
        elif self.type == ControlMsgType.INJECT_TEXT:
            text_bytes = self.text.encode("utf-8")[:300]
            buf.extend(struct.pack(">I", len(text_bytes)))
            buf.extend(text_bytes)
            
        elif self.type == ControlMsgType.INJECT_TOUCH_EVENT:
            buf.append(self.action)
            buf.extend(struct.pack(">q", self.pointer_id))
            buf.extend(struct.pack(">iiHH", self.x, self.y, self.width, self.height))
            buf.extend(struct.pack(">H", float_to_u16fp(self.pressure)))
            buf.extend(struct.pack(">II", self.action_button, self.buttons))
            
        elif self.type == ControlMsgType.INJECT_SCROLL_EVENT:
            buf.extend(struct.pack(">iiHH", self.x, self.y, self.width, self.height))
            h = float_to_i16fp(max(-1.0, min(1.0, self.hscroll / 16.0)))
            v = float_to_i16fp(max(-1.0, min(1.0, self.vscroll / 16.0)))
            buf.extend(struct.pack(">hhI", h, v, self.buttons))
            
        elif self.type == ControlMsgType.BACK_OR_SCREEN_ON:
            buf.append(self.action)
            
        elif self.type == ControlMsgType.GET_CLIPBOARD:
            buf.append(self.copy_key)
            
        elif self.type == ControlMsgType.SET_CLIPBOARD:
            buf.extend(struct.pack(">q?", self.sequence, self.paste))
            text_bytes = self.text.encode("utf-8")
            buf.extend(struct.pack(">I", len(text_bytes)))
            buf.extend(text_bytes)
            
        elif self.type == ControlMsgType.SET_DISPLAY_POWER:
            buf.append(1 if self.on else 0)
            
        elif self.type == ControlMsgType.UHID_CREATE:
            buf.extend(struct.pack(">HHH", self.id, self.vendor_id, self.product_id))
            name_bytes = self.name.encode("utf-8")[:127]
            buf.append(len(name_bytes))
            buf.extend(name_bytes)
            buf.extend(struct.pack(">H", len(self.data)))
            buf.extend(self.data)
            
        elif self.type == ControlMsgType.UHID_INPUT:
            buf.extend(struct.pack(">HH", self.id, len(self.data)))
            buf.extend(self.data)
            
        elif self.type == ControlMsgType.UHID_DESTROY:
            buf.extend(struct.pack(">H", self.id))
            
        elif self.type == ControlMsgType.START_APP:
            name_bytes = self.name.encode("utf-8")[:255]
            buf.append(len(name_bytes))
            buf.extend(name_bytes)
            
        return bytes(buf)
