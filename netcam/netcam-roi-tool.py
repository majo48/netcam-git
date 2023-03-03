# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

# Tool for defining one ROI (region of interest) within a camera view.
#
# Call this tool with: # python3 netcam-roi-tool.py <index>
# where <index> is: 0, 1, 2, 3, etc.
# in other words: the camera index as defined in the file cameras/config.py

import numpy as np
import cv2

#image_path
image_path= '/Users/mart/desktop/carolina.jpg'
image = cv2.imread(image_path)

# Select ROI:
# 1. select picture titelbar
# 2. press left mouse button
# 3. drag mouse pointer and release left mouse button
# 4. ROI is displayed as blue box
# 5. enter 'enter' to print result
# 6. enter 'c' to close
r = cv2.selectROI("select the area", image, showCrosshair=False)
print(r)
print('x1: '+str(r[0])+', y1: '+str(r[1])+', x2: '+str(r[2])+', y2: '+str(r[3]))

# Crop image
cropped_image = image[int(r[1]):int(r[1] + r[3]),
                int(r[0]):int(r[0] + r[2])]

# Display cropped image
cv2.imshow("Cropped image", cropped_image)
cv2.waitKey(0)
