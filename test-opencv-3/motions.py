"""
    Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
"""

import cv2
import numpy as np
import os

class Motions:
    """ detect motions in video stream frames """

    BG_SUB_METHODE = 'MOG2' # backgrounde subtraction methode: ( 'MOG2', 'KNN')

    def __init__(self, vidObj):
        """ create instance of motions """
        self.vidObj = vidObj
        if self.BG_SUB_METHODE == 'MOG2':
            self.backSub = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=400.0, detectShadows=False)
        elif self.BG_SUB_METHODE == 'KNN':
            self.backSub = cv2.createBackgroundSubtractorKNN(
                history=500, dist2Threshold=400.0, detectShadows=False)
        else:
            self.backSub = None
            raise ValueError('Illegal background subtraction methode defined.')
        pass

    def __del__(self):
        """ delete instance of motions """
        pass

    def parse_frame(self, frame):
        """ parse one frame in the video stream """

        # update the background model
        fgMask = self.backSub.apply(frame)
        cv2.imshow('FG Mask', fgMask)

        # display frame number in frame
        fnum = str(int(self.vidObj.get(cv2.CAP_PROP_POS_FRAMES)))
        cv2.rectangle(frame, (10, 2), (100, 20), (255, 255, 255), -1)
        cv2.putText(frame, fnum, (15, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))

        # check for motions
        motionDetected = False
        contours, hierarchy = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        minArea = (500)
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            if (w * h) > minArea:
                motionDetected = True
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return motionDetected, frame

if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
