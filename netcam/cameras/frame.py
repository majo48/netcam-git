# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# frame class modul for storage of frames from video cameras

import threading
import copy
import imutils
import os

class Frame:
    """ protected (thread safe) storage of video frames """

    def __init__(self, frm):
        """ initialize an instance of the class """
        self.frame = frm # save the first frame
        self.semaf = threading.Semaphore(value=1)

    def set_frame(self, frm):
        """ write (protected) a new frame """
        with self.semaf:
            self.frame = frm
        pass

    def get_clone(self):
        """ get a clone (protected) of the current frame """
        with self.semaf:
            cln = copy.deepcopy(self.frame)
        return cln

    def get_picture(self, width):
        """ get the jpeg representation of the current frame """
        with self.semaf:
            pic = imutils.resize(self.frame, width)
        return pic


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
