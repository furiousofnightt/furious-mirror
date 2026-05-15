class Binary:
    @staticmethod
    def to_unsigned_short(value: int) -> int:
        return value & 0xFFFF

    @staticmethod
    def to_unsigned_byte(value: int) -> int:
        return value & 0xFF

    @staticmethod
    def u16_fixed_point_to_float(value: int) -> float:
        unsigned_short = Binary.to_unsigned_short(value)
        return 1.0 if unsigned_short == 0xFFFF else (unsigned_short / 65536.0)

    @staticmethod
    def i16_fixed_point_to_float(value: int) -> float:
        # value is a signed 16-bit integer
        return 1.0 if value == 0x7FFF else (value / 32768.0)
