import json
import os
import shutil

import ffpb

with open('config.json', 'r') as f:
    config = json.load(f)

def convertFolder(PATH):
    os.chdir(PATH)
    if config['KEEP']:
        KEEPLOCATION = os.path.join(PATH, 'original')
        if not os.path.exists('original'):
            os.makedirs('original')
    for FILENAME in os.listdir(PATH):
        if (FILENAME.endswith(tuple(config['COMMONTYPES']))):
            WITHOUTEXT = os.path.splitext(FILENAME)[0]
            OUTPUT = "".join([WITHOUTEXT, config['CONTAINER']])
            ffpb.main(argv=['-i', FILENAME, '-vn', '-c:a',
                            'libopus', '-b:a', config['BITRATE'], '-vbr', 'on', OUTPUT])
            if config['KEEP']:
                shutil.move('{0}/{1}'.format(PATH, FILENAME), KEEPLOCATION)
            else:
                os.remove(FILENAME)
        else:
            continue


def convertFile(FILENAME):
    WITHOUTEXT = os.path.splitext(FILENAME)[0]
    FILEPATH = os.path.dirname(FILENAME)
    os.chdir(FILEPATH)
    OUTPUT = "".join([WITHOUTEXT, config['CONTAINER']])
    ffpb.main(argv=['-i', FILENAME, '-vn', '-c:a', 'libopus',
                    '-b:a', config['BITRATE'], '-vbr', 'on', OUTPUT])
    if not config['KEEP']:
        os.remove(FILENAME)
