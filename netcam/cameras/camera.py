# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import queue
from imutils.video import VideoStream
import os
import threading


class Camera(threading.Thread):
    """ class for one physical video cameras """

    def __init__(self, idx, rtsp_url):
        """
        initialize connection to one physical video camera
        """
        threading.Thread.__init__(self)
        self.idx = idx # thread index
        self.rtsp_url = rtsp_url # url of the external camera
        self.frame_count = 0 # frame count
        self.skipped_frames = 0 # counts the number of frames skipped
        self.qq = queue.Queue(maxsize=1) # interface to other threads
        self.keep_running = True

    def run(self):
        """
        open/connect video stream from one physical video camera
        """
        thread = threading.currentThread()
        vs = VideoStream(self.rtsp_url).start()
        print("Start video stream in thread '" + thread.name + "'\n")
        # loop through all frames provided by the camera stream
        while self.keep_running:
            # get frames from camera (blocking)
            frame = vs.read()
            # check frame
            if frame is None:
                # todo: add some proper error handling here
                continue
            # increment frame count
            self.frame_count += 1
            # put one frame in the queue
            try:
                self.qq.put(frame, block=False)
            except queue.Full:
                # queue already has a frame (not consumed)
                self.skipped_frames += 1
            pass # keep on looping

        cv2.destroyAllWindows()
        vs.stop()

    def get_frame_count(self):
        """ get the frame count """
        return self.frame_count

    def get_frame(self):
        """ get frame (with blocking) """
        return self.qq.get(block=True, timeout=None)

    def terminate_thread(self):
        """ stop running this thread, called when main thread terminates """
        self.keep_running = False
        pass # try again

if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
