#!/usr/bin/env python

import signal
import tinys3
import logging
import os
from os import listdir
from os.path import isfile, join, isdir
from config_persist import Persist
import time
import linecache
import sys
import shutil

SETTINGS_FILE = "/var/lib/s3monitor/settings.cfg"
LOG_FILENAME = '/var/log/s3monitor/s3monitor.log'
__version__ = "1.0"
ARCHIVED_FOLDER = "archived"

def archiveFile(folder, fileName):
    archivedDir = join(folder, ARCHIVED_FOLDER)
    if not os.path.exists(archivedDir):
        os.makedirs(archivedDir)
    logging.info("Archiving %s"%(fileName))
    shutil.move(join(folder, fileName), join(archivedDir, fileName))

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
        logging.info("S3 Monitor %s"%__version__)

        self.startMonitor()

    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    def run(self):
        self.startup()

    def startMonitor(self):
        logging.info('Monitor started')
        logging.info('Before try')
        try:
            persist = Persist()

            # while True:
            settings = persist.readLastConfig(SETTINGS_FILE)
            logging.info("Settings: " +str(settings))
            toMonitor = settings["toMonitor"]
            S3_SECRET_KEY = settings['AWS_SECRET_ACCESS_KEY']
            S3_ACCESS_KEY = settings['AWS_ACCESS_KEY_ID']
            self.conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True)

            while True:
                for monitor in toMonitor:
                    for f in listdir(monitor['folder']):
                        logging.info('%s a folder? %s' % (join(monitor['folder'], f), isdir(join(monitor['folder'], f))))
                        if not isdir(join(monitor['folder'], f)):
                            logging.info('Synching %s to %s' % (f, monitor['bucket']))
                            logging.info('Going to upload %s' % f)
                            with open(join(monitor['folder'], f),'rb') as file:
                                self.conn.upload(f,file,monitor['bucket'])
                                archiveFile(monitor['folder'], f)
                time.sleep(60)
        except Exception,e:
            logging.error("Error: %s at %s" %(str(e), ExceptionMessage()))
            print "Error: %s at %s" %(str(e), ExceptionMessage())

if __name__ == "__main__":
    app = App().run()