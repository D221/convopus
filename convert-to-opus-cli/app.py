import json
import os
import shutil

import ffpb

with open('config.json', 'r') as f:
    config = json.load(f)


def convertFolder(PATH):
    if config['KEEP']:
        KEEPLOCATION = os.path.join(PATH, 'original')
        os.makedirs(KEEPLOCATION, exist_ok=True)
    for FILENAME in os.listdir(PATH):
        if (FILENAME.endswith(tuple(config['COMMONTYPES']))):
            WITHOUT_EXT = os.path.splitext(FILENAME)[0]
            INPUT = "".join([PATH, FILENAME])
            OUTPUT = "".join([PATH, WITHOUT_EXT, config['CONTAINER']])
            ffpb.main(argv=['-i', INPUT, '-vn', '-c:a', 'libopus',
                      '-b:a', config['BITRATE'], '-vbr', 'on', OUTPUT])
            if config['KEEP']:
                shutil.move(INPUT, KEEPLOCATION)
            else:
                os.remove(INPUT)
        else:
            continue


def convertFile(FILENAME):
    WITHOUT_EXT = os.path.splitext(FILENAME)[0]
    OUTPUT = "".join([WITHOUT_EXT, config['CONTAINER']])
    ffpb.main(argv=['-i', FILENAME, '-vn', '-c:a', 'libopus',
              '-b:a', config['BITRATE'], '-vbr', 'on', OUTPUT])
    if not config['KEEP']:
        os.remove(FILENAME)
