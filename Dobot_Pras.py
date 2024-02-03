import threading
import DobotDllType as dType
import cv2
import numpy as np
from ctypes import *
import time, platform
import tkinter.messagebox
from tkinter import *
import imutils
import math
import random

CON_STR = {
    dType.DobotConnect.DobotConnect_NoError: "DobotConnect_NoError",
    dType.DobotConnect.DobotConnect_NotFound: "DobotConnect_NotFound",
    dType.DobotConnect.DobotConnect_Occupied: "DobotConnect_Occupied"}

# Load Dll
api = dType.load()

# Connect Dobot
state = dType.ConnectDobot(api, "", 115200)[0]
print("Connect status:", CON_STR[state])

if (state == dType.DobotConnect.DobotConnect_NoError):
    # Clean Command Queued
    dType.SetQueuedCmdClear(api)

    # Async Motion Params Setting
    dType.SetHOMEParams(api, 250, 0, 50, 0, isQueued=1)
    dType.SetPTPJointParams(api, 200, 200, 200, 200, 200, 200, 200, 200, isQueued=1)
    dType.SetPTPCommonParams(api, 100, 100, isQueued=1)

# open camera
camera = cv2.VideoCapture(0)
if (camera.isOpened()):
    print('camera Open!')
else:
    print('Fail to open!')

width = 7
height = 6
length = 15
visionPoints = np.mat(np.zeros((3, 3)))
dobotPoints = np.mat(np.zeros((3, 3)))
RT = np.mat(np.zeros((3, 3)))
Inv = np.mat(np.zeros((3, 3)))


def calibration(corners):
    visionPoints[0, 0] = corners[0, 0, 0]
    visionPoints[1, 0] = corners[0, 0, 1]
    visionPoints[2, 0] = 1

    visionPoints[0, 1] = corners[width - 1, 0, 0]
    visionPoints[1, 1] = corners[width - 1, 0, 1]
    visionPoints[2, 1] = 1

    visionPoints[0, 2] = corners[width * height - 1, 0, 0]
    visionPoints[1, 2] = corners[width * height - 1, 0, 1]
    visionPoints[2, 2] = 1

    mat = dobotPoints * visionPoints.I
    RT[0, 0] = mat[0, 0]
    RT[1, 0] = mat[1, 0]
    RT[2, 0] = mat[2, 0]
    RT[0, 1] = mat[0, 1]
    RT[1, 1] = mat[1, 1]
    RT[2, 1] = mat[2, 1]
    RT[0, 2] = mat[0, 2]
    RT[1, 2] = mat[1, 2]
    RT[2, 2] = mat[2, 2]


def transform(imgX, imgY):
    transformXY = []
    mat1 = np.mat(np.zeros((3, 1)))
    mat1[0, 0] = int(imgX)
    mat1[1, 0] = int(imgY)
    mat1[2, 0] = 1

    mat2 = RT * mat1
    transformXY.append(mat2[0, 0])
    transformXY.append(mat2[1, 0])
    return transformXY


# class Counter:
#     def __init__(self): #sets count to zero when first initialized
#         self.count = 0
#     def increase(self):
#         self.count += 1 #function to increase the count by one

class ShapeDetector:
    global shape

    def __init__(self):
        pass

    def detect(self, c):
        # initialize the shape name and approximate the contour
        shape = "unidentified"
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        # if the shape is a triangle, it will have 3 vertices
        if len(approx) == 3:
            shape = 'triangle'  # Triangle

        # if the shape has 4 vertices, it is either a square or
        # a rectangle
        elif len(approx) == 4:
            # compute the bounding box of the contour and use the
            # bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            ar = w / float(h)

            # a square will have an aspect ratio that is approximately
            # equal to one, otherwise, the shape is a rectangle
            shape = 'square'  # square

        # if the shape is a pentagon, it will have 5 vertices
        elif len(approx) == 5:
            shape = "pentagon"

        # otherwise, we assume the shape is a circle
        else:
            shape = 'circle'  # Circle

        # return the name of the shape
        return shape


theBoard = {'7': ' ', '4': ' ', '1': ' ',
            '8': ' ', '5': ' ', '2': ' ',
            '9': ' ', '6': ' ', '3': ' '}

corner = ["1", "3", "7", "9"]
between = ["2", "4", "5", "6", "8"]
move = " "

board_keys = []

for key in theBoard:
    board_keys.append(key)


def printBoard(board):
    print(board['7'] + '|' + board['4'] + '|' + board['1'])
    print('-+-+-')
    print(board['8'] + '|' + board['5'] + '|' + board['2'])
    print('-+-+-')
    print(board['9'] + '|' + board['6'] + '|' + board['3'])


