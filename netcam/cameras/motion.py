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

    def __init__(self, roi):
        """ create instance of motions """
        self.roi = roi # region of interest: (x,y,w,h)Tuple
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
        self._bounding_box = [0,0,0,0, False] # x, y, x2(x+w), y2(y+h), empty
        pass

    def __del__(self):
        """ delete instance of motions """
        pass

    def _init_bounding_box(self):
        """ initialize bounding box """
        self._bounding_box[4] = False
        return self._bounding_box

    def _set_bounding_box(self, x, y, w, h):
        """ set bounding box same as first value """
        self._bounding_box[0] = x
        self._bounding_box[1] = y
        self._bounding_box[2] = x + w
        self._bounding_box[3] = y + h
        self._bounding_box[4] = True
        return self._bounding_box

    def _get_bounding_box(self, x,  y, w, h):
        """ calculate the largest bounding box """
        return self._bounding_box

    def _update_bounding_box(self, x,  y, w, h):
        """ calculate the largest bounding box """
        if not self._bounding_box[4]:
            return self._set_bounding_box(x, y, w, h)
        #
        if x < self._bounding_box[0]:
            self._bounding_box[0] = x
        if y < self._bounding_box[1]:
            self._bounding_box[1] = y
        if (x + w) > self._bounding_box[2]:
            self._bounding_box[2] = x + w
        if (y + h) > self._bounding_box[3]:
            self._bounding_box[3] = y + h
        return self._bounding_box

    def _paint_bounding_box(self, frame):
        """ add the bounding box to the frame """
        x1, y1 = self.roi[0], self.roi[1] # region of interest
        cv2.rectangle(frame,
                      (self._bounding_box[0] + x1, self._bounding_box[1] + y1),
                      (self._bounding_box[2] + x1, self._bounding_box[3] + y1),
                      (0, 0, 255), 4) # red frame, 4 pixels thick
        return self._bounding_box

    def parse_frame(self, frame):
        """ parse ONE picture frame (roi) for motions """
        cropped_frame = frame[int(self.roi[1]):int(self.roi[1] + self.roi[3]),
                              int(self.roi[0]):int(self.roi[0] + self.roi[2])]
        # update the background model
        fgMask = self.backSub.apply(cropped_frame)
        # warmup
        if self.warmup > 0:
            # ignore motion in frames for a short while
            self.warmup -= 1
            return False, 0, frame # motion_detected, pixelarea, frame
        # check for motions
        pixelarea = 0
        motion_detected = False
        x1, y1 = self.roi[0], self.roi[1]
        contours, hierarchy = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # [default]
        self._init_bounding_box()
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            area = w * h # pixels
            if area > self.FG_MIN_AREA:
                motion_detected = True
                pixelarea += area
                # [debug] decorate frame with little green boxes (motions)
                # [debug] cv2.rectangle(frame, (x+x1,y+y1), (x+x1+w,y+y1+h), (0, 255, 0), 4)
                self._update_bounding_box(x, y, w, h)
        # finished
        self._paint_bounding_box(frame) # one red box
        return motion_detected, pixelarea, frame


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
