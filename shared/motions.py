"""
    This file contains code for detecting motions in video streams.
    Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
"""

import cv2
import numpy as np
import os


class Motions:

    def __init__(self, vidObj):
        """ create instance of motions """
        self.vidObj = vidObj
        self.prevFrame = None
        pass

    def __del__(self):
        """ delete instance of motions """
        pass

    def parseFrame(self, frame):
        """ parse one frame """
        if self.prevFrame is not None:
            self._parseFrames(frame, self.prevFrame)
        self.prevFrame = frame

    def _parseFrames(self, frame1, frame2):
        """ parse two subsequent frames (first and second frame) """
        pass


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.'
    )
