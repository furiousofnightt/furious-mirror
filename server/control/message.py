from dataclasses import dataclass, field
from typing import Optional
from ..device.position import Position

@dataclass
class ControlMessage:
    TYPE_INJECT_KEYCODE = 0
    TYPE_INJECT_TEXT = 1
    TYPE_INJECT_TOUCH_EVENT = 2
    TYPE_INJECT_SCROLL_EVENT = 3
    TYPE_BACK_OR_SCREEN_ON = 4
    TYPE_EXPAND_NOTIFICATION_PANEL = 5
    TYPE_EXPAND_SETTINGS_PANEL = 6
    TYPE_COLLAPSE_PANELS = 7
    TYPE_GET_CLIPBOARD = 8
    TYPE_SET_CLIPBOARD = 9
    TYPE_SET_DISPLAY_POWER = 10
    TYPE_ROTATE_DEVICE = 11
    TYPE_UHID_CREATE = 12
    TYPE_UHID_INPUT = 13
    TYPE_UHID_DESTROY = 14
    TYPE_OPEN_HARD_KEYBOARD_SETTINGS = 15
    TYPE_START_APP = 16
    TYPE_RESET_VIDEO = 17

    COPY_KEY_NONE = 0
    COPY_KEY_COPY = 1
    COPY_KEY_CUT = 2

    type: int
    text: Optional[str] = None
    meta_state: int = 0
    action: int = 0
    keycode: int = 0
    repeat: int = 0
    action_button: int = 0
    buttons: int = 0
    pointer_id: int = 0
    pressure: float = 0.0
    position: Optional[Position] = None
    h_scroll: float = 0.0
    v_scroll: float = 0.0
    copy_key: int = 0
    paste: bool = False
    sequence: int = 0
    id: int = 0
    data: Optional[bytes] = None
    on: bool = False
    vendor_id: int = 0
    product_id: int = 0

    @classmethod
    def create_inject_keycode(cls, action, keycode, repeat, meta_state):
        return cls(type=cls.TYPE_INJECT_KEYCODE, action=action, keycode=keycode, repeat=repeat, meta_state=meta_state)

    @classmethod
    def create_inject_text(cls, text):
        return cls(type=cls.TYPE_INJECT_TEXT, text=text)

    @classmethod
    def create_inject_touch_event(cls, action, pointer_id, position, pressure, action_button, buttons):
        return cls(type=cls.TYPE_INJECT_TOUCH_EVENT, action=action, pointer_id=pointer_id, position=position, 
                   pressure=pressure, action_button=action_button, buttons=buttons)

    @classmethod
    def create_inject_scroll_event(cls, position, h_scroll, v_scroll, buttons):
        return cls(type=cls.TYPE_INJECT_SCROLL_EVENT, position=position, h_scroll=h_scroll, v_scroll=v_scroll, buttons=buttons)

    @classmethod
    def create_back_or_screen_on(cls, action):
        return cls(type=cls.TYPE_BACK_OR_SCREEN_ON, action=action)

    @classmethod
    def create_get_clipboard(cls, copy_key):
        return cls(type=cls.TYPE_GET_CLIPBOARD, copy_key=copy_key)

    @classmethod
    def create_set_clipboard(cls, sequence, text, paste):
        return cls(type=cls.TYPE_SET_CLIPBOARD, sequence=sequence, text=text, paste=paste)

    @classmethod
    def create_set_display_power(cls, on):
        return cls(type=cls.TYPE_SET_DISPLAY_POWER, on=on)

    @classmethod
    def create_empty(cls, type):
        return cls(type=type)

    @classmethod
    def create_uhid_create(cls, id, vendor_id, product_id, name, report_desc):
        return cls(type=cls.TYPE_UHID_CREATE, id=id, vendor_id=vendor_id, product_id=product_id, text=name, data=report_desc)

    @classmethod
    def create_uhid_input(cls, id, data):
        return cls(type=cls.TYPE_UHID_INPUT, id=id, data=data)

    @classmethod
    def create_uhid_destroy(cls, id):
        return cls(type=cls.TYPE_UHID_DESTROY, id=id)

    @classmethod
    def create_start_app(cls, name):
        return cls(type=cls.TYPE_START_APP, text=name)
