"""
    Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
"""

import cv2
import numpy as np
import os
from operator import itemgetter

class Motions:
    """ detect motions in video stream frames """

    BG_SUB_METHODE = 'MOG2' # backgrounde subtraction methode: ( 'MOG2', 'KNN')
    FG_MIN_AREA = 500 # minimal size of green boxes

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
        """
            parse one frame in the video stream
        """
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
        boxes = self._merge_overlaps(contours, frame)
        for box in boxes:
            if box["valid"]:
                motionDetected = True
                cv2.rectangle(frame, (box['x'], box['y']), (box['x2'], box['y2']), (0, 255, 0), 4)
            else:
                dummy = 'stopq'
        # finished
        return motionDetected, frame

    def _merge_overlaps(self, contours, frame=None):
        """
            merge all overlaps in the contours list
        """
        # build list of boxes fro, the contours
        boxes = []
        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            area = w * h # pixels
            if area > self.FG_MIN_AREA:
                boxes.append({
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'x2': x + w, 'y2': y + h, 'area': area,
                    'order': i, 'valid': True })
                # display the contours in red
                # if frame is not None:
                #     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 10)

        # check for overlaps
        for i in range(len(boxes)):
            box1 = boxes[i]
            if box1["valid"]:
                for j in range(i+1, len(boxes)):
                    box2 = boxes[j]
                    if box2["valid"]:
                        intersects, area = self._intersecting_boxes(box1, box2)
                        if intersects:
                            boxes[i], boxes[j] = self._merge_boxes(box1, box2)
        # finished
        return boxes

    def _intersecting_boxes(self, boxA, boxB):
        """
            Check if two rectangles intersect, using opencv coordinates,
            defined as: top left is [0, 0], both x and y ascending (>0).
            This can return a positive result, with an empty area (w*h == 0).
        """
        x = max(boxA["x"], boxB["x"])
        y = max(boxA["y"], boxB["y"])
        w = min(boxA["x"] + boxA["w"], boxB["x"] + boxB["w"]) - x
        h = min(boxA["y"] + boxA["h"], boxB["y"] + boxB["h"]) - y
        intersects = True
        if w < 0 or h < 0:
            intersects = False
        return intersects, [x, y, w, h]

    def _merge_boxes(self, box1, box2):
        """"
            merge box2 into box1
        """
        # recalculate borders and size of box1
        box1["x"] = min(box1["x"], box2["x"]) # leftmost value
        box1["y"] = min(box1["y"], box2["y"]) # topmost value
        box1["x2"] = max(box1["x2"], box2["x2"]) # rightmost value
        box1["y2"] = max(box1["y2"], box2["y2"]) # bottommost value
        box1["w"] = box1["x2"] - box1["x"]
        box1["h"] = box1["y2"] - box1["y"]
        box1["area"] = box1["w"] * box1["h"]
        # cancel box2
        box2["valid"] = False
        # finished
        return box1, box2


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
