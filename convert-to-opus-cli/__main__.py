import argparse

from app import convertFile, convertFolder

def main():
    parser = argparse.ArgumentParser(
    description='A Python CLI program for converting audio files to opus')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-D', '--directory',
                       help='Converts whole directory of files')
    group.add_argument('-F', '--file', help='Converts a single file')
    args = parser.parse_args()
    if args.directory:
        convertFolder(args.directory)
    elif args.file:
        convertFile(args.file)


if __name__ == '__main__':
    main()