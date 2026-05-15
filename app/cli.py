import argparse
from dataclasses import dataclass
from .options import Options

@dataclass
class CLIArgs:
    opts: Options
    help: bool = False
    version: bool = False

def parse_args(argv):
    parser = argparse.ArgumentParser(description="scrcpy-python")
    parser.add_argument("--max-size", type=int, help="Limit video size")
    parser.add_argument("--bit-rate", type=int, help="Video bit rate")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio")
    parser.add_argument("--no-video", action="store_true", help="Disable video")
    parser.add_argument("-s", "--serial", help="Device serial number")
    parser.add_argument("serial_pos", nargs="?", help="Device serial number (positional)")
    
    # This is a simplified version of scrcpy's complex CLI
    args, unknown = parser.parse_known_args(argv[1:])
    
    opts = Options()
    opts.serial = args.serial or args.serial_pos or ""
    if args.max_size:
        opts.max_size = args.max_size
    if args.bit_rate:
        opts.video_bit_rate = args.bit_rate
    if args.no_audio:
        opts.audio = False
    if args.no_video:
        opts.video = False
        
    return CLIArgs(opts=opts)
