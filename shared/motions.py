"""
    This file contains code for detecting motions in video streams.
    Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
"""

import cv2
import numpy as np
import os


class Motions:
    """ detect motions in video stream frames """

    BLUR_PERCENT = 4 # (4) blur frames to cancel small movements (e.g. moving leaves)
    DELTA_THRESH = 5 # (5) absolut value difference for any pixel to be “triggered” as motion
    FRAME_WEIGHT = 0.5 # (0.5) Weight of the input image. A scalar double.

    def __init__(self, vidObj):
        """ create instance of motions """
        self.vidObj = vidObj
        ret, frame = vidObj.read() # get first frame
        if ret:
            self.frameDimensions = frame.shape # pixels: (height, width, colors)
            blur = round(self.frameDimensions[0] * self.BLUR_PERCENT / 100)
            self.blur = (blur, blur) # blur range
            self._init_background_frame(frame) # into self.bgFrame
        else:
            raise ValueError('Cannot open first video frame in stream.')
        pass

    def __del__(self):
        """ delete instance of motions """
        pass

    def _build_basic_frame(self, frame):
        """ convert frame to greyscale and blur it """
        basicFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # convert to greyscale
        basicFrame = cv2.GaussianBlur(basicFrame, self.blur, 0) # blur the frame
        return basicFrame

    def _init_background_frame(self, frame):
        """ initialize the background frame with the first frame in the stream """
        basicFrame = self._build_basic_frame(frame)
        self.bgFrame = basicFrame.copy().astype("float") # save frame as float type
        pass

    def parse_frame(self, frame):
        """ parse one frame in the video stream """
        basicFrame = self._build_basic_frame(frame)
        # accumulate frame to weighted running average
        bgFrameCopy = self.bgFrame
        cv2.accumulateWeighted(basicFrame, self.bgFrame, self.FRAME_WEIGHT)
        # build diff between fore- and background
        diffFrame = cv2.absdiff(basicFrame, cv2.convertScaleAbs(self.bgFrame))
        # enhance the diff between fore- and background
        thresholdFrame = cv2.threshold(diffFrame, self.DELTA_THRESH, 255, cv2.THRESH_BINARY)[1]
        # Display the resulting frame
        cv2.imshow('Threshold', thresholdFrame)
        # NOTE: the image shown above, includes "shadows" from previous frames,
        # ----  basically showing two persons walking instead of one.
        pass


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
