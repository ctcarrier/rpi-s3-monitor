#!/usr/bin/env python

import subprocess

#!/usr/bin/env python

import os
from os import listdir
from os.path import join
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

from wrappers import Identify
from wrappers import Convert
from s3_service import S3Service

FFMPEG_BIN = "ffmpeg"
SETTINGS_FILE = "/var/lib/s3timelapse/settings.cfg"
OUTPUT_DIR = '/var/lib/s3timelapse/output/timelapse.mp4'
LOG_FILENAME = '/var/log/s3monitor/s3monitor.log'
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
        self.DEBUG_OUTPUT_DIR = '/tmp'
        self.start_frame = self.settings['startFrame']

        self.identify = Identify(subprocess)
        self.convert = Convert(subprocess)
        self.s3_service = S3Service(S3_SECRET_KEY, S3_ACCESS_KEY)

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
        processedPrefix = self.settings['processedPrefix']
        try:
            bucket = self.conn.get_bucket(self.settings['bucket'])
            processed_bucket = self.conn.get_bucket(self.settings['processedBucket'])
            bucketList = bucket.list(self.settings['prefix'] + '/IMG')
            logging.info('Bucket: {} processedBucket: {}'.format(self.settings['bucket'], self.settings['processedBucket']))
            for idx, item in enumerate(bucketList):

                file_name = item.name[item.name.index('/')+1 : len(item.name)]
                processed_file_name = '{}/{}'.format(processedPrefix, file_name)
                print join(self.DEBUG_OUTPUT_DIR, file_name)
                print processed_file_name
                existing_file = bucket.get_key(processed_file_name)
                if existing_file == None:
                    print 'File new, saving'
                    im = self.get_image_from_bucket(bucket, item.name)
                    tmp_file_path = self.resize_and_save(im, file_name)
                    processed_file_path = self.overlay_text(tmp_file_path, idx)
                    logging.info('Uploading {} to bucket: {} and key {}'.format(processed_file_path, processed_bucket, file_name))
                    self.s3_service.uploadFileToS3(processed_bucket, processed_file_name, processed_file_path)
                    self.remove_file(tmp_file_path)
                    self.remove_file(processed_file_path)

                    print 'Saved'
        except Exception,e:
            logging.error("Error: %s at %s" %(str(e), ExceptionMessage()))
            print "Error: %s at %s" %(str(e), ExceptionMessage())

    def remove_file(self, file_path):
        os.remove(file_path)

    def get_image_from_bucket(self, bucket, name):
        fileContents = bucket.get_key(name).get_contents_as_string()
        output = StringIO.StringIO()
        output.write(fileContents)
        logging.info('Getting image')
        return Image.open(output)

    def resize_and_save(self, image, fileName):
        resizedIm = image.resize((3840, 2560))
        croppedIm = resizedIm.crop((0, 0, 3840, 2160))
        to_save_path = join(self.DEBUG_OUTPUT_DIR, fileName)
        logging.info('Resizing and saving to ' + to_save_path)
        croppedIm.save(to_save_path)
        return join(to_save_path)

    def overlay_text(self, file_path, idx):
        minutes = 10 * idx
        hours = minutes/60
        minuteRemainder = minutes%60
        overlay_text = '{} hours'.format(hours)
        new_file_path = file_path + '.tmp'
        logging.info('Overlaying text: {} on file: {} and saving to {}'.format(str(overlay_text), file_path, new_file_path))
        self.convert.overlay_text(file_path, overlay_text, new_file_path)
        return new_file_path

if __name__ == "__main__":
    app = App().run()