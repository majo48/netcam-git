# this is the second of 'learning by doing' packages
# Reference: https://towardsdatascience.com/image-analysis-for-beginners-creating-a-motion-detector-with-opencv-4ca6faba4b42

import cv2
import numpy as np
from shared import motions

def run():
    # Create the VideoCapture object and read from input file or stream
    # If the input is the camera, pass 0 instead of the video file name
    vidObj = cv2.VideoCapture('../clips/vtest.avi')
    # vidObj = cv2.VideoCapture(0) # access macbook camera works too

    # Check if camera opened successfully
    if (vidObj.isOpened() == False):
        print("Error opening video stream or file")

    # Initialize the motions object
    motObj = motions.Motions(vidObj)

    # Read until video is completed
    while (vidObj.isOpened()):
        # Capture frame-by-frame
        ret, frame = vidObj.read()
        if ret == True:
            # Parse the resulting frame
            motionDetected, frame = motObj.parse_frame(frame)
            # Display the resulting frame
            cv2.imshow('Frame', frame)
            # Select video frame, then press Q on keyboard to exit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        # End of video stream or file, break the loop
        else:
            break

    # When everything done, release the video capture object +++
    vidObj.release()
    del motObj

    # Closes all the frames
    cv2.destroyAllWindows()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
