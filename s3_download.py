#!/usr/bin/env python

import subprocess as sp

#!/usr/bin/env python

from os import listdir
import signal
import tinys3
import logging
from PIL import Image
from config_persist import Persist
import time
import linecache
import sys
import boto
import boto.s3.connection
import StringIO

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
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format='%(asctime)s %(message)s')
        logging.info('Started %s' % __file__)
        logging.info("S3 Timelapse %s"%__version__)

        self.persist = Persist()
        self.settings = self.persist.readLastConfig(SETTINGS_FILE)
        logging.info("Settings: " +str(self.settings))
        S3_SECRET_KEY = self.settings['AWS_SECRET_ACCESS_KEY']
        S3_ACCESS_KEY = self.settings['AWS_ACCESS_KEY_ID']
        self.DEBUG_OUTPUT_DIR = self.settings['folder']

        self.conn = boto.connect_s3(
            aws_access_key_id = S3_ACCESS_KEY,
            aws_secret_access_key = S3_SECRET_KEY)

        self.start()

    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    def run(self):
        self.startup()

    def start(self):
        logging.info('Timelapse monitor started')
        try:
            bucket = self.conn.get_bucket(self.settings['bucket'])
            bucketList = bucket.list(self.settings['prefix'] + '/IMG')
            # self.conn.list(self.settings['prefix'], self.settings['bucket'])
            existingFiles = listdir(self.DEBUG_OUTPUT_DIR)
            for item in bucketList:
                fileName = item.name[item.name.index('/')+1 : len(item.name)]
                print self.DEBUG_OUTPUT_DIR + fileName
                if fileName not in existingFiles:
                    print 'File new, saving'
                    fileContents = bucket.get_key(item.name).get_contents_as_string()
                    output = StringIO.StringIO()
                    output.write(fileContents)
                    im = Image.open(output)
                    im.save(self.DEBUG_OUTPUT_DIR + fileName)
                    print 'Saved'
        except Exception,e:
            logging.error("Error: %s at %s" %(str(e), ExceptionMessage()))
            print "Error: %s at %s" %(str(e), ExceptionMessage())

if __name__ == "__main__":
    app = App().run()