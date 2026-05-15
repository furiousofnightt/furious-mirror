from ..util.ln import Ln

class Device:
    DISPLAY_ID_NONE = -1

    @staticmethod
    def get_device_name():
        # In a real replication on Android, we'd read /system/build.prop or use 'getprop'
        return "Android Device"

    @staticmethod
    def supports_input_events(display_id: int):
        return display_id == 0 # Simplified

    @staticmethod
    def inject_event(input_event, display_id: int, inject_mode: int):
        # This would call the Android input manager
        Ln.d(f"Injecting event {input_event} to display {display_id}")
        return True

    @staticmethod
    def inject_key_event(action: int, key_code: int, repeat: int, meta_state: int, display_id: int, inject_mode: int):
        Ln.d(f"Injecting key event: code={key_code}, action={action}")
        return True

    @staticmethod
    def press_release_keycode(key_code: int, display_id: int, inject_mode: int):
        return (Device.inject_key_event(0, key_code, 0, 0, display_id, inject_mode) and
                Device.inject_key_event(1, key_code, 0, 0, display_id, inject_mode))

    @staticmethod
    def is_screen_on(display_id: int):
        return True

    @staticmethod
    def expand_notification_panel():
        Ln.d("Expanding notification panel")

    @staticmethod
    def expand_settings_panel():
        Ln.d("Expanding settings panel")

    @staticmethod
    def collapse_panels():
        Ln.d("Collapsing panels")

    @staticmethod
    def get_clipboard_text():
        return None

    @staticmethod
    def set_clipboard_text(text: str):
        Ln.d(f"Setting clipboard text: {text}")
        return True

    @staticmethod
    def set_display_power(display_id: int, on: bool):
        Ln.d(f"Setting display power: {on} for display {display_id}")
        return True

    @staticmethod
    def rotate_device(display_id: int):
        Ln.d(f"Rotating device display {display_id}")

    @staticmethod
    def start_app(package_name: str, display_id: int, force_stop: bool):
        Ln.d(f"Starting app {package_name} on display {display_id} (force_stop={force_stop})")
