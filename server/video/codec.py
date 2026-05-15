from enum import Enum

class VideoCodec(Enum):
    H264 = "h264"
    H265 = "h265"
    AV1 = "av1"

    @classmethod
    def find_by_name(cls, name):
        for item in cls:
            if item.value == name.lower():
                return item
        return None
