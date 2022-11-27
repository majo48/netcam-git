# this is the fourth of 'learning by doing' packages
# Reference: http://jacarini.dinf.usherbrooke.ca/dataset2012
# upgrade from version 3: uses dataset2012 instead of video clips

import cv2
import motions
import videocapture

def run():
    # List of input files for testing
    vidObjNames = [
        '../dataset2012/dataset/intermittentObjectMotion/abandonedBox/input/in000001.jpg',
        '../dataset2012/dataset/dynamicBackground/canoe/input/in000001.jpg',
        '../dataset2012/dataset/dynamicBackground/boats/input/in000001.jpg',
        '../dataset2012/dataset/baseline/highway/input/in000001.jpg',
        '../dataset2012/dataset/baseline/office/input/in000001.jpg',
        '../dataset2012/dataset/baseline/pedestrians/input/in000001.jpg',
        '../dataset2012/dataset/baseline/PETS2006/input/in000001.jpg',
    ]
    vidObj = None
    motObj = None

    for vidObjName in vidObjNames:

        # Create the VideoCapture object and read from input file or stream
        vidObj = videocapture.VideoCapture(vidObjName)

        # Check if camera opened successfully
        if (vidObj.isOpened() == False):
            print("Error opening video stream or file: "+vidObjName)
            break
        else:
            print("Opening file "+vidObjName+" "+vidObj.get_statistics())

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
        if vidObj is not None: del vidObj
        if motObj is not None: del motObj
    pass # end for

    # Closes all the frames
    cv2.destroyAllWindows()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
