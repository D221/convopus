import argparse

from app import convertFile, convertFolder

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Python CLI program for converting audio files to opus')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--directory', help='Converts whole directory of files')
    group.add_argument('-s', '--single', help='Converts single file')
    args = parser.parse_args()
    if args.directory:
        convertFolder(args.directory)
    elif args.single:
        convertFile(args.single)
