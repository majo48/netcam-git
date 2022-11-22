# this is the third of 'learning by doing' packages
# Reference: https://towardsdatascience.com/image-analysis-for-beginners-creating-a-motion-detector-with-opencv-4ca6faba4b42
# upgrade from version 2: added some statistics to file names (fps, pixels)

import cv2
import motions

def run():
    # List of video clips for testing
    vidObjNames = [
        '../clips/vtest.avi',
        '../clips/autostrasse.mp4',
        '../clips/garageausfahrt.mp4',
        '../clips/parking-lot1.mp4',
        '../clips/parking-lot2.mp4',
    ]
    vidObj = None
    motObj = None

    for vidObjName in vidObjNames:

        # Create the VideoCapture object and read from input file or stream
        vidObj = cv2.VideoCapture(vidObjName)

        # statistics
        fps = vidObj.get(cv2.CAP_PROP_FPS)
        w = vidObj.get(3)  # float `width`
        h = vidObj.get(4)  # float `height`
        print('Processing file: ' + vidObjName+' ,'+str(int(fps))+' fps, '+str(int(w))+'x'+str(int(h))+' pixels.')

        # Check if camera opened successfully
        if (vidObj.isOpened() == False):
            print("Error opening video stream or file: "+vidObjName)
            break

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
        pass # end while

        # When everything done, release the video capture object +++
        if vidObj is not None: vidObj.release()
        if motObj is not None: del motObj
    pass # end for

    # Closes all the frames
    cv2.destroyAllWindows()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
