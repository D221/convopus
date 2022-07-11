'''Initialize program and parse arguments'''
import argparse
import os

from convopus.app import convert_file, convert_folder
from convopus.genconf import read_config

config = read_config()


def main():
    '''Parse arguments from command line'''
    parser = argparse.ArgumentParser(
        prog="convopus",
        description='A Python CLI program for converting audio files to opus')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument(
        '-b', '--bitrate', help='Prefered bitrate for audio files (default: 128k)')
    parser.add_argument(
        '-c', '--container', help='Container for audio files (.ogg, .opus, .oga, .mkv, .webm) (default: .ogg)')
    parser.add_argument(
        '-dk', '--dont-keep', help='Don\'t Keep original files (default: False)', action="store_true")
    parser.add_argument('-v', '--vbr', help='Variable Bitrate (on/off) (default: on)',
                        choices=["on", "off"], metavar="on/off")
    args = parser.parse_args()
    if args.bitrate:
        config_bitrate = args.bitrate
    else:
        config_bitrate = config['BITRATE']

    if args.container:
        config_container = args.container
    else:
        config_container = config['CONTAINER']

    if args.dont_keep:
        config_keep = False
    else:
        config_keep = config['KEEP']

    if args.vbr:
        config_vbr = args.vbr
    else:
        config_vbr = config['VBR']

    config_common_types = config['COMMONTYPES']

    if os.path.isdir(args.input):
        convert_folder(args.input, config_bitrate, config_container,
                       config_keep, config_vbr, config_common_types)
    elif os.path.isfile(args.input):
        convert_file(args.input, config_bitrate,
                     config_container, config_keep, config_vbr)
    else:
        print("The path/file is invalid!")


if __name__ == '__main__':
    main()
