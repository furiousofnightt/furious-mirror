import threading
import time
from .message import ControlMessage
from ..util.ln import Ln
from ..device.device import Device

class Controller:
    def __init__(self, control_channel, cleanup, options):
        self.control_channel = control_channel
        self.cleanup = cleanup
        self.options = options
        self.display_id = options.display_id
        self.thread = None
        self.sender = None # Hypothetical DeviceMessageSender

    def control_loop(self):
        Ln.i("Starting controller loop...")
        
        # On start, power on the device (if needed)
        # Device.press_release_keycode(KeyEvent.KEYCODE_POWER, self.display_id)
        
        try:
            while True:
                msg = self.control_channel.recv()
                if not msg:
                    break
                self.handle_event(msg)
        except Exception as e:
            Ln.e("Controller error", e)
        finally:
            Ln.d("Controller stopped")

    def handle_event(self, msg: ControlMessage):
        t = msg.type
        if t == ControlMessage.TYPE_INJECT_KEYCODE:
            self.inject_keycode(msg.action, msg.keycode, msg.repeat, msg.meta_state)
        elif t == ControlMessage.TYPE_INJECT_TEXT:
            self.inject_text(msg.text)
        elif t == ControlMessage.TYPE_INJECT_TOUCH_EVENT:
            self.inject_touch(msg.action, msg.pointer_id, msg.position, msg.pressure, msg.action_button, msg.buttons)
        elif t == ControlMessage.TYPE_INJECT_SCROLL_EVENT:
            self.inject_scroll(msg.position, msg.h_scroll, msg.v_scroll, msg.buttons)
        elif t == ControlMessage.TYPE_BACK_OR_SCREEN_ON:
            self.press_back_or_turn_screen_on(msg.action)
        elif t == ControlMessage.TYPE_EXPAND_NOTIFICATION_PANEL:
            Device.expand_notification_panel()
        elif t == ControlMessage.TYPE_EXPAND_SETTINGS_PANEL:
            Device.expand_settings_panel()
        elif t == ControlMessage.TYPE_COLLAPSE_PANELS:
            Device.collapse_panels()
        elif t == ControlMessage.TYPE_GET_CLIPBOARD:
            self.get_clipboard(msg.copy_key)
        elif t == ControlMessage.TYPE_SET_CLIPBOARD:
            self.set_clipboard(msg.text, msg.paste, msg.sequence)
        elif t == ControlMessage.TYPE_SET_DISPLAY_POWER:
            self.set_display_power(msg.on)
        elif t == ControlMessage.TYPE_ROTATE_DEVICE:
            Device.rotate_device(self.display_id)
        # Add more cases as needed...

    def inject_keycode(self, action, keycode, repeat, meta_state):
        Ln.d(f"Injecting keycode: {keycode}, action: {action}")
        return Device.inject_key_event(action, keycode, repeat, meta_state, self.display_id)

    def inject_text(self, text):
        Ln.d(f"Injecting text: {text}")
        return Device.inject_text(text, self.display_id)

    def inject_touch(self, action, pointer_id, position, pressure, action_button, buttons):
        Ln.d(f"Injecting touch: {action} at {position}")
        return Device.inject_touch_event(action, pointer_id, position, pressure, action_button, buttons, self.display_id)

    def inject_scroll(self, position, h_scroll, v_scroll, buttons):
        Ln.d(f"Injecting scroll: {h_scroll}, {v_scroll} at {position}")
        return Device.inject_scroll_event(position, h_scroll, v_scroll, buttons, self.display_id)

    def press_back_or_turn_screen_on(self, action):
        return Device.press_back_or_turn_screen_on(action, self.display_id)

    def get_clipboard(self, copy_key):
        text = Device.get_clipboard_text()
        # sender.send(DeviceMessage.create_clipboard(text))

    def set_clipboard(self, text, paste, sequence):
        ok = Device.set_clipboard_text(text)
        if paste:
            Device.press_release_keycode(279, self.display_id) # KEYCODE_PASTE

    def set_display_power(self, on):
        Device.set_display_power(self.display_id, on)

    def start(self):
        self.thread = threading.Thread(target=self.control_loop, name="control-recv")
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        # Logic to stop the loop
        pass
