from enum import Enum

class AudioCodec(Enum):
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    RAW = "raw"

    @classmethod
    def find_by_name(cls, name):
        for item in cls:
            if item.value == name.lower():
                return item
        return None
