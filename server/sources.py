from enum import Enum

class VideoSource(Enum):
    DISPLAY = "display"
    CAMERA = "camera"

    @classmethod
    def find_by_name(cls, name):
        for item in cls:
            if item.value == name.lower():
                return item
        return None

class AudioSource(Enum):
    OUTPUT = "output"
    MIC = "mic"
    VOICE_CALL = "voice_call"
    SYSTEM = "system"

    @classmethod
    def find_by_name(cls, name):
        for item in cls:
            if item.value == name.lower():
                return item
        return None
