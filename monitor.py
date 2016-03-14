import tinys3
import logging
import os
from os import listdir
from os.path import isfile, join
from config_persist import Persist
from datetime import datetime
from datetime import timedelta

SETTINGS_FILE = "/var/lib/s3monitor/settings.cfg"
LOG_FILENAME = '/var/log/s3monitor/s3monitor.log'
__version__ = "1.0"


class App():
    def startup(self):
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format='%(asctime)s %(message)s')
        logging.info('Started %s' % __file__)
        logging.info("S3 Monitor %s"%__version__)

        S3_SECRET_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
        S3_ACCESS_KEY = os.environ['AWS_ACCESS_KEY_ID']

        self.conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True)
        self.startMonitor()

    def run(self):
        self.startup()

    def startMonitor(self):
        persist = Persist()

        # while True:
        toMonitor = persist.readLastConfig(SETTINGS_FILE)
        logging.info("Settings: " +str(toMonitor))

        for monitor in toMonitor:
            logging.info('Syncing ' +str(monitor['folder']))
            logging.info('Synching %s to %s' % (monitor['folder'], monitor['bucket']))
            for f in listdir(monitor['folder']):
                logging.info(f)
                if isfile(join(monitor['folder'], f)):
                    logging.info('Going to upload %s' % f)
                    with open(join(monitor['folder'], f),'rb') as file:
                        self.conn.upload(f,file,monitor['bucket'])

if __name__ == "__main__":
    app = App().run()