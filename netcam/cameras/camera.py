# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os
import threading
import logging


class Camera(threading.Thread):
    """ class for one physical video cameras """

    def __init__(self, idx, rtsp_url, frm):
        """
        initialize connection to one physical video camera
        """
        threading.Thread.__init__(self)
        self.idx = idx # thread index
        self.rtsp_url = rtsp_url # url of the external camera or webcam index
        self.frame = frm # static class: netcam-git.netcam.cameras.frame.Frame
        self.frame_count = 0 # frame count
        self.skipped = 0 # skipped frame count
        self.sync_event = threading.Event()
        self.sync_event.clear() # not set
        self.keep_running = True # maintain video streaming from this camera

    def run(self):
        """
        open/connect video stream from one physical video camera
        """
        thread = threading.currentThread()
        stream = cv2.VideoCapture(self.rtsp_url)
        logging.info(">>> Started video stream in thread '" + thread.name)
        # loop through all frames provided by the camera stream
        while self.keep_running:
            # get one frame from camera
            ret, frm = stream.read()
            # check frame
            if frm is None:
                self.skipped += 1
                continue # todo: add some proper error handling here
            # increment frame count
            self.frame.set_frame(frm)
            self.frame_count += 1
            # start consumer threads waiting in get_frame()
            self.sync_event.set()

        logging.info("<<< Stopped video stream in thread '" + thread.name)
        cv2.destroyAllWindows()
        stream.release()

    def get_frame_count(self):
        """ get the frame count """
        return self.frame_count

    def get_frame_clone(self):
        """ get cloned frame from provider (this instance) """
        # wait for sync
        self.sync_event.wait()
        # restart the consumer task
        return self.frame.get_clone()

    def get_frame_picture(self, width=1920):
        """ get picture frame from provider (this instance) """
        # wait for sync
        self.sync_event.wait()
        # restart the consumer task
        return self.frame.get_picture(width)

    def terminate_thread(self):
        """ stop running this thread, called when main thread terminates """
        self.keep_running = False
        pass # try again


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
