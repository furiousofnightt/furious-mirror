class Ln:
    _level = "info"

    @classmethod
    def init_log_level(cls, level):
        cls._level = level.value if hasattr(level, 'value') else level

    @classmethod
    def i(cls, message):
        print(f"[INFO] {message}")

    @classmethod
    def d(cls, message):
        if cls._level in ["debug", "verbose"]:
            print(f"[DEBUG] {message}")

    @classmethod
    def w(cls, message):
        print(f"[WARN] {message}")

    @classmethod
    def e(cls, message, exception=None):
        print(f"[ERROR] {message}")
        if exception:
            print(exception)
