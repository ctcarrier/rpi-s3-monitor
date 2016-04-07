import re
import time
import os

class Wrapper(object):

    def __init__(self, subprocess):
        self._subprocess = subprocess

    def call(self, cmd):
        p = self._subprocess.Popen(cmd, shell=True, stdout=self._subprocess.PIPE,
            stderr=self._subprocess.PIPE)
        out, err = p.communicate()
        # error handling
        if p.returncode != 0:
            raise Exception(err)
        return p.returncode, out.rstrip(), err.rstrip()

    def call_net(self, cmd):
        p = self._subprocess.Popen(cmd, shell=True, stdout=self._subprocess.PIPE,
            stderr=self._subprocess.PIPE)
        out, err = p.communicate()
        return p.returncode, out.rstrip(), err.rstrip()

class Identify(Wrapper):
    """ A class which wraps calls to the external identify process. """

    def __init__(self, subprocess):
        Wrapper.__init__(self, subprocess)
        self._CMD = 'identify'

    def date_created(self, filepath):
        code, out, err = self.call(self._CMD + ' -verbose ' +  filepath + ' | grep date:create | sed "s|.*T\(.*\):[0-9][0-9]-04:00|\\1|" ')
        return out

    def width(self, filepath):
        code, out, err = self.call(self._CMD + ' -format %w ' + filepath)
        return out

class Convert(Wrapper):
    """ A class which wraps calls to the external convert process. """

    def __init__(self, subprocess):
        Wrapper.__init__(self, subprocess)
        self._CMD = 'convert'

    def overlay_text(self, filepath, text, outpath):
        code, out, err = self.call(self._CMD + ' -background "#0008" -fill white -gravity center -size 3840x300 '
            + 'caption:' + text+ ' '
            + filepath + ' +swap -gravity south -composite  ' + outpath )
        return out