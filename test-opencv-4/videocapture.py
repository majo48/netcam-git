"""
    Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
"""

import cv2
import os

class VideoCapture:
    """
        custom video capture object, reading frames from dataset2012 ../input folders
    """

    def __init__(self, path_filename):
        """ create instance of VideoCapture """
        self.next_filename = path_filename
        # open next_filename
        if os.path.isfile(self.next_filename):
            # file exists
            img = cv2.imread(self.next_filename)  # reads an image in the BGR format
            self.frame_number = 1
            shape = img.shape
            self.high = shape[0]
            self.wide = shape[1]
            self.opened = True
        else:
            # could not open next_filename
            self.frame_number = 0
            self.high = 0
            self.wide = 0
            self.opened = False
        pass # end of initialization

    def __del__(self):
        """ object destructor """
        # print('Destructor called, VideoCapture object deleted')

    def isOpened(self):
        """ has this object found the next frame, or not """
        return self.opened

    def get(self, property):
        """ get the cv2.CAP_PROP_POS_FRAMES property """
        if property == cv2.CAP_PROP_POS_FRAMES:
            # return the frame number
            return self.frame_number
        else:
            return 0

    def get_statistics(self):
        """ get file statistics """
        return str(self.high)+'x'+str(self.wide)+' pixels'

    def read(self):
        """
            get the next frame from the /input folder
            returns:
                success: True or False
                frame: ndarray or None
        """
        if os.path.isfile(self.next_filename):
            # file exists
            img = cv2.imread(self.next_filename)  # reads an image in the BGR format
            self.opened = True
            self.next_filename = self._get_next(self.next_filename)
        else:
            img = None
            self.opened = False
        return self.opened, img

    def _get_next(self, filename):
        """ get next filename (increment once) """
        head, tail = os.path.split(filename)
        leadin = tail[0:2]
        extension = tail[-4:]
        if leadin == 'in' and extension == '.jpg':
            self.frame_number = int(tail[2:8]) + 1
            scnt = f'{self.frame_number:06}' # string with leading zeros
            return head + '/' + leadin + scnt + extension
        else:
            return 'error'


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
