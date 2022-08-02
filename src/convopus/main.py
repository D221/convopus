'''Initialize program and parse arguments'''
import argparse
import os

from convopus.app import convert_file, convert_folder
from convopus.genconf import read_config, print_config

config = read_config()


def main():
    '''Parse arguments from command line'''
    init_parser = argparse.ArgumentParser(
        prog="convopus",
        description='A Python CLI program for converting audio files to opus',
        add_help=False)
    init_parser.add_argument(
        '--config', help='Prints config location and it\'s content', action="store_true")
    init_parser.add_argument(
        '-v', '--version', action='version', version='%(prog)s 1.3.1')
    options, remainder = init_parser.parse_known_args()

    if options.config:
        print_config()
    else:
        parser = argparse.ArgumentParser(
            prog="convopus",
            description='A Python CLI program for converting audio files to opus',
            parents=[init_parser],
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('input', help='Input file or directory')
        parser.add_argument(
            '-b', '--bitrate', help='Prefered bitrate for audio files', default=config['BITRATE'])
        parser.add_argument(
            '-c', '--container', help='Container for audio files (.ogg, .opus, .oga, .mkv, .webm)', default=config['CONTAINER'])
        parser.add_argument('-vbr', help='Variable Bitrate (on/off)',
                            default=config['VBR'], choices=["on", "off"], metavar="on/off")
        parser.add_argument(
            '-dk', '--dont-keep', help='Don\'t Keep original files', action="store_true")
        args = parser.parse_args(remainder)

    # Don't like this logic
    if args.dont_keep:
        config_keep = False
    else:
        config_keep = config['KEEP']

    config_common_types = config['COMMONTYPES']

    if os.path.isdir(args.input):
        convert_folder(args.input, args.bitrate, args.container,
                       config_keep, args.vbr, config_common_types)
    elif os.path.isfile(args.input):
        convert_file(args.input, args.bitrate,
                     args.container, config_keep, args.vbr)
    else:
        print("The path/file is invalid!")


if __name__ == '__main__':
    main()
