# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import time
import cv2
import os
import threading
import collections
from enum import Enum
from netcam.database import database

BUFFER = 10 # must be larger than PREFIX or POSTFIX
PREFIX = 4  # frames before first motion detected
POSTFIX = 4 # frames after last motion detected


class Status(Enum):
    BEGIN = 0
    WAITING = 1
    STARTING = 2
    RECORDING = 3
    STOPPING = 4
    END = 5


class Snapshot(threading.Thread):
    """
    threading daemon for writing a snapshot to file (memory)
    NOTE/MEASUREMENTS:
        1. writing snapshot in same thread: QA is 97.15% average
        2. writing snapshot in other thread: QA is 98.25% average
        3. writing snapshot in other process: QA is 98.44% average
           choose: write snapshot in other thread (keep it simple)
    """

    def __init__(self, frame, filename, logger):
        """ initialize snapshot class """
        threading.Thread.__init__(self)
        self.frame = frame
        self.filename = filename
        self.logger = logger

    def run(self):
        """ write snapshot to file, then terminate """
        time.sleep(1/100) # wait 10 msecs before writing to file
        try:
            cv2.imwrite(self.filename, self.frame)
        except cv2.error:
            self.logger.error('Cannot write to snapshot file: ' + self.filename)
        return # finish thread