##def game(count):
##    print("\nThis is the computer's move. \n")
##    move = random.choice(corner)
##    theBoard[move] = turn
##
##    count += 1
##    print(count)
##
##    if count != 1 and count <= 5:
##        if theBoard['7'] == theBoard['1'] == 'X' and theBoard['4'] == ' ':
##            move = "4"
##            theBoard[move] = turn
##
##        elif theBoard['1'] == theBoard['3'] == 'X' and theBoard['2'] == ' ':
##            move = "2"
##            theBoard[move] = turn
##
##        elif theBoard['3'] == theBoard['9'] == 'X' and theBoard['6'] == ' ':
##            move = "6"
##            theBoard[move] = turn
##
##        elif theBoard['9'] == theBoard['7'] == 'X' and theBoard['8'] == ' ':
##            move = "8"
##            theBoard[move] = turn
##
##        elif theBoard['7'] == theBoard['3'] == 'X' and theBoard['5'] == ' ':
##            move = "5"
##            theBoard[move] = turn
##
##        elif theBoard['1'] == theBoard['9'] == 'X' and theBoard['5'] == ' ':
##            move = "5"
##            theBoard[move] = turn
##
##        else:
##            move = random.choice(corner)
##            theBoard[move] = turn
##
##            count += 1
##
##
##    elif count > 5:
##        if theBoard['7'] == theBoard['1'] == theBoard['3'] == 'X':
##            if theBoard['6'] == ' ' and theBoard['8'] == ' ':
##                between.remove("6")
##                between.remove("8")
##            elif theBoard['6'] == ' ':
##                between.remove("6")
##            elif theBoard['8'] == ' ':
##                between.remove("8")
##            move = random.choice(between)
##
##
##        elif theBoard['1'] == theBoard['3'] == theBoard['9'] == 'X':
##            if theBoard['4'] == ' ' and theBoard['8'] == ' ':
##                between.remove("4")
##                between.remove("8")
##            elif theBoard['4'] == ' ':
##                between.remove("4")
##            elif theBoard['8'] == ' ':
##                between.remove("8")
##            move = random.choice(between)
##
##
##        elif theBoard['3'] == theBoard['9'] == theBoard['7'] == 'X':
##            if theBoard['2'] == ' ' and theBoard['4'] == ' ':
##                between.remove("2")
##                between.remove("4")
##            elif theBoard['2'] == ' ':
##                between.remove("2")
##            elif theBoard['4'] == ' ':
##                between.remove("4")
##            move = random.choice(between)
##
##
##        elif theBoard['9'] == theBoard['7'] == theBoard['1'] == 'X':
##            if theBoard['2'] == ' ' and theBoard['6'] == ' ':
##                between.remove("2")
##                between.remove("6")
##            elif theBoard['2'] == ' ':
##                between.remove("2")
##            elif theBoard['6'] == ' ':
##                between.remove("6")
##            move = random.choice(between)
##
##
##        theBoard[move] = turn
##
##        count += 1
##
##    if count >= 5:
##        if theBoard['1'] == theBoard['2'] == theBoard['3'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['4'] == theBoard['5'] == theBoard['6'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['7'] == theBoard['8'] == theBoard['9'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['1'] == theBoard['4'] == theBoard['7'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['2'] == theBoard['5'] == theBoard['8'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['3'] == theBoard['6'] == theBoard['9'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['1'] == theBoard['5'] == theBoard['9'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. ****\n")
##
##        elif theBoard['3'] == theBoard['5'] == theBoard['7'] != ' ':
##            printBoard(theBoard)
##            print("\nGame Over.\n")
##            print(" **** " +turn + " won. **** \n")
##
##
##    if count == 9:
##        print("\nGame Over.\n")
##        print("It's a Tie!! \n")
##
##    return move


