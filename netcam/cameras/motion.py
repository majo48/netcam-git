# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os

class Motion:
    """
        detect motion in video stream frames, using standard
        built-in background subtraction methods (opencv)
        https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.12.3705&rep=rep1&type=pdf
    """
    BG_SUB_METHODE = 'MOG2' # [default] background subtraction methods are: ( 'MOG2', 'KNN')
    FG_MIN_AREA = 500       # [default] minimal size of green boxes (sensitivity)
    WARMUP_FRAMES = 100     # [default] frames read (delay) before detecting motions

    def __init__(self, vidObj):
        """ create instance of motions """
        self.vidObj, self.width, self.height = vidObj, None, None
        self.warmup = self.WARMUP_FRAMES
        if self.BG_SUB_METHODE == 'MOG2':
            self.backSub = cv2.createBackgroundSubtractorMOG2(
                history=100, varThreshold=400.0, detectShadows=False) # [defaults: 500, 400, False]
        elif self.BG_SUB_METHODE == 'KNN':
            self.backSub = cv2.createBackgroundSubtractorKNN(
                history=500, dist2Threshold=400.0, detectShadows=False) # [defaults: 500, 400, False]
        else:
            self.backSub = None
            raise ValueError('Illegal background subtraction methode defined.')
        pass

    def __del__(self):
        """ delete instance of motions """
        pass

    def parse_frame(self, frame):
        """ parse one frame in the video stream """
        fgMask = self.backSub.apply(frame) # update the background model
        if self.warmup > 0:
            if (frame is not None) and (self.width is None or self.height is None):
                self.vidObj = frame # copy of first frame
                self.width = frame.shape[0]
                self.height = frame.shape[1]
            # ignore motion in frames for a short time
            self.warmup -= 1
            return False, frame

        # check for motions
        motion_detected = False
        contours, hierarchy = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # [default]
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            area = w * h # pixels
            if area > self.FG_MIN_AREA:
                motion_detected = True
                # decorate frame with little green boxes (motions)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0, 255, 0), 4)

        return motion_detected, frame


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
