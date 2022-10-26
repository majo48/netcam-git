import cv2

avg = None

def motion_detector(img):
    global avg
    occupied = False
    # resize the frame, convert it to grayscale, and blur it
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (15, 15), 0)

    if avg is None:
        print("[INFO] starting background model...")
        avg = gray.copy().astype("float")

    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    # threshold the delta image, dilate the thresholded image to fill
    # in holes, then find contours on thresholded image
    thresh = cv2.threshold(frameDelta, 5, 255,
                           cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0]

    # loop over the contours
    if cnts is not None:
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < 500:
                pass
            else:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                occupied = True

    return occupied

if __name__ == '__main__':
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

            # detect motion
            occupied = motion_detector(frame)

            # Display the resulting frames
            cv2.imshow('Frame', frame)
            cv2.imshow('Background', avg)

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
