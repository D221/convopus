import argparse
import os
import subprocess
import sys

from convopus.app import convert_file, convert_folder
from convopus.genconf import read_config, print_config

# BETA multithreading / progress bar broken, saving original not ideal
# from convopus.app_mt import convert_file, convert_folder

# Read config data once
CONFIG_DATA = read_config()
COMMON_TYPES = CONFIG_DATA["COMMONTYPES"]
PREFERRED_BITRATE = CONFIG_DATA["BITRATE"]
CONTAINER = CONFIG_DATA["CONTAINER"]
VARIABLY_BIT_RATE = CONFIG_DATA["VBR"]
RECURSIVE = CONFIG_DATA["RECURSIVE"]
KEEP_FILES = CONFIG_DATA.get("KEEP", True)


# check if ffmpeg is installed
def check_ffmpeg():
    '''Function to check ffmpeg installation'''
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except OSError:
        print("Error: ffmpeg is not installed or not in the system path.")
        sys.exit()

def parse_arguments(argv):
    '''Function to parse command-line arguments'''
    # If user needs to view config file, just print and exit gracefully
    parser = argparse.ArgumentParser(description='A Python CLI program for converting audio files to opus', 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
   
    parser.add_argument('input',nargs='?',default=None,help='Input file or directory (optional)')

    group = parser.add_argument_group(title="Conversion Options")
    group.add_argument('-r','--recursive', help='Also convert files in subdirectories', action='store_true', default=RECURSIVE)
    group.add_argument('-c','--container', help='Container for audio files (.ogg, .opus, .oga, .mkv, .webm)',
                        default=CONTAINER)
    group.add_argument('--vbr', help='Variable Bitrate option', choices=['on', 'off'], default=VARIABLY_BIT_RATE)
    group.add_argument('-b', '--bitrate', help=f'Preferred bitrate for audio files', default=PREFERRED_BITRATE)

    action_group = parser.add_mutually_exclusive_group(required=False)
    action_group.add_argument('-k','--keep-original-files',action='store_true',help='Keeps original files after conversion')
    action_group.add_argument('-dk','--delete-original-files',action='store_true',help='Delete original files after conversion')

    parser.add_argument('--config',help="Prints config location and it\'s content", action='store_true', dest='print_config')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.3.3')

    args = parser.parse_args(args=argv)
    #if user wants to see the config, retrieve and display it
    if args.print_config:
        print_config() 
        sys.exit(0) 
    return args

def convert(input_path, bitrate, container, keep_files, vbr, common_types, recursive):
    '''Function that converts audio files into opus format'''
    if os.path.isdir(input_path):
        convert_folder(input_path, bitrate, container,keep_files,vbr,common_types, recursive)
    elif os.path.isfile(input_path):
        convert_file(input_path, bitrate, container,keep_files, vbr)
    else:
        print(f"The path/file {input_path} is invalid!")
        sys.exit(1)

def main():
    '''Main function to run the program'''

    argv = sys.argv[1:]
    args = parse_arguments(argv)
    check_ffmpeg()

    # Set value of keep_files variable based on command-line arguments
    keep_files = None
    if args.keep_original_files:
        keep_files = True
    elif args.delete_original_files:
        keep_files = False
    # If no flag is specified for keep_files, use default value from config file
    if keep_files is None:
        keep_files = KEEP_FILES

    convert(args.input,args.bitrate,args.container,keep_files, args.vbr,COMMON_TYPES, args.recursive)


if __name__ == '__main__':
    main()