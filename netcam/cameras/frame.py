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
        self.fps = 0 # frames per second
        pass

    def _calc_fps(self):
        """ calculate average value of frames per second, every 100 frames """
        now = time.time()
        fps = 100 / (now - self.init_time)
        if self.fps == 0:
            self.fps = fps # first calculation
        self.fps = (fps + self.fps) / 2  # average value
        self.init_time = now
        pass

    def set_frame(self, frm):
        """ write (protected) a new frame """
        with self.semaf:
            self.frame = frm
            self.frame_count += 1
            if (self.frame_count % 100) == 0:
                self._calc_fps()
        pass

    def get_frame_count(self):
        """ get the number of frames processed """
        with self.semaf:
            return self.frame_count

    def get_fps(self):
        """ get (average) frames per second """
        with self.semaf:
            return round(self.fps, 1)

    def get_clone(self):
        """
        get a clone (protected) of the current frame
        :returns clone, counter
        """
        with self.semaf:
            cln = copy.deepcopy(self.frame)
            count = self.frame_count
            return cln, count


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
