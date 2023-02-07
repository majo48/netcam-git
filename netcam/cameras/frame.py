# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# class modul for thread safe storage of a stream of frames from a video camera

import threading
import copy
import imutils
import os
import time

class Frame:
    """ protected (thread safe) storage of video frames """

    def __init__(self, frm):
        """ initialize an instance of the class """
        self.frame = frm # save the first frame
        self.semaf = threading.Semaphore(value=1)
        self.frame_count = 0
        self.init_time = time.time()

    def set_frame(self, frm):
        """ write (protected) a new frame """
        with self.semaf:
            self.frame = frm
            self.frame_count += 1
        pass

    def get_frame_count(self):
        """ get the number of frames processed """
        return self.frame_count

    def get_fps(self):
        """ get (an approximate) frames per second """
        secs = time.time() - self.init_time
        fps = self.frame_count / secs
        return round(fps, 0)

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
