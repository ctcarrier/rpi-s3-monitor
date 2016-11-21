#!/usr/bin/env python

import subprocess
import StringIO

#!/usr/bin/env python

from os import listdir, getcwd
import signal
import logging
from PIL import Image
import linecache
import sys
from wrappers import Convert
from os.path import join

FFMPEG_BIN = "ffmpeg"
SETTINGS_FILE = "/var/lib/s3download/settings.cfg"
OUTPUT_DIR = '/var/lib/s3download/output/timelapse.mp4'
LOG_FILENAME = '/var/log/s3download/s3download.log'
__version__ = "1.0"

def ExceptionMessage():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

class App():
    def startup(self):
        self.convert = Convert(subprocess)

        self.start()

    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    def run(self):
        self.startup()

    def start(self):
        try:
            existingFiles = listdir(getcwd())
            for file in existingFiles:
                print file
                img = Image.open(file)
                #self.resize_and_save(img, file)
        except Exception,e:
            logging.error("Error: %s at %s" %(str(e), ExceptionMessage()))
            print "Error: %s at %s" %(str(e), ExceptionMessage())

    def resize_and_save(self, image, fileName):
        resizedIm = image.resize((3840, 2560))
        croppedIm = resizedIm.crop((0, 0, 3840, 2160))
        to_save_path = join(getcwd(), fileName)
        logging.info('Resizing and saving to ' + to_save_path)
        croppedIm.save(to_save_path)
        return join(to_save_path)

if __name__ == "__main__":
    app = App().run()