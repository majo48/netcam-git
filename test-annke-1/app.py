# simple test for the proper rtsp_url for the ANNKE AN-I91BL0102 bullet camera
# this file lacks error handling, e.g. camera not running etc.

import os
import cv2
import imutils
from imutils.video import VideoStream
import config

rtsp_url = "rtsp://<user>:<password>@<ip>:554/H264/ch1/main/av_stream"
# replace url credentials from the .env file (see python-dotenv package)
config = config.Config()
rtsp_url = rtsp_url.replace('<user>', config.get_username())
rtsp_url = rtsp_url.replace('<password>', config.get_password())
rtsp_url = rtsp_url.replace('<ip>', config.get_ip_adresse_list()[0])

vs = VideoStream(rtsp_url).start()

while True:
    frame = vs.read()
    if frame is None:
        continue # add error handling here

    frame = imutils.resize(frame, width=1200)
    cv2.imshow('ANNKE/CN#1', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()
vs.stop()
