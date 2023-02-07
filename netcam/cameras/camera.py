# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os
import threading
import logging
import time


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
        self.skipped = 0 # skipped frame count
        self.sync_event = threading.Event()
        self.sync_event.clear() # not set
        self.keep_running = True # maintain video streaming from this camera

    def run(self):
        """
        open/connect video stream from one physical video camera
        """
        while self.keep_running:
            try:
                thread = threading.currentThread()
                stream = cv2.VideoCapture(self.rtsp_url)
                logging.info(">>> Started video stream in thread '" + thread.name)
                # loop through all frames provided by the camera stream
                while self.keep_running:
                    # get one frame from camera
                    success, frm = stream.read()
                    # check frame
                    if (frm is None) or (success == False):
                        self.skipped += 1
                        if self.skipped > 10:
                            raise Exception('Connection problem(s), restart video stream after a delay.')
                        else:
                            continue # skip the frame
                    self.skipped = 0
                    # pass frame to a thread safe container and start consumer threads
                    self.frame.set_frame(frm)
                    self.sync_event.set() # consumer threads: '1' motion detector, '0, 1, many' web clients

                logging.info("<<< Stopped video stream in thread '" + thread.name)
                cv2.destroyAllWindows()
                stream.release()
            except BaseException as err:
                logging.error(str(err))
                time.sleep(30)  # delay, before trying again
            finally:
                pass

    def get_frame_count(self):
        """ get the frame count """
        return self.frame.get_frame_count()

    def get_fps(self):
        """ get approx. frames per second """
        return self.frame.get_fps()

    def get_frame_clone(self):
        """
        called from external function
        get cloned frame from provider (this instance)
        """
        # wait for sync here
        self.sync_event.wait()
        # restarted the consumer task
        return self.frame.get_clone()

    def get_frame_picture(self, width=1920):
        """
        called from external function
        get picture frame from provider (this instance)
        """
        # wait for sync here
        self.sync_event.wait()
        # restarted the consumer task
        return self.frame.get_picture(width)

    def terminate_thread(self):
        """ stop running this thread, called when main thread terminates """
        self.keep_running = False
        pass


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
