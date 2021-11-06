from fretboard_identification import *

def get_skin(img):
    # apply the skin mask to an image, returns image with all but skin pixels blacked out

    # convert to hsv colour space
    converted = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # create and apply mask
    HSV_mask = cv2.bitwise_not(cv2.inRange(converted, (50, 0, 0), (150, 255, 255)))
    skin = cv2.bitwise_and(img, img, mask = HSV_mask)

    return skin 

def convert_binary(img):
    # convert to a binary image e.g non-black pixels to white
    skin_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (thresh, skin_white) = cv2.threshold(skin_gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return skin_white

def morphological_transform(img):
    # perform the relevant morphological transform on a binary image
    kernel = np.ones((30,30), np.uint8)
    opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    return(opening)

def find_b_intercept(x_intercept, grad, opening):
    # find the bottom hand/fret intercept
    for y in range(999,0, -1):
        x = int(x_intercept - y/grad)
        if (x > 399):
            x = 399
        elif (x < 0):
            x = 0
        if (opening[y][x] != 0):
            return y
    return (-1)

def find_t_intercept(x_intercept, grad, opening):
    # find the top hand/fret intercept
    for y in range(0,1000):
        x = int(x_intercept - y/grad)
        if (x > 399):
            x = 399
        elif (x < 0):
            x = 0
        if (opening[y][x] != 0):
            return y
    return (-1)

def get_hand_intercepts(top_strings, bot_strings, frame):

    i = 0
    top_intercepts = []
    bottom_intercepts = []
    opening = morphological_transform(convert_binary(get_skin(frame)))
    for string in bot_strings:
        dy = 1000
        dx = string - top_strings[i]
        grad = dy/dx
        i += 1
        top_intercepts.append(find_t_intercept(string, grad, opening))
        bottom_intercepts.append(find_b_intercept(string, grad, opening))

    intercepts = zip(top_intercepts, bottom_intercepts)

    return intercepts