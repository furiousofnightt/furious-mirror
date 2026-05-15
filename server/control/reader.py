import struct
from typing import Optional
from .message import ControlMessage
from ..device.position import Position, Point, Size
from ..util.binary import Binary

class ControlMessageReader:
    def __init__(self, stream):
        self.stream = stream

    def read_unsigned_byte(self) -> int:
        data = self.stream.read(1)
        if not data:
            raise EOFError()
        return data[0]

    def read_int(self) -> int:
        data = self.stream.read(4)
        return struct.unpack(">i", data)[0]

    def read_long(self) -> int:
        data = self.stream.read(8)
        return struct.unpack(">q", data)[0]

    def read_short(self) -> int:
        data = self.stream.read(2)
        return struct.unpack(">h", data)[0]

    def read_unsigned_short(self) -> int:
        data = self.stream.read(2)
        return struct.unpack(">H", data)[0]

    def read_bool(self) -> bool:
        return self.read_unsigned_byte() != 0

    def parse_buffer_length(self, size_bytes: int) -> int:
        value = 0
        for _ in range(size_bytes):
            value = (value << 8) | self.read_unsigned_byte()
        return value

    def parse_byte_array(self, size_bytes: int) -> bytes:
        length = self.parse_buffer_length(size_bytes)
        return self.stream.read(length)

    def parse_string(self, size_bytes: int = 4) -> str:
        data = self.parse_byte_array(size_bytes)
        return data.decode("utf-8")

    def parse_position(self) -> Position:
        x = self.read_int()
        y = self.read_int()
        w = self.read_unsigned_short()
        h = self.read_unsigned_short()
        return Position(Point(x, y), Size(w, h))

    def read(self) -> Optional[ControlMessage]:
        try:
            msg_type = self.read_unsigned_byte()
        except EOFError:
            return None

        if msg_type == ControlMessage.TYPE_INJECT_KEYCODE:
            action = self.read_unsigned_byte()
            keycode = self.read_int()
            repeat = self.read_int()
            meta_state = self.read_int()
            return ControlMessage.create_inject_keycode(action, keycode, repeat, meta_state)

        elif msg_type == ControlMessage.TYPE_INJECT_TEXT:
            text = self.parse_string()
            return ControlMessage.create_inject_text(text)

        elif msg_type == ControlMessage.TYPE_INJECT_TOUCH_EVENT:
            action = self.read_unsigned_byte()
            pointer_id = self.read_long()
            pos = self.parse_position()
            pressure = Binary.u16_fixed_point_to_float(self.read_short())
            action_button = self.read_int()
            buttons = self.read_int()
            return ControlMessage.create_inject_touch_event(action, pointer_id, pos, pressure, action_button, buttons)

        elif msg_type == ControlMessage.TYPE_INJECT_SCROLL_EVENT:
            pos = self.parse_position()
            h_scroll = Binary.i16_fixed_point_to_float(self.read_short()) * 16
            v_scroll = Binary.i16_fixed_point_to_float(self.read_short()) * 16
            buttons = self.read_int()
            return ControlMessage.create_inject_scroll_event(pos, h_scroll, v_scroll, buttons)

        elif msg_type == ControlMessage.TYPE_BACK_OR_SCREEN_ON:
            action = self.read_unsigned_byte()
            return ControlMessage.create_back_or_screen_on(action)

        elif msg_type == ControlMessage.TYPE_GET_CLIPBOARD:
            copy_key = self.read_unsigned_byte()
            return ControlMessage.create_get_clipboard(copy_key)

        elif msg_type == ControlMessage.TYPE_SET_CLIPBOARD:
            seq = self.read_long()
            paste = self.read_bool()
            text = self.parse_string()
            return ControlMessage.create_set_clipboard(seq, text, paste)

        elif msg_type == ControlMessage.TYPE_SET_DISPLAY_POWER:
            on = self.read_bool()
            return ControlMessage.create_set_display_power(on)

        elif msg_type in [
            ControlMessage.TYPE_EXPAND_NOTIFICATION_PANEL,
            ControlMessage.TYPE_EXPAND_SETTINGS_PANEL,
            ControlMessage.TYPE_COLLAPSE_PANELS,
            ControlMessage.TYPE_ROTATE_DEVICE,
            ControlMessage.TYPE_OPEN_HARD_KEYBOARD_SETTINGS,
            ControlMessage.TYPE_RESET_VIDEO
        ]:
            return ControlMessage.create_empty(msg_type)

        elif msg_type == ControlMessage.TYPE_UHID_CREATE:
            id = self.read_unsigned_short()
            vid = self.read_unsigned_short()
            pid = self.read_unsigned_short()
            name = self.parse_string(1)
            data = self.parse_byte_array(2)
            return ControlMessage.create_uhid_create(id, vid, pid, name, data)

        elif msg_type == ControlMessage.TYPE_UHID_INPUT:
            id = self.read_unsigned_short()
            data = self.parse_byte_array(2)
            return ControlMessage.create_uhid_input(id, data)

        elif msg_type == ControlMessage.TYPE_UHID_DESTROY:
            id = self.read_unsigned_short()
            return ControlMessage.create_uhid_destroy(id)

        elif msg_type == ControlMessage.TYPE_START_APP:
            name = self.parse_string(1)
            return ControlMessage.create_start_app(name)

        else:
            raise ValueError(f"Unknown control message type: {msg_type}")
