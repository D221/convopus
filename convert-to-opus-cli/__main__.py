'''Initialize program and parse arguments'''
import argparse
import os

from app import convert_file, convert_folder


def main():
    '''Parse arguments from command line'''
    parser = argparse.ArgumentParser(
        prog="convert-to-opus-cli",
        description='A Python CLI program for converting audio files to opus')
    parser.add_argument('input', help='Input file or directory')
    args = parser.parse_args()
    if os.path.isdir(args.input):
        convert_folder(args.input)
    elif os.path.isfile(args.input):
        convert_file(args.input)


if __name__ == '__main__':
    main()
