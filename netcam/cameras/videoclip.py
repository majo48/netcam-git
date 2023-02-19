# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os
import threading
import logging
import collections
from datetime import datetime

LEADIN = 15 # frames before first motion detected
LEADOUT = 15 # frames after last motion detected

class VideoClip(threading.Thread):
    """ class for making video clips for one physical video cameras """

    def __init__(self, idx, cam, mtn):
        """ initialize the video clip maker """
        super().__init__()
        self.idx = idx # camera number 0, 1, 2 etc.
        self.camera = cam # frame buffer mpeg
        self.motion = mtn # motion detector
        self.writemode = False # True: writing data to file, False: inactive
        self.fifo = collections.deque([], maxlen=LEADIN) # FIFO queue with [15] frames
        self.filename = 'clip-' # current filename (clip.YYYY-mm-dd.HHMMSS.avi)
        self.keep_running = True
        self.frame_counter = -1 # current frame counter (index number)
        self.fps = 15.0 # current frames per second
        self.vout = None

    def _open_file(self, frame):
        """ open file for writing, order of height, width is critical """
        if self.fps == 0:
            return # ignore this call
        now = datetime.now()
        self.filename = now.strftime('videos/clip'+str(self.idx)+'.%Y-%m-%d.%H%M%S.avi')
        logging.debug('>>> open video file '+self.filename)
        width, height = frame.shape[0], frame.shape[1]
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.vout = cv2.VideoWriter()
        success = self.vout.open(self.filename, fourcc, self.fps, (height, width), True)
        return success

    def _write_to_file(self, frame):
        """ write one frame to file """
        if self.vout is not None:
            self.vout.write(frame)
        pass

    def _close_file(self):
        """ close the open file """
        logging.debug('<<< close video file '+self.filename)
        if self.vout is not None:
            self.vout.release()
            self.vout = None
        pass

    def _write_conditional(self, frame, leadoutfrms):
        """
        write frame to file conditionally
        conditions:
        - leadoutfrms: starts at LEADOUT and is decremented once per frame
        - self.writemode: True: write frame to file, False: inactive
        """
        if frame is None:
            return None # skip frame
        # check conditions
        if leadoutfrms > 0 and not self.writemode:
            # first frame with motion detected
            self.writemode = True
            self._open_file(frame) # open new file
            self._write_to_file(frame) # write frame to file
        elif leadoutfrms > 0 and self.writemode:
            # continue writing frame to file
            self._write_to_file(frame)
        elif leadoutfrms == 0 and self.writemode:
            # stop writing frames to file
            self._write_to_file(frame)
            self._close_file()
            self.writemode = False
        pass

    def run(self):
        """
        connect to camera through the frame buffer, detect motion and make video clips
        stored in the local filesystem and remote cloud backup
        """
        logging.info('>>> Started video clip maker no. '+str(self.idx))
        leadoutsecs = 0 # counts between LEADOUT and zero
        while self.keep_running:
            # get video frame from camara buffer
            frame, self.frame_counter, self.fps = self.camera.get_frame_clone() # thread safe buffer (blocking)
            # detect any motions
            motion_detected, decorated_frame = self.motion.parse_frame(frame)
            if motion_detected:
                leadoutsecs = LEADOUT
            elif leadoutsecs >0:
                leadoutsecs -= 1
            # add frame to left side of bounded FIFO buffer
            self.fifo.appendleft(decorated_frame)
            # get right side frame from FIFO buffer and write to file conditionally
            self._write_conditional(self.fifo[-1], leadoutsecs )
            pass

        if self.writemode:
            self._close_file()
        pass # end run

    def terminate_thread(self):
        """ stop running this thread, called when main thread terminates """
        self.keep_running = False
        pass


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
