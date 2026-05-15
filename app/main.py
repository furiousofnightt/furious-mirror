import argparse
from .options import Options
from .furious import FuriousMirror
from .util.log import logger

def main():
    parser = argparse.ArgumentParser(description="Furious Mirror Engine")
    parser.add_argument("-s", "--serial", help="Device serial number")
    parser.add_argument("--no-video", action="store_false", dest="video", help="Disable video")
    parser.add_argument("--no-audio", action="store_false", dest="audio", help="Disable audio")
    parser.add_argument("--no-control", action="store_false", dest="control", help="Disable control")
    
    args = parser.parse_args()
    
    options = Options()
    options.serial = args.serial
    options.video = args.video
    options.audio = args.audio
    options.control = args.control
    
    logger.info("Furious Mirror Engine Initializing...")
    while True:
        app = FuriousMirror(options)
        try:
            app.start()
        except KeyboardInterrupt:
            app.stop()
            break
            
        if getattr(app, 'reconnect_requested', False):
            import time
            logger.info("Reconnecting in 1 second...")
            time.sleep(1)
            continue
        break
