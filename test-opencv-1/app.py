# this is the first of 'learning by doing' packages
# Reference: https://learnopencv.com/read-write-and-display-a-video-using-opencv-cpp-python/

import cv2
import numpy as np

def run():
    # Create a VideoCapture object and read from input file
    # If the input is the camera, pass 0 instead of the video file name
    vidObj = cv2.VideoCapture('../clips/vtest.avi')
    # vidObj = cv2.VideoCapture(0) # access macbook camera works too

    # Check if camera opened successfully
    if (vidObj.isOpened() == False):
        print("Error opening video stream or file")

    # Read until video is completed
    while (vidObj.isOpened()):
        # Capture frame-by-frame
        ret, frame = vidObj.read()
        if ret == True:

            # Display the resulting frameq
            cv2.imshow('Frame', frame)

            # Select video frame, then press Q on keyboard to exit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

        # End of video stream or file, break the loop
        else:
            break

    # When everything done, release the video capture object
    vidObj.release()

    # Closes all the frames
    cv2.destroyAllWindows()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
