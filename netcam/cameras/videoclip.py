# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os
import threading
import logging
import collections
from datetime import datetime
from enum import Enum

LEADIN = 10 # frames before first motion detected
LEADOUT = 10 # frames after last motion detected
LEADDELTA = 3 # DELTA: must be max. LEADIN or LEADOUT

class Status(Enum):
    BEGIN = 0
    WAITING = 1
    STARTING = 2
    RECORDING = 3
    STOPPING = 4
    END = 5

class VideoClip(threading.Thread):
    """ class for making video clips for one physical video cameras """

    def __init__(self, idx, nfps, cam, mtn):
        """ initialize the video clip maker """
        super().__init__()
        self.idx = idx # camera number 0, 1, 2 etc.
        self.camera = cam # frame buffer mpeg
        self.motion = mtn # motion detector
        self.fifo = collections.deque([], maxlen=LEADIN) # FIFO queue with [15] frames
        self.filename = 'clip-' # current filename (clip.YYYY-mm-dd.HHMMSS.avi)
        self.keep_running = True
        self.frame_counter = -1 # current frame counter (index number)
        self.previous_counter = 0 # previous frame counter (index number)
        self.delta_average = 0 # frames missed: average(current-previous)
        self.nfps = nfps # nominal frames per second
        self.fps = nfps # current frames per second
        self.vout = None # VideoWriter object
        self._rstate = Status.BEGIN.value # enumeration
        self._rcount = 0
        self._pixelareas = []

    def _open_file(self, frame):
        """ open file for writing, order of height, width is critical """
        now = datetime.now()
        self.filename = now.strftime('videos/clip'+str(self.idx)+'.%Y-%m-%d.%H%M%S.avi')
        logging.debug('>>> open video file '+self.filename)
        width, height = frame.shape[0], frame.shape[1]
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.vout = cv2.VideoWriter()
        success = self.vout.open(self.filename, fourcc, self.nfps, (height, width), True)
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

    def _record(self, motion_detected, pixelarea, frame):
        """ state machine for recording videoclips """
        if self._rstate == Status.BEGIN.value:
            self._rstate = Status.WAITING.value

        elif self._rstate == Status.WAITING.value:
            if motion_detected:
                self._rstate = Status.STARTING.value
                self._rcount = 1 # set counter
                self._pixelareas.append(pixelarea)

        elif self._rstate == Status.STARTING.value:
            if motion_detected:
                self._rcount += 1 # increment counter
                self._pixelareas.append(pixelarea)
                if self._rcount >= LEADIN-LEADDELTA:
                    if self._open_file(frame):
                        # successfully opened .avi file
                        self._write_to_file(frame) # write first frame to file
                        self._rstate = Status.RECORDING.value
                        # logging.debug('??? Pixels before opening file: '+str(self._pixelareas)) # [debug]
                        self._pixelareas = []
                    else:
                        # failed to open file
                        logging.critical("Failed to open file: "+self.filename)
                        self._rstate = Status.WAITING.value # try again
            else:
                # no motion detected while starting, fall back immediately
                self._rstate = Status.WAITING.value # change state

        elif self._rstate == Status.RECORDING.value:
            self._write_to_file(frame)  # write next frame to file
            if not motion_detected:
                self._rstate = Status.STOPPING.value # change state
                self._rcount = 1 # set counter, first missing motion detected

        elif self._rstate == Status.STOPPING.value:
            self._write_to_file(frame)  # write next frame to file
            if motion_detected:
                self._rstate = Status.RECORDING.value  # change state
            else:
                self._rcount += 1  # increment counter
                if self._rcount >= LEADOUT-LEADDELTA:
                    self._close_file()
                    self._rstate = Status.WAITING.value  # change state

        elif self._rstate == Status.END.value:
            self._close_file()
        else:
            logging.critical("Illegal recording state encountered: "+str(self._rstate))
            self._rstate = Status.WAITING.value # try again
        pass

    def _quality_test(self, frame_counter):
        """ calculate quality of frames missed """
        delta = frame_counter - self.previous_counter
        self.previous_counter = frame_counter
        if delta < LEADOUT:
            avg = (self.delta_average + delta) / 2
        else:
            avg = delta
        return avg

    def run(self):
        """
        connect to camera through the frame buffer, detect motion and make video clips
        stored in the local filesystem and remote cloud backup
        """
        logging.info(">>> Started video clip maker in " + threading.currentThread().getName())
        while self.keep_running:
            # get video frame from camara buffer
            frame, self.frame_counter = self.camera.get_frame_clone() # thread safe buffer (blocking)
            self.delta_average = self._quality_test(self.frame_counter) # quality benchmark

            # detect motions
            motion_detected, pixelarea, decorated_frame = self.motion.parse_frame(frame)

            # add frame to left side of bounded FIFO buffer
            self.fifo.appendleft(decorated_frame)

            # get right side frame from FIFO buffer and write to file conditionally
            self._record(motion_detected, pixelarea, self.fifo[-1])
            # self._record(motion_detected, pixels, frame) # [debug] w.o. green motion objects (boxes)
            pass

        logging.debug('*** Quality benchmark: '+str(self.delta_average)+' (should be 1.00).')
        if self._rstate == Status.RECORDING.value or self._rstate == Status.STOPPING.value:
            self._close_file()
        self._rstate = Status.END.value
        logging.info("<<< Stopped video clip maker in " + threading.currentThread().getName())
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