def find_coordinate(img, count):
    global shape
    transforms = []  # This is a list that gets the x,y values
    shapeIndx = []  # The shape index will give us the global shape string
    coords = []
    coordinate = []
    CX = []
    CY = []
    out = []
    pokemon = []

    resized = imutils.resize(img, width=300)
    ratio = img.shape[0] / float(resized.shape[0])

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    sd = ShapeDetector()

    cv2.line(img, (510, 0), (510, 477), (255, 0, 0), 3)
    # img_board = img[:, :510]
    #cv2.imshow("image2", img_board)
    # img_outboard = img[:, 510:]
    #cv2.imshow("image", img_outboard)

    


    for i, c in enumerate(cnts):
        # compute the center of the contour, then detect the name of the
        # shape using only the contour
        M = cv2.moments(c)
        cX = float((M["m10"] / M["m00"]) * ratio)
        cY = float((M["m01"] / M["m00"]) * ratio)
        shape = sd.detect(c)
        transforms.append((cX, cY))  # Append the cx, cy values to the tranform list
        shapeIndx.append(shape)  # append the shape to shapeIndx

        # print("Object type and Coordinates: ")
        # print('object ',i, ': ', shape, ", ", cX, cY)

        cv2.circle(img, (int(cX), int(cY)), 10, (0, 0, 255), 10, -1)
        list = transform(cX, cY)
        list[0] = cX
        list[1] = cY

        # multiply the contour (x, y)-coordinates by the resize ratio,
        # then draw the contours and the name of the shape on the image
        c = c.astype("float")
        c *= ratio
        c = c.astype("int")
        cv2.drawContours(img, [c], -1, (0, 255, 0), 2)
        cv2.putText(img, (shape + str(i)), (int(cX), int(cY)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        ##out board    
        if shape != '':
            if cX > 500 and shape == 'square':
                out.append((cX, cY))

                ##In board

            if cX < 500: 

                CX = cX / 100
                CY = cY / 100
                coords.append((cX, cY, i, shape))
                coordinate.append((math.floor(CX), math.floor(CY), i, shape))
        else:
            return
        

    cv2.imshow("DobotRun", img)
    out.sort()
    

    # cv2.imwrite('img'+str(i)+'.jpg', img)
    cv2.waitKey(0)


    # print(coords)

    coordinate.sort()
    turn = ' '

    if coordinate[0][3] == "square":
        turn = 'X'
        theBoard['1'] = turn
        if "1" in corner:
            corner.remove("1")
    elif coordinate[0][3] == "circle":
        turn = 'O'
        theBoard['1'] = turn
        if "1" in corner:
            corner.remove("1")

    if coordinate[1][3] == "square":
        turn = 'X'
        theBoard['2'] = turn
        if "2" in between:
            between.remove("2")
    elif coordinate[1][3] == "circle":
        turn = 'O'
        theBoard['2'] = turn
        if "2" in between:
            between.remove("2")

    if coordinate[2][3] == "square":
        turn = 'X'
        theBoard['3'] = turn
        if "3" in corner:
            corner.remove("3")
    elif coordinate[2][3] == "circle":
        turn = 'O'
        theBoard['3'] = turn
        if "3" in corner:
            corner.remove("3")

    if coordinate[3][3] == "square":
        turn = 'X'
        theBoard['4'] = turn
        if "4" in between:
            between.remove("4")
    elif coordinate[3][3] == "circle":
        turn = 'O'
        theBoard['4'] = turn
        if "4" in between:
            between.remove("4")

    if coordinate[4][3] == "square":
        turn = 'X'
        theBoard['5'] = turn
        if "5" in between:
            between.remove("5")
    elif coordinate[4][3] == "circle":
        turn = 'O'
        theBoard['5'] = turn
        if "5" in between:
            between.remove("5")

    if coordinate[5][3] == "square":
        turn = 'X'
        theBoard['6'] = turn
        if "6" in between:
            between.remove("6")
    elif coordinate[5][3] == "circle":
        turn = 'O'
        theBoard['6'] = turn
        if "6" in between:
            between.remove("6")

    if coordinate[6][3] == "square":
        turn = 'X'
        theBoard['7'] = turn
        if "7" in corner:
            corner.remove("7")
    elif coordinate[6][3] == "circle":
        turn = 'O'
        theBoard['7'] = turn
        if "7" in corner:
            corner.remove("7")

    if coordinate[7][3] == "square":
        turn = 'X'
        theBoard['8'] = turn
        if "8" in between:
            between.remove("8")
    elif coordinate[7][3] == "circle":
        turn = 'O'
        theBoard['8'] = turn
        if "8" in between:
            between.remove("8")

    if coordinate[8][3] == "square":
        turn = 'X'
        theBoard['9'] = turn
        if "9" in corner:
            corner.remove("9")
    elif coordinate[8][3] == "circle":
        turn = 'O'
        theBoard['9'] = turn
        if "9" in corner:
            corner.remove("9")



    coor = []
    pokemon2 = []

    c1 = []
    c2 = []
    c3 = []
    c4 = []
    c5 = []
    c6 = []
    c7 = []
    c8 = []
    c9 = []

    a1 = []
    a2 = []
    a3 = []
    a4 = []
    a5 = []



    i = 0
    j = 0

    if coordinate[i][2] == coords[j][2]:
        c1 = (coords[j][0], coords[j][1])
    elif coordinate[i][2] == coords[j + 1][2]:
        c1 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i][2] == coords[j + 2][2]:
        c1 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i][2] == coords[j + 3][2]:
        c1 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i][2] == coords[j + 4][2]:
        c1 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i][2] == coords[j + 5][2]:
        c1 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i][2] == coords[j + 6][2]:
        c1 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i][2] == coords[j + 7][2]:
        c1 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c1 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 1][2] == coords[j][2]:
        c2 = (coords[j][0], coords[j][1])
    elif coordinate[i + 1][2] == coords[j + 1][2]:
        c2 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 1][2] == coords[j + 2][2]:
        c2 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 1][2] == coords[j + 3][2]:
        c2 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 1][2] == coords[j + 4][2]:
        c2 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 1][2] == coords[j + 5][2]:
        c2 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 1][2] == coords[j + 6][2]:
        c2 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 1][2] == coords[j + 7][2]:
        c2 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c2 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 2][2] == coords[j][2]:
        c3 = (coords[j][0], coords[j][1])
    elif coordinate[i + 2][2] == coords[j + 1][2]:
        c3 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 2][2] == coords[j + 2][2]:
        c3 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 2][2] == coords[j + 3][2]:
        c3 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 2][2] == coords[j + 4][2]:
        c3 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 2][2] == coords[j + 5][2]:
        c3 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 2][2] == coords[j + 6][2]:
        c3 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 2][2] == coords[j + 7][2]:
        c3 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c3 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 3][2] == coords[j][2]:
        c4 = (coords[j][0], coords[j][1])
    elif coordinate[i + 3][2] == coords[j + 1][2]:
        c4 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 3][2] == coords[j + 2][2]:
        c4 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 3][2] == coords[j + 3][2]:
        c4 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 3][2] == coords[j + 4][2]:
        c4 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 3][2] == coords[j + 5][2]:
        c4 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 3][2] == coords[j + 6][2]:
        c4 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 3][2] == coords[j + 7][2]:
        c4 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c4 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 4][2] == coords[j][2]:
        c5 = (coords[j][0], coords[j][1])
    elif coordinate[i + 4][2] == coords[j + 1][2]:
        c5 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 4][2] == coords[j + 2][2]:
        c5 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 4][2] == coords[j + 3][2]:
        c5 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 4][2] == coords[j + 4][2]:
        c5 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 4][2] == coords[j + 5][2]:
        c5 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 4][2] == coords[j + 6][2]:
        c5 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 4][2] == coords[j + 7][2]:
        c5 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c5 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 5][2] == coords[j][2]:
        c6 = (coords[j][0], coords[j][1])
    elif coordinate[i + 5][2] == coords[j + 1][2]:
        c6 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 5][2] == coords[j + 2][2]:
        c6 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 5][2] == coords[j + 3][2]:
        c6 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 5][2] == coords[j + 4][2]:
        c6 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 5][2] == coords[j + 5][2]:
        c6 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 5][2] == coords[j + 6][2]:
        c6 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 5][2] == coords[j + 7][2]:
        c6 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c6 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 6][2] == coords[j][2]:
        c7 = (coords[j][0], coords[j][1])
    elif coordinate[i + 6][2] == coords[j + 1][2]:
        c7 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 6][2] == coords[j + 2][2]:
        c7 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 6][2] == coords[j + 3][2]:
        c7 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 6][2] == coords[j + 4][2]:
        c7 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 6][2] == coords[j + 5][2]:
        c7 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 6][2] == coords[j + 6][2]:
        c7 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 6][2] == coords[j + 7][2]:
        c7 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c7 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 7][2] == coords[j][2]:
        c8 = (coords[j][0], coords[j][1])
    elif coordinate[i + 7][2] == coords[j + 1][2]:
        c8 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 7][2] == coords[j + 2][2]:
        c8 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 7][2] == coords[j + 3][2]:
        c8 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 7][2] == coords[j + 4][2]:
        c8 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 7][2] == coords[j + 5][2]:
        c8 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 7][2] == coords[j + 6][2]:
        c8 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 7][2] == coords[j + 7][2]:
        c8 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c8 = (coords[j + 8][0], coords[j + 8][1])

    if coordinate[i + 8][2] == coords[j][2]:
        c9 = (coords[j][0], coords[j][1])
    elif coordinate[i + 8][2] == coords[j + 1][2]:
        c9 = (coords[j + 1][0], coords[j + 1][1])
    elif coordinate[i + 8][2] == coords[j + 2][2]:
        c9 = (coords[j + 2][0], coords[j + 2][1])
    elif coordinate[i + 8][2] == coords[j + 3][2]:
        c9 = (coords[j + 3][0], coords[j + 3][1])
    elif coordinate[i + 8][2] == coords[j + 4][2]:
        c9 = (coords[j + 4][0], coords[j + 4][1])
    elif coordinate[i + 8][2] == coords[j + 5][2]:
        c9 = (coords[j + 5][0], coords[j + 5][1])
    elif coordinate[i + 8][2] == coords[j + 6][2]:
        c9 = (coords[j + 6][0], coords[j + 6][1])
    elif coordinate[i + 8][2] == coords[j + 7][2]:
        c9 = (coords[j + 7][0], coords[j + 7][1])
    else:
        c9 = (coords[j + 8][0], coords[j + 8][1])

    a1 = (out[0][0], out[0][1])
    a2 = (out[1][0], out[1][1])
    a3 = (out[2][0], out[2][1])
    a4 = (out[3][0], out[3][1])
    a5 = (out[4][0], out[4][1])



    ## Putting the coordinates to their own unique variable

    coor.append(c1)
    coor.append(c2)
    coor.append(c3)
    coor.append(c4)
    coor.append(c5)
    coor.append(c6)
    coor.append(c7)
    coor.append(c8)
    coor.append(c9)

    ##Out board cordinates
    pokemon2.append(a1)
    pokemon2.append(a2)
    pokemon2.append(a3)
    pokemon2.append(a4)
    pokemon2.append(a5)
    

    ## We put each triangle coordinates into a transform function to make it compatible with the dobot arm

    CC1 = transform(c1[0], c1[1])
    CC2 = transform(c2[0], c2[1])
    CC3 = transform(c3[0], c3[1])
    CC4 = transform(c4[0], c4[1])
    CC5 = transform(c5[0], c5[1])
    CC6 = transform(c6[0], c6[1])
    CC7 = transform(c7[0], c7[1])
    CC8 = transform(c8[0], c8[1])
    CC9 = transform(c9[0], c9[1])

    AA1 = transform(a1[0], a1[1])
    AA2 = transform(a2[0], a2[1])
    AA3 = transform(a3[0], a3[1])
    AA4 = transform(a4[0], a4[1])
    AA5 = transform(a5[0], a5[1])


    newCoords = []
    newCoords.append(CC1)
    newCoords.append(CC2)
    newCoords.append(CC3)
    newCoords.append(CC4)
    newCoords.append(CC5)
    newCoords.append(CC6)
    newCoords.append(CC7)
    newCoords.append(CC8)
    newCoords.append(CC9)


    #Transformed out board cordinates
    sqaure_outside = []
    sqaure_outside.append(AA1)
    sqaure_outside.append(AA2)
    sqaure_outside.append(AA3)
    sqaure_outside.append(AA4)
    sqaure_outside.append(AA5)
    sqaure_outside.sort()

    print("\nThis is the computer's move. \n")

    ##Algorithm

    if count != 1 and count <= 3:

        if theBoard['1'] == theBoard['3'] == 'X' and theBoard['2'] == theBoard['5'] != ' ':
            move = "8"
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['7'] == 'X' and theBoard['4'] == theBoard['5'] != ' ':
            move = "6"
            theBoard[move] = turn

        elif theBoard['7'] == theBoard['9'] == 'X' and theBoard['5'] == theBoard['8'] != ' ':
            move = "2"
            theBoard[move] = turn

        elif theBoard['3'] == theBoard['9'] == 'X' and theBoard['5'] == theBoard['6'] != ' ':
            move = "4"
            theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == 'X' and theBoard['5'] == theBoard['2'] != ' ':
            move = "8"
            theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == 'X' and theBoard['4'] == theBoard['5'] != ' ':
            move = "6"
            theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == 'X' and theBoard['5'] == theBoard['6'] != ' ':
            move = "4"
            theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == 'X' and theBoard['5'] == theBoard['8'] != ' ':
            move = "2"
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['9'] == 'X' and theBoard['5'] == theBoard['8'] != ' ':
            move = "2"
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['9'] == 'X' and theBoard['5'] == theBoard['2'] != ' ':
            move = "8"
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['9'] == 'X' and theBoard['5'] == theBoard['6'] != ' ':
            move = "4"
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['9'] == 'X' and theBoard['5'] == theBoard['4'] != ' ':
            move = "6"
            theBoard[move] = turn

        elif theBoard['7'] == theBoard['1'] == 'X' and theBoard['4'] == ' ':
            move = "4"
            theBoard[move] = turn
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['1'] == theBoard['3'] == 'X' and theBoard['2'] == ' ':
            move = "2"
            theBoard[move] = turn
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['3'] == theBoard['9'] == 'X' and theBoard['6'] == ' ':
            move = "6"
            theBoard[move] = turn
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['9'] == theBoard['7'] == 'X' and theBoard['8'] == ' ':
            move = "8"
            theBoard[move] = turn
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['7'] == theBoard['3'] == 'X' and theBoard['5'] == ' ':
            move = "5"
            theBoard[move] = turn
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['1'] == theBoard['9'] == 'X' and theBoard['5'] == ' ':
            move = "5"
            theBoard[move] = turn
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        else:
            turn = 'X'
            move = random.choice(corner)
            theBoard[move] = turn

    elif count == 4:

        if theBoard['7'] == theBoard['1'] == theBoard['3'] == 'X':
            if theBoard['6'] == ' ' and theBoard['8'] == ' ':
                between.remove("6")
                between.remove("8")
            elif theBoard['6'] == ' ':
                between.remove("6")
            elif theBoard['8'] == ' ':
                between.remove("8")
            turn = 'X'
            move = random.choice(between)
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['3'] == theBoard['9'] == 'X':
            if theBoard['4'] == ' ' and theBoard['8'] == ' ':
                between.remove("4")
                between.remove("8")
            elif theBoard['4'] == ' ':
                between.remove("4")
            elif theBoard['8'] == ' ':
                between.remove("8")
            turn = 'X'
            move = random.choice(between)
            theBoard[move] = turn

        elif theBoard['3'] == theBoard['9'] == theBoard['7'] == 'X':
            if theBoard['2'] == ' ' and theBoard['4'] == ' ':
                between.remove("2")
                between.remove("4")
            elif theBoard['2'] == ' ':
                between.remove("2")
            elif theBoard['4'] == ' ':
                between.remove("4")
            turn = 'X'
            move = random.choice(between)
            theBoard[move] = turn

        elif theBoard['9'] == theBoard['7'] == theBoard['1'] == 'X':
            if theBoard['2'] == ' ' and theBoard['6'] == ' ':
                between.remove("2")
                between.remove("6")
            elif theBoard['2'] == ' ':
                between.remove("2")
            elif theBoard['6'] == ' ':
                between.remove("6")
            turn = 'X'
            move = random.choice(between)
            theBoard[move] = turn

        elif theBoard['1'] == theBoard['3'] == theBoard['8'] == 'X':
            if theBoard['4'] == ' ' and theBoard['6'] != ' ':
                move = "4"
                theBoard[move] = turn

            elif theBoard['4'] != ' ' and theBoard['6'] != ' ':
                move = "6"
                theBoard[move] = turn

            elif theBoard['4'] == ' ' and theBoard['6'] == ' ':
                turn = 'X'
                move = random.choice(corner)
                theBoard[move] = turn

        elif theBoard['1'] == theBoard['7'] == theBoard['6'] == 'X':
            if theBoard['2'] == ' ' and theBoard['8'] != ' ':
                move = "2"
                theBoard[move] = turn

            elif theBoard['2'] != ' ' and theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn

            elif theBoard['2'] == ' ' and theBoard['8'] == ' ':
                turn = 'X'
                move = random.choice(corner)
                theBoard[move] = turn

        elif theBoard['7'] == theBoard['9'] == theBoard['2'] == 'X':
            if theBoard['4'] == ' ' and theBoard['6'] != ' ':
                move = "4"
                theBoard[move] = turn

            elif theBoard['4'] != ' ' and theBoard['6'] == ' ':
                move = "6"
                theBoard[move] = turn

            elif theBoard['4'] == ' ' and theBoard['6'] == ' ':
                turn = 'X'
                move = random.choice(corner)
                theBoard[move] = turn

        elif theBoard['3'] == theBoard['9'] == theBoard['4'] == 'X':
            if theBoard['2'] == ' ' and theBoard['8'] != ' ':
                move = "2"
                theBoard[move] = turn

            elif theBoard['2'] != ' ' and theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn

            elif theBoard['2'] == ' ' and theBoard['8'] == ' ':
                turn = 'X'
                move = random.choice(corner)
                theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == theBoard['8'] == 'X':
            if theBoard['9'] == ' ':
                move = "9"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            elif theBoard['9'] != ' ':
                move = "1"
                theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == theBoard['6'] == 'X':
            if theBoard['2'] == ' ' and theBoard['8'] != ' ':
                move = "2"
                theBoard[move] = turn

            elif theBoard['2'] != ' ' and theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn

            elif theBoard['2'] == ' ' and theBoard['8'] == ' ':
                turn = 'X'
                move = random.choice(corner)
                theBoard[move] = turn

        elif theBoard['3'] == theBoard['4'] == theBoard['7'] == 'X':
            if theBoard['2'] == ' ' and theBoard['8'] != ' ':
                move = "2"
                theBoard[move] = turn

            elif theBoard['2'] != ' ' and theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn

            elif theBoard['2'] == ' ' and theBoard['8'] == ' ':
                turn = 'X'
                move = random.choice(corner)
                theBoard[move] = turn

        elif theBoard['3'] == theBoard['7'] == theBoard['2'] == 'X':
            if theBoard['1'] == ' ':
                move = "1"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            elif theBoard['9'] != ' ':
                move = "9"
                theBoard[move] = turn

        elif theBoard['1'] == theBoard['2'] == theBoard['9'] == 'X':
            if theBoard['3'] == ' ':
                move = "3"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            elif theBoard['3'] != ' ':
                move = "7"
                theBoard[move] = turn

        elif theBoard['1'] == theBoard['8'] == theBoard['9'] == 'X':
            if theBoard['7'] == ' ':
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            elif theBoard['7'] != ' ':
                move = "3"
                theBoard[move] = turn

        elif theBoard['1'] == theBoard['4'] == theBoard['9'] == 'X':
            if theBoard['7'] == ' ':
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            elif theBoard['7'] != ' ':
                move = "3"
                theBoard[move] = turn

        elif theBoard['1'] == theBoard['6'] == theBoard['9'] == 'X':
            if theBoard['3'] == ' ':
                move = "3"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            elif theBoard['3'] != ' ':
                move = "7"
                theBoard[move] = turn

    elif count == 5:

        if theBoard['1'] == theBoard['3'] == theBoard['4'] == theBoard['8'] == 'X':
            if theBoard['7'] == ' ':
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "9"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['6'] == theBoard['8'] == 'X':
            if theBoard['9'] == ' ':
                move = "9"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['8'] == theBoard['9'] == 'X':
            if theBoard['6'] == ' ':
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['7'] == theBoard['8'] == 'X':
            if theBoard['4'] == ' ':
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['6'] == theBoard['7'] == theBoard['8'] == 'X':
            if theBoard['9'] == ' ':
                move = "9"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "3"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['2'] == theBoard['6'] == theBoard['7'] == 'X':
            if theBoard['3'] == ' ':
                move = "3"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "9"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['6'] == theBoard['7'] == 'X':
            if theBoard['2'] == ' ':
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['6'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['2'] == theBoard['4'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['1'] == ' ':
                move = "1"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "3"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['2'] == theBoard['6'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['3'] == ' ':
                move = "3"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "1"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['2'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['4'] == ' ':
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['2'] == theBoard['3'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['6'] == ' ':
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['3'] == theBoard['4'] == theBoard['8'] == theBoard['9'] == 'X':
            if theBoard['7'] == ' ':
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "1"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['2'] == theBoard['3'] == theBoard['4'] == theBoard['9'] == 'X':
            if theBoard['1'] == ' ':
                move = "1"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['3'] == theBoard['4'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['7'] == ' ':
                move = "7"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['4'] == theBoard['9'] == 'X':
            if theBoard['2'] == ' ':
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['7'] == theBoard['8'] == 'X':
            if theBoard['4'] == ' ':
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['6'] == theBoard['7'] == 'X':
            if theBoard['2'] == ' ':
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['3'] == theBoard['4'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['2'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['4'] == ' ':
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['2'] == theBoard['3'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['6'] == ' ':
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['7'] == theBoard['8'] == 'X':
            if theBoard['6'] == ' ':
                move = "6"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "4"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['3'] == theBoard['4'] == theBoard['9'] == 'X':
            if theBoard['2'] == ' ':
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

        elif theBoard['1'] == theBoard['6'] == theBoard['7'] == theBoard['9'] == 'X':
            if theBoard['8'] == ' ':
                move = "8"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print(" **** " + turn + " won. ****\n")

            else:
                move = "2"
                theBoard[move] = turn
                printBoard(theBoard)
                print("\nGame Over.\n")
                print("It's a Tie!! \n")

    elif count == 1:
        turn = 'X'
        move = random.choice(corner)
        theBoard[move] = turn

# Moving to specific coordinates based on the computer's input
# Taking values of Square_outside
    if value == 1:

        x_temp=sqaure_outside[count-1][0]
        y_temp=sqaure_outside[count-1][1]
        
        current_pose = dType.GetPose(api)
        dType.SetPTPCmdEx(api, 0, (x_temp),  -y_temp,  (-45), 0, 1)
        current_pose = dType.GetPose(api)
        dType.SetPTPCmdEx(api, 2, (x_temp), -y_temp, 50, 0, 1)
        dType.SetEndEffectorSuctionCupEx(api, 1, 1)
        current_pose = dType.GetPose(api)

        if move == "1":
            print(" Turn ", count, ",", " going to ", CC1)
            dType.SetPTPCmdEx(api, 0, CC1[0], CC1[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC1[0], CC1[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "2":
            print("Turn ", count, " going to ", CC2)
            dType.SetPTPCmdEx(api, 0, CC2[0], CC2[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC2[0], CC2[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "3":
            print("Turn ", count, " going to ", CC3)
            dType.SetPTPCmdEx(api, 0, CC3[0], CC3[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC3[0], CC3[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "4":
            print("Turn ", count, " going to ", CC4)
            dType.SetPTPCmdEx(api, 0, CC4[0], CC4[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC4[0], CC4[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "5":
            print("Turn ", count, " going to ", CC5)
            dType.SetPTPCmdEx(api, 0, CC5[0], CC5[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC5[0], CC5[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 160, (0), (0), 0, 1)

        elif move == "6":
            print("Turn ", count, " going to ", CC6)
            dType.SetPTPCmdEx(api, 0, CC6[0], CC6[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC6[0], CC6[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "7":
            print("Turn ", count, " going to ", CC7)
            dType.SetPTPCmdEx(api, 0, CC7[0], CC7[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC7[0], CC7[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "8":
            print("Turn ", count, " going to ", CC8)
            dType.SetPTPCmdEx(api, 0, CC8[0], CC8[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC8[0], CC8[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        elif move == "9":
            print("Turn ", count, " going to ", CC9)
            dType.SetPTPCmdEx(api, 0, CC9[0], CC9[1], 50, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, CC9[0], CC9[1], (-35), 0, 1)
            dType.SetEndEffectorSuctionCupEx(api, 0, 1)
            current_pose = dType.GetPose(api)
            dType.SetPTPCmdEx(api, 0, 161, (0), (0), 0, 1)

        else:
            print("ERRORR!!!!")

    print("count: ", count)

    if count >= 3:
        if theBoard['1'] == theBoard['2'] == theBoard['3'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['4'] == theBoard['5'] == theBoard['6'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['7'] == theBoard['8'] == theBoard['9'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['1'] == theBoard['4'] == theBoard['7'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['2'] == theBoard['5'] == theBoard['8'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['3'] == theBoard['6'] == theBoard['9'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['1'] == theBoard['5'] == theBoard['9'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. ****\n")

        elif theBoard['3'] == theBoard['5'] == theBoard['7'] != ' ':
            printBoard(theBoard)
            print("\nGame Over.\n")
            print(" **** " + turn + " won. **** \n")

    if count == 9:
        print("\nGame Over.\n")
        print("It's a Tie!! \n")


# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6 * 7, 3), np.float32)
objp[:, :2] = np.mgrid[0:7, 0:6].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.

turn = 'X'
count = 1
value = 0

while True:
    grabbed, img = camera.read()  # Video stream by frame by frame
    # x,y = find_coordinate(img)
    if not grabbed:
        break
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # convert grey image

    cv2.imshow('lwpCVWindow', gray)  # Display the captured video stream
    key = cv2.waitKey(1) & 0xFF
    if key == ord('c'):
        cornerCount = 0
        ret, corners = cv2.findChessboardCorners(gray, (7, 6), None)
        if ret == True:
            objpoints.append
            (objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            # Draw and display the cornes

            # red Point
            cv2.circle(img, (corners2[0, 0, 0], corners2[0, 0, 1]), 10, (0, 0, 255), -1)
            # green Point
            cv2.circle(img, (corners2[width - 1, 0, 0], corners2[width - 1, 0, 1]), 10, (0, 255, 0), -1)
            # bluePoint
            cv2.circle(img, (corners2[width * height - 1, 0, 0], corners2[width * height - 1, 0, 1]), 10, (255, 0, 0),
                       -1)

            img = cv2.drawChessboardCorners(img, (7, 6), corners2, ret)
            cv2.imshow('matWindow', img)
            cv2.waitKey(500)

            tkinter.messagebox.askokcancel("VisionDemo", 'Please move the Dobot to the red spot by teaching key!')
            dType.GetPose(api)
            dobotPoints[0, 0] = dType.GetPose(api)[0]
            dobotPoints[1, 0] = dType.GetPose(api)[1]
            dobotPoints[2, 0] = 1

            tkinter.messagebox.askokcancel("VisionDemo", 'Please move the Dobot to the green spot by teaching key!')
            dType.GetPose(api)
            dobotPoints[0, 1] = dType.GetPose(api)[0]
            dobotPoints[1, 1] = dType.GetPose(api)[1]
            dobotPoints[2, 1] = 1

            tkinter.messagebox.askokcancel("VisionDemo", 'Please move the Dobot to the blue spot by teaching key!')
            dType.GetPose(api)
            dobotPoints[0, 2] = dType.GetPose(api)[0]
            dobotPoints[1, 2] = dType.GetPose(api)[1]
            dobotPoints[2, 2] = 1

            calibration(corners)
            cv2.destroyWindow('matWindow')

    if key == ord("s"):
        value = 1

        cv2.destroyWindow('lwpCVWindow')

        dType.SetQueuedCmdStartExec(api)
        grabbed, img = camera.read()

        cv2.namedWindow('DobotRun')

        find_coordinate(img, count)

        count += 1
        dType.SetQueuedCmdStopExec(api)

        printBoard(theBoard)

    if key == ord('q'):
        # Disconnect Dobot
        dType.DisconnectDobot(api)
        cv2.destroyAllWindows()
        break