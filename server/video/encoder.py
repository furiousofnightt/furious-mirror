import threading
from ..util.ln import Ln

class SurfaceEncoder:
    DEFAULT_I_FRAME_INTERVAL = 10
    REPEAT_FRAME_DELAY_US = 100000

    def __init__(self, capture, streamer, options):
        self.capture = capture
        self.streamer = streamer
        self.options = options
        self.stopped = False
        self.thread = None

    def stream_capture(self):
        Ln.i("Starting video stream capture...")
        # In a real replication on Android, this would use MediaCodec.
        # In Python, we would need a way to capture the screen and encode it.
        
        try:
            while not self.stopped:
                # 1. Capture a frame from SurfaceCapture
                # 2. Encode it using some encoder (e.g., FFmpeg/AV)
                # 3. Write packets to the streamer
                
                # For now, we stub this out as a loop.
                # In a real app, this would be highly optimized.
                pass
        except Exception as e:
            Ln.e("Video encoding error", e)
        finally:
            Ln.d("Screen streaming stopped")

    def start(self):
        self.thread = threading.Thread(target=self.stream_capture, name="video")
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.stopped = True

    def join(self):
        if self.thread:
            self.thread.join()
