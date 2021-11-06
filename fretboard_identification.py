import numpy as np
import cv2
from matplotlib import pyplot as plt

def perspective_transform(frame, pts1, pts2):
    # Perform perspective transform on input frame, cropping to input points
    length_pix = 1000
    width_pix = 400

    matrix = cv2.getPerspectiveTransform(pts1, pts2) 
    result = cv2.warpPerspective(frame, matrix, (width_pix, length_pix)) 

    return result

def find_frets(cap, frame):
    # Uses Canny and Hough to find the location of the strings and frets

    frame = get_img(cap,frame)

    # Canny edge detection
    edged = cv2.Canny(frame, 250, 600)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    # Hough lines, giving strings. Also calculate median gradient for later
    thresh = 550

    string_lines = cv2.HoughLines(edged, 1, np.pi/180.0, thresh)

    while(string_lines is None or string_lines.size/2.0 < 6): 
        thresh -= 25
     #   print(thresh)
        if (thresh <= 0):
            raise Exception('Image unsatisfactory')
        string_lines = cv2.HoughLines(edged, 1, np.pi/180.0, thresh)

    height, width, channels = frame.shape

    gradients = np.zeros(int(string_lines.size/2))
    i = 0 

    for line in string_lines:
        rho, theta = line[0]
        # convert from polar to cartesian and plot line
        a = np.cos(theta)
        b = np.sin(theta)
        gradients[i] = a/b
        i = i + 1

    median = np.median(gradients)
    perp_median = -1/median 

    # Find x intercept for clustering of strings
    intercepts = np.zeros(int(string_lines.size/2.0))
    i = 0

    for line in string_lines:
        rho, theta = line[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        length_to_intercept =  (1080 - y0)/a
        x_intercept = int(x0 + length_to_intercept*(-b))
        intercepts[i] = x_intercept
        i = i+1


    intercepts = np.float32(intercepts)
    intercepts.sort()

    #Perform clustering
    flags = cv2.KMEANS_PP_CENTERS
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    compactness, labels, string_centers = cv2.kmeans(intercepts, 6, None, criteria = criteria, attempts = 10, flags = flags)

    # Store as new lines
    string_lines = []

    for centre in string_centers: 
        x0 = int(centre[0])
        y0 = 1080
        y_intercept = y0 + median*x0 # use negative of median as grad because plot techincally 'upside-down'
        x1 = 1750
        y1 = int(-median*x1 + y_intercept) 

        line = (y_intercept, median) # line in form of y intercept, gradient
        string_lines.append((line))

    # Perform hough with angle filter for frets
    fret_lines = cv2.HoughLines(edged, 1, np.pi/180.0, 100,  min_theta = 5*np.pi/8, max_theta = 7*np.pi/8)
    thresh = 90
    while(fret_lines is None or fret_lines.size/2.0 < 2): 
        thresh -= 5
        fret_lines = cv2.HoughLines(edged, 1, np.pi/180.0, thresh,  min_theta = 5*np.pi/8, max_theta = 7*np.pi/8)

    # Identify top line
    min_y = np.Infinity

    for line in fret_lines:
        rho, theta = line[0]

        # convert from polar to cartesian
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        
        if(y0 < min_y):
            min_line = line[0]
            min_y = y0

    rho, theta = min_line

    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a*rho
    y0 = b*rho

    # Get top line's intercepts with strings
    intercepts1 = []

    for line in string_lines:
        c1, m1 = line

        # Get y = mx+c form
        m2 = a/b
        c2 = y0 + m2*x0

        # Get intersection
        x_intercept = (c1 - c2)/(m1 - m2)
        y_intercept = -m1 * x_intercept + c1

        intercepts1.append((x_intercept, y_intercept))

    # Find bottom line and repeat
    fret_lines = cv2.HoughLines(edged, 1, np.pi/180.0, 130, min_theta =  11*np.pi/16, max_theta = 13*np.pi/16)
    
    while(fret_lines is None or fret_lines.size/2.0 < 2): 
        thresh -= 5
        fret_lines = cv2.HoughLines(edged, 1, np.pi/180.0, thresh,  min_theta = 5*np.pi/8, max_theta = 7*np.pi/8)

    max_y = -np.Infinity

    for line in fret_lines:
        rho, theta = line[0]

        # convert from polar to cartesian and plot line
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho

        if(y0 > max_y):
            max_line = line[0]
            max_y = y0

    rho, theta = max_line

    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a*rho
    y0 = b*rho

    intercepts2 = []

    for line in string_lines:
        c1, m1 = line

        # Get y = mx+c form
        m2 = a/b
        c2 = y0 + m2*x0

        # Get intersection
        x_intercept = (c1 - c2)/(m1 - m2)
        y_intercept = -m1 * x_intercept + c1
        
        intercepts2.append((x_intercept, y_intercept))

    # Perspective transform
    length_pix = 1000
    width_pix = 400

    intercepts1.sort()
    intercepts2.sort()

    transform_pts1 = np.float32([intercepts1[0], intercepts1[5], intercepts2[0], intercepts2[5]]) 
    transform_pts2 = np.float32([[0, 0], [width_pix, 0], [0, length_pix], [width_pix, length_pix]]) 
        
    result = perspective_transform(frame, transform_pts1, transform_pts2)

    # Calculating fret positions
    ppi = length_pix/17.3
    L = 26
    frets = np.zeros(20)

    for i in range(0, 19):
        frets[i+1] = (frets[i] + (L-frets[i])/17.817)

    frets = frets*ppi

    # Now need to find strings in this perspective
    edged_transform = cv2.Canny(result, 50, 80)
    edged_transform = cv2.dilate(edged_transform, None, iterations=1)
    edged_transform = cv2.erode(edged_transform, None, iterations=1)

    string_lines = cv2.HoughLines(edged_transform, 1, np.pi/180.0, 300, min_theta= 15*np.pi/16, max_theta= 17*np.pi/16 )
    
    while(string_lines is None or string_lines.size/2.0 < 6): 
        thresh -= 25
        string_lines = cv2.HoughLines(edged, 1, np.pi/180.0, thresh)

    bot_intercepts = np.zeros(int(string_lines.size/2.0), dtype= np.float32)
    i = 0

    for line in string_lines:
        rho, theta = line[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        length_to_intercept =  (length_pix - y0)/a
        x_intercept = int(x0 + length_to_intercept*(-b))
        bot_intercepts[i] = x_intercept
        i = i+1

    top_intercepts = np.zeros(int(string_lines.size/2.0), dtype= np.float32)
    i = 0

    for line in string_lines:
        rho, theta = line[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        length_to_intercept =  (y0)/a
        x_intercept = int(x0 + length_to_intercept*(-b))
        top_intercepts[i] = x_intercept
        i = i+1

    result_copy = result.copy()

    intercepts = np.float32(intercepts)
    flags = cv2.KMEANS_PP_CENTERS
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)

    compactness, labels, top_string_centers = cv2.kmeans(top_intercepts, 6, None, criteria = criteria, attempts = 10, flags = flags)

    compactness, labels, bot_string_centers = cv2.kmeans(bot_intercepts, 6, None, criteria = criteria, attempts = 10, flags = flags)

    bot_string_centers1 = np.zeros(6)
    top_string_centers1 = np.zeros(6)

    i=0
    for centre in bot_string_centers:
        bot_string_centers1[i] = bot_string_centers[i][0]
        i = i+1
    i=0
    for centre in top_string_centers:
        top_string_centers1[i] = top_string_centers[i][0]
        i = i+1

    top_string_centers1.sort()
    bot_string_centers1.sort()

    strings = zip(top_string_centers1, bot_string_centers1)


    return(frets, strings, transform_pts1, transform_pts2)

def get_img(cap, frame_num):
    # return image at frame frame_num
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    
    return frame