class VideoClip(threading.Thread):
    """ class for making video clips for one physical video cameras """

    def __init__(self, idx, cnfg, cam, mtn, lggr):
        """ initialize the video clip maker """
        super().__init__()
        self.idx = idx # camera number 0, 1, 2 etc.
        self.cnfg = cnfg # configuration
        self.camera = cam # frame buffer mpeg
        self.motion = mtn # motion detector
        self.logger = lggr # logger for this camera
        self.fifo = collections.deque([], maxlen=BUFFER) # FIFO queue with [10] frames
        self.filename = '' # current filename
        self.timestamp = '' # timestamp of current file
        self.keep_running = True
        self.nfps = cnfg.get_nominal_fps(idx) # nominal frames per second
        self.vout = None # VideoWriter object
        self._rstate = Status.BEGIN.value # enumeration
        self._rcount = 0
        self._pixel_areas = []
        self._frame_counters = []
        self.db = database.Database() # sqlite3 database (register video files)
        self._max_pixel_area = 0 # pixel area with motion detected
        self._max_frame = None # frame with max motion area

    def _set_snapshot(self, pixel_area, current_frame):
        """ take a snapshot with a maximum of motion """
        if pixel_area > self._max_pixel_area:
            self._max_pixel_area = pixel_area
            self._max_frame = current_frame  # snapshot
        pass

    def _reset_snapshot(self):
        """ delete snapshot """
        self._max_pixel_area = 0
        self._max_frame = None

    def _save_snapshot(self, filename):
        """ save snapshot to jpeg file """
        if self._max_frame is not None:
            jpgname = filename.replace(".avi", ".jpg")
            snpsht = Snapshot(self._max_frame, jpgname, self.logger)
            snpsht.daemon = True
            snpsht.start()
        else:
            self.logger.error('Snapshot frame is missing (None).')
        pass

    def _open_file(self, frame):
        """ open file for writing, order of height, width is critical """
        self.filename, self.timestamp = self.cnfg.get_video_filename(self.idx)
        try:
            self.logger.debug('>>> open video file '+self.filename)
            width, height = frame.shape[0], frame.shape[1]
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.vout = cv2.VideoWriter()
            success = self.vout.open(self.filename, fourcc, self.nfps, (height, width), True)
        except cv2.error:
            self.logger.error('Cannot write to video file: ' + self.filename)
            success = False
        #
        self._reset_snapshot() # reset snapshot frame to None
        return success

    def _write_to_file(self, frame):
        """ write one frame to file """
        if self.vout is not None:
            self.vout.write(frame)
        pass

    def _close_file(self, qpct):
        """ close the open file """
        # close video file
        if self.vout is not None:
            self.vout.release()
            self.vout = None
        # build statistics
        if qpct > 0.0:
            qa = str(round(qpct,1))
            frms = len(self._frame_counters)
            dt = self.timestamp.replace('.', '') # remove dots
            # register clip in database
            self.db.set_clip(self.filename, self.idx, dt, {"qa":qa, "frms": frms})
            # log closure event
            self.logger.debug('<<< close video file '+self.filename+', QA: '+qa+'%, frames: '+str(frms))
            # save snapshot to file
            self._save_snapshot(self.filename)
        pass

    def _check_quality(self):
        """
        check the quality of the recording in terms of frames missed
        - tm = missed frames
        - tot = last frame counter - first frame counter
        - quality = (tot-tm)/tot in percent, e.g. 99% @ 4 fps (nominal)
        """
        size = len(self._frame_counters)
        if size >0:
            first = self._frame_counters[0]
            if first >0:
                last = self._frame_counters[-1]
                tot = last-first
                tm = tot -size +1
                return (tot-tm)/tot*100

    def _record(self, motion_detected, pixel_area, fifo):
        """ state machine for recording videoclips """
        frame = fifo[0]
        frame_counter = fifo[1]
        if self._rstate == Status.BEGIN.value:
            self._rstate = Status.WAITING.value

        elif self._rstate == Status.WAITING.value:
            if motion_detected:
                self._rstate = Status.STARTING.value
                self._rcount = 1 # set counter
                self._pixel_areas.append(pixel_area)

        elif self._rstate == Status.STARTING.value:
            if motion_detected:
                self._rcount += 1 # increment counter
                self._pixel_areas.append(pixel_area)
                if self._rcount >= BUFFER-PREFIX:
                    self._frame_counters = [] # make empty list
                    if self._open_file(frame):
                        # successfully opened .avi file
                        self._frame_counters.append(frame_counter) # add frame counter to list
                        self._write_to_file(frame) # write first frame to file
                        self._rstate = Status.RECORDING.value
                        self._pixel_areas = []
                    else:
                        # failed to open file
                        self.logger.critical("Failed to open file: "+self.filename)
                        self._rstate = Status.WAITING.value # try again
            else:
                # no motion detected while starting, fall back immediately
                self._rstate = Status.WAITING.value # change state

        elif self._rstate == Status.RECORDING.value:
            self._frame_counters.append(frame_counter) # add frame counter to list
            self._write_to_file(frame) # write next frame to file
            if not motion_detected:
                self._rstate = Status.STOPPING.value # change state
                self._rcount = 1 # set counter, first missing motion detected

        elif self._rstate == Status.STOPPING.value:
            self._frame_counters.append(frame_counter) # add frame counter to list
            self._write_to_file(frame)  # write next frame to file
            if motion_detected:
                self._rstate = Status.RECORDING.value  # change state
            else:
                self._rcount += 1  # increment counter
                if self._rcount >= BUFFER+POSTFIX:
                    qpct = self._check_quality()
                    self._close_file(qpct)
                    self._rstate = Status.WAITING.value  # change state

        elif self._rstate == Status.END.value:
            self._close_file(0.0)
        else:
            self.logger.critical("Illegal recording state encountered: "+str(self._rstate))
            self._rstate = Status.WAITING.value # try again
        pass

    def run(self):
        """
        connect to camera through the frame buffer, detect motion and make video clips
        stored in the local filesystem and remote cloud backup
        """
        self.logger.info(">>> Started video clip recorder in " + threading.currentThread().getName())
        while self.keep_running:
            # get video frame from camara buffer
            frame, frame_counter = self.camera.get_frame_clone() # thread safe buffer (blocking)

            # detect motions
            motion_detected, pixel_area, decorated_frame = self.motion.parse_frame(frame)
            if motion_detected:
                self._set_snapshot(pixel_area, decorated_frame)  # set snapshot of maximum motion

            # add frame to left side of bounded FIFO buffer
            self.fifo.appendleft((frame, frame_counter))

            # get right side frame from FIFO buffer and write to file conditionally
            self._record(motion_detected, pixel_area, self.fifo[-1])
            pass

        if self._rstate == Status.RECORDING.value or self._rstate == Status.STOPPING.value:
            self._close_file(0.0)
        self._rstate = Status.END.value
        self.logger.info("<<< Stopped video clip recorder in " + threading.currentThread().getName())
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
