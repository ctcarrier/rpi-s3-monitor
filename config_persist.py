import json
import os

class Persist():

    #http://stackoverflow.com/a/10352231/810944
    @staticmethod
    def touchopen(filename, *args, **kwargs):
        # Open the file in R/W and create if it doesn't exist. *Don't* pass O_TRUNC
        fd = os.open(filename, os.O_RDWR | os.O_CREAT)

        # Encapsulate the low-level file descriptor in a python file object
        return os.fdopen(fd, *args, **kwargs)
   
    @staticmethod
    def readLastConfig(filename):
        with Persist.touchopen(filename, "r+") as target:
            try:
                settings = json.load(target)
            except ValueError:
                settings = []
            return settings
