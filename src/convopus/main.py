'''Initialize program and parse arguments'''
import argparse
import os

from convopus.app import convert_file, convert_folder
from convopus.genconf import read_config, print_config

config = read_config()


def main():
    '''Parse arguments from command line'''
    init_parser = argparse.ArgumentParser(add_help=False)
    init_parser.add_argument(
        '--config', help='Prints config location and it\'s content', action="store_true")
    init_parser.add_argument(
        '-v', '--version', action='version', version='%(prog)s 1.3.2')
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
        parser.add_argument(
            '-k', '--keep', help='Keep original files', action="store_true")
        args = parser.parse_args(remainder)

    config_common_types = config['COMMONTYPES']

    if (config['KEEP'] and not args.dont_keep) or (not config['KEEP'] and args.keep):
        keep_files = True
    elif (not config['KEEP'] and not args.keep ) or ( config['KEEP'] and args.dont_keep):
        keep_files = False
    else:
        print("Conflicting paramenters!")
    if os.path.isdir(args.input):
        convert_folder(args.input, args.bitrate, args.container,
                       keep_files, args.vbr, config_common_types)
    elif os.path.isfile(args.input):
        convert_file(args.input, args.bitrate,
                     args.container, keep_files, args.vbr)
    else:
        print("The path/file " + args.input + " is invalid!")


if __name__ == '__main__':
    main()
