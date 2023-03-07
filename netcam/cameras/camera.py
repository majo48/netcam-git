# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import cv2
import os
import threading
import logging
import time

# constants
MAX_SKIPPED = 30 # [30] skipped frames
WAIT_LONG = 30 # [30] seconds

class Camera(threading.Thread):
    """ class for one physical video cameras """

    def __init__(self, idx, ipaddr, rtsp_url, frm):
        """
        initialize connection to one physical video camera
        """
        threading.Thread.__init__(self)
        self.idx = idx # thread index
        self.ipaddr = ipaddr # ip address of the IP camera
        self.rtsp_url = rtsp_url # url of the external camera or webcam index
        if isinstance(ipaddr, str) and len(ipaddr) == 1:
            self.ipaddr = int(ipaddr) # this is a local webcam
        self.frame = frm # static class: netcam-git.netcam.cameras.frame.Frame
        self.skipped = 0 # skipped frame count
        self.sync_event = threading.Event()
        self.sync_event.clear() # not set
        self.keep_running = True # maintain video streaming from this camera

    def _ping_camera(self, ipaddr):
        """
        Send a ping to the network camera
        :return: True is active, False is not connected
        """
        if isinstance(ipaddr, str):
            # IP camera
            response = os.system("ping -c 1 " + ipaddr + " > /dev/null 2>&1")
            return response == 0
        elif isinstance(ipaddr, int):
            # local webcam (for testing)
            return True # always OK

    def _sleep(self, secs):
        """ sleep for a number of seconds """
        cnt = secs
        while self.keep_running and cnt!=0:
            time.sleep(1)
            cnt -= 1
        pass

    def run(self):
        """
        open/connect video stream from one physical video camera
        """
        while self.keep_running:
            if not self._ping_camera(self.ipaddr):
                # cannot connect to camera, ping failed
                logging.warning(">>> Start video stream, cannot connect to camera "+str(self.idx)+" ("+self.ipaddr+")")
                self.set_connection_problem()
                time.sleep(1)
            else:
                logging.info(">>> Started video stream in " + threading.currentThread().getName())
                stream = cv2.VideoCapture(self.rtsp_url)
                self.skipped = 0 # reset skip counter
                while self.keep_running:
                    try:
                        success, frm = stream.read() # read one frame
                    except cv2.error:
                        logging.warning('<<< Connection problem (cv2).')
                        break

                    if (success == False) or (frm is None):
                        self.skipped += 1
                        if self.has_connection_problem():
                            logging.warning('<<< Connection problem(too many empty frames).')
                            break
                    else:
                        self.skipped = 0 # reset skip counter
                        self.frame.set_frame(frm) # pass frame to a thread safe container
                        self.sync_event.set() # unblock waiting consumer threads
                        self.sync_event.clear() # block subsequent waits

                cv2.destroyAllWindows()
                stream.release()
                logging.info("<<< Stopped video stream in " + threading.currentThread().getName())
                if self.keep_running:
                    self._sleep(WAIT_LONG)  # delay, before trying again

    def get_frame_count(self):
        """ get the frame count """
        return self.frame.get_frame_count()

    def get_skipped_count(self):
        """ get the number of frames skipped """
        return self.skipped

    def get_fps(self):
        """ get approx. frames per second """
        return self.frame.get_fps()

    def get_frame_clone(self):
        """
        called from external function
        get cloned frame from provider (this instance)
        :returns clone, counter
        """
        # wait for sync here
        self.sync_event.wait()
        # restarted the consumer task
        return self.frame.get_clone()

    def has_connection_problem(self):
        """ has a connection problem been detected? """
        return self.skipped >= MAX_SKIPPED

    def set_connection_problem(self):
        """ set the var(s) for connection problem(s) """
        self.skipped = MAX_SKIPPED
        pass

    def terminate_thread(self):
        """ stop running this thread, called when main thread terminates """
        self.keep_running = False
        pass


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
