# proof of concept
def intersect(boxA, boxB):
    """
        check if two rectangles intersect, using opencv coordinates
        e.g. top left is [0, 0], both x and y ascending (>0)
        this may return an empty area (with w * h == 0)
    """
    x = max(boxA["x"], boxB["x"])
    y = max(boxA["y"], boxB["y"])
    w = min(boxA["x"] + boxA["w"], boxB["x"] + boxB["w"]) - x
    h = min(boxA["y"] + boxA["h"], boxB["y"] + boxB["h"]) - y
    intersects = True
    if w < 0 or h < 0:
        intersects = False
    return intersects, [x, y, w, h]


# test code
if __name__ == "__main__":
    boxes = [
        {"x": 0, "y": 0, "w": 10, "h": 10, "name": "box1"},
        {"x": 5, "y": 5, "w": 10, "h": 10, "name": "box2"},
        {"x": 20, "y": 20, "w": 10, "h": 10, "name": "box3"},
        {"x": 10, "y": 10, "w": 10, "h": 10, "name": "box4"}
    ]
    for i in range(len(boxes)):
        boxA = boxes[i]
        for j in range(i+1, len(boxes)):
            boxB = boxes[j]
            intersects, rectangle = intersect(boxA, boxB)
            if intersects:
                ret = 'intersects'
            else:
                ret = 'none intersecting'
            print("Compare "+boxA["name"]+" with "+boxB["name"]+": "+ret+" "+str(rectangle))
# output [x, y, w, h]:
# Compare box1 with box2: intersects [5, 5, 5, 5]
# Compare box1 with box3: none intersecting [20, 20, -10, -10]
# Compare box1 with box4: intersects [10, 10, 0, 0]
# Compare box2 with box3: none intersecting [20, 20, -5, -5]
# Compare box2 with box4: intersects [10, 10, 5, 5]
# Compare box3 with box4: intersects [20, 20, 0, 0]