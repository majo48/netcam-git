# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os

class Motion:
    """
        detect motion in video stream frames, using standard
        built-in background subtraction methods (opencv)
    """
    BG_SUB_METHODE = 'MOG2' # [default] background subtraction methods are: ( 'MOG2', 'KNN')
    FG_MIN_AREA = 500       # [default] minimal size of green boxes (sensitivity)

    def __init__(self, vidObj):
        """ create instance of motions """
        self.vidObj = vidObj
        if self.BG_SUB_METHODE == 'MOG2':
            self.backSub = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=400.0, detectShadows=False) # [default]
        elif self.BG_SUB_METHODE == 'KNN':
            self.backSub = cv2.createBackgroundSubtractorKNN(
                history=500, dist2Threshold=400.0, detectShadows=False) # [default]
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
        # cv2.imshow('FG Mask', fgMask) # [debug] show background model

        # check for motions
        motion_detected, max_pixels, max_bounds = False, 0, {}
        contours, hierarchy = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # [default]
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            area = w * h # pixels
            if area > self.FG_MIN_AREA:
                motion_detected = True
                if area > max_pixels:
                    max_pixels = area
                    max_bounds = {"x": x, "y": y, "w": w, "h": h}

        # build results
        if motion_detected:
            # decorate frame with one motion rectangle
            cv2.rectangle(frame,
                (max_bounds['x'], max_bounds['y']),
                (max_bounds['x']+max_bounds['w'], max_bounds['y']+max_bounds['h']),
                (0, 255, 0), 4) # [default] rectangle.color=green 4px thick
        return motion_detected, frame


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
