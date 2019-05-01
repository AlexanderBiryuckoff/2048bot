import cv2
import numpy as np
import win32api, win32gui, win32ui, win32con, win32com.client
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageGrab
import pyautogui
from time import sleep

from ctypes import windll
user32 = windll.user32
user32.SetProcessDPIAware()

WINDOW_SUBSTRING = "2048 - Google Chrome"

class Board(object):
    UP, DOWN, LEFT, RIGHT = 1, 2, 3, 4

    def __init__(self, clientwindowtitle):
        self.hwnd = self.getClientWindow(clientwindowtitle)
        if not self.hwnd:
            return

        self.tiles, self.tileheight, self.contour = self.findTiles(self.get_data_from_program())
        if not self.tiles:
            return

    def get_window_info(self):  # получение координат окна
        window_info = []
        win32gui.EnumWindows(self.set_window_coordinates, window_info)
        return window_info

    def set_window_coordinates(self, hwnd, window_info):
        if win32gui.IsWindowVisible(hwnd):
            if win32gui.GetWindowText(hwnd) == WINDOW_SUBSTRING:
                rect = win32gui.GetWindowRect(hwnd)
                x = rect[0]
                y = rect[1]
                w = rect[2] - x
                h = rect[3] - y
                window_info.append(x)
                window_info.append(y)
                window_info.append(w)
                window_info.append(h)
                win32gui.SetForegroundWindow(hwnd)

    def get_screen(self, x1, y1, x2, y2):
        screen = ImageGrab.grab((x1, y1, x2, y2))
        img = np.array(screen.getdata(), dtype=np.uint8).reshape((screen.size[1], screen.size[0], 3))
        return img

    def get_data_from_program(self):
        window_info = self.get_window_info()
        x1 = window_info[0]
        y1 = window_info[1]
        self.window_coordinates = (x1, y1)
        x2 = x1 + window_info[2]
        y2 = y1 + window_info[3]
        img = self.get_screen(x1, y1, x2, y2)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        '''cv2.imshow('board',img)
        cv2.waitKey(0)
        cv2.destroyWindow( 'board' )'''
        return img

    def getClientWindow(self, windowtitle):
        toplist, winlist = [], []

        def enum_cb(hwnd, results):
            winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_cb, toplist)
        window = [(hwnd, title) for hwnd, title in winlist if windowtitle.lower() in title.lower()]
        if not len(window):
            return 0
        return window[0][0]

    def findTiles(self, cvframe):
        tiles, avgh = [], 0

        gray = cv2.cvtColor(cvframe, cv2.COLOR_BGRA2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, 1, 1, 11, 2)
        contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        def findBoard(contours):  # get largest square
            ww, sqcnt = 10, None
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w > ww and abs(w - h) < w / 10:
                    ww = w
                    sqcnt = cnt
            return sqcnt

        board = findBoard(contours)
        '''if board == None:
            print('board not found!')
            return tiles, avgh, board'''

        bx, by, bw, bh = cv2.boundingRect(board)
        self.board_coordinates = (bx, by, bw, bh)
        # cv2.rectangle(cvframe,(bx,by),(bx+bw,by+bh),(0,255,0),2)
        # cv2.imshow('board',cvframe)
        # cv2.waitKey(0)
        # cv2.destroyWindow( 'board' )
        maxh = bh / 4
        minh = (maxh * 4) / 5
        count = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if y > by and w > minh and w < maxh and h > minh and h < maxh:
                avgh += h
                count += 1
        if not count:
            print('no tile found!')
            return tiles, avgh, board

        print(bx, by, bw, bh)
        avgh = avgh // count
        margin = (bh - avgh * 4) / 5
        for row in range(4):
            for col in range(4):
                x0 = bx + avgh * col + margin * (col + 1)
                x1 = x0 + avgh
                y0 = by + avgh * row + margin * (row + 1)
                y1 = y0 + avgh
                tiles.append([int(x0), int(y0), int(x1), int(y1)])
                # cv2.rectangle(cvframe,(x0,y0),(x1,y1),(0,255,0),2)
        # cv2.imshow('tiles',cvframe)
        # cv2.waitKey(0)
        # cv2.destroyWindow( 'tiles' )
        print(tiles)
        return tiles, avgh, board

    def getTileNumbers(self, cvframe):
        numbers = []
        outframe = np.zeros(cvframe.shape, np.uint8)
        for tile in self.tiles:
            x0, y0, x1, y1 = tile
            color, color1, color2 = cvframe[y0+20, x0+50]
            cv2.rectangle(outframe, (x0, y0), (x1, y1), (int(color), int(color1), int(color2)), 2)
            number = 0 if color == 180 else \
                           2 if color == 218 else \
                           4 if color == 200 else \
                           8 if color == 121 else \
                           16 if color == 99 else \
                           32 if color == 95 else \
                           64 if color == 59 else \
                           128 if color == 114 else \
                           256 if color == 97 else \
                           512 if color == 80 else \
                           1024 if color == 63 else -color
            numbers.append(number)
            cv2.putText(outframe, str(number), (x0+20, y0+30), 0, 1, (0, 255, 0))
        print(numbers)
        return numbers, outframe

    def refresh_game(self):
        sleep(5)
        print(self.window_coordinates, self.board_coordinates)
        x = self.window_coordinates[0]+self.board_coordinates[0]+self.board_coordinates[2]//4
        y = self.window_coordinates[1]+self.board_coordinates[1]+self.board_coordinates[3]//2
        pyautogui.moveTo(x, y, 2)
        pyautogui.click()

    def getWindowHandle(self):
        return self.hwnd

    def getBoardContour(self):
        return self.contour

    def update(self):
        frame = self.get_data_from_program()
        self.tilenumbers, outframe = self.getTileNumbers(frame)
        return self.tilenumbers, frame, outframe

    def copyTileNumbers(self):
        return self.tilenumbers[:]

    def getCell(self, tiles, x, y):
        return tiles[(y * 4) + x]

    def setCell(self, tiles, x, y, v):
        tiles[(y * 4) + x] = v
        return tiles

    def getCol(self, tiles, x):
        return [self.getCell(tiles, x, i) for i in range(4)]

    def setCol(self, tiles, x, col):
        for i in range(4):
            self.setCell(tiles, x, i, col[i])
        return tiles

    def getLine(self, tiles, y):
        return [self.getCell(tiles, i, y) for i in range(4)]

    def setLine(self, tiles, y, line):
        for i in range(4):
            self.setCell(tiles, i, y, line[i])
        return tiles

    def validMove(self, tilenumbers, direction):
        if direction == self.UP or direction == self.DOWN:
            for x in range(4):
                col = self.getCol(tilenumbers, x)
                for y in range(4):
                    if (y < 4 - 1 and col[y] == col[y + 1] and col[y] != 0):
                        return True
                    if (direction == self.DOWN and y > 0 and col[y] == 0 and col[y - 1] != 0):
                        return True
                    if (direction == self.UP and y < 4 - 1 and col[y] == 0 and col[y + 1] != 0):
                        return True
        if direction == self.LEFT or direction == self.RIGHT:
            for y in range(4):
                line = self.getLine(tilenumbers, y)
                for x in range(4):
                    if (x < 4 - 1 and line[x] == line[x + 1] and line[x] != 0):
                        return True
                    if (direction == self.RIGHT and x > 0 and line[x] == 0 and line[x - 1] != 0):
                        return True
                    if (direction == self.LEFT and x < 4 - 1 and line[x] == 0 and line[x + 1] != 0):
                        return True
        return False

    def moveTileNumbers(self, tilenumbers, direction):
        def collapseline(line, direction):
            if (direction == self.LEFT or direction == self.UP):
                inc = 1
                rg = range(0, 4 - 1, inc)
            else:
                inc = -1
                rg = range(4 - 1, 0, inc)
            pts = 0
            for i in rg:
                if line[i] == 0:
                    continue
                if line[i] == line[i + inc]:
                    v = line[i] * 2
                    line[i] = v
                    line[i + inc] = 0
                    pts += v
            return line, pts

        def moveline(line, directsion):
            nl = [c for c in line if c != 0]
            if directsion == self.UP or directsion == self.LEFT:
                return nl + [0] * (4 - len(nl))
            return [0] * (4 - len(nl)) + nl

        score = 0
        if direction == self.LEFT or direction == self.RIGHT:
            for i in range(4):
                origin = self.getLine(tilenumbers, i)
                line = moveline(origin, direction)
                collapsed, pts = collapseline(line, direction)
                new = moveline(collapsed, direction)
                tilenumbers = self.setLine(tilenumbers, i, new)
                score += pts
        elif direction == self.UP or direction == self.DOWN:
            for i in range(4):
                origin = self.getCol(tilenumbers, i)
                line = moveline(origin, direction)
                collapsed, pts = collapseline(line, direction)
                new = moveline(collapsed, direction)
                tilenumbers = self.setCol(tilenumbers, i, new)
                score += pts

        return score, tilenumbers

    # AI based on "term2048-AI"


# https://github.com/Nicola17/term2048-AI
class AI(object):
    def __init__(self, board):
        self.board = board

    def nextMove(self):
        tilenumbers = self.board.tilenumbers[:]
        m, s = self.nextMoveRecur(tilenumbers[:], 5, 5)
        print(s)
        return m

    def nextMoveRecur(self, tilenumbers, depth, maxDepth, base=0.9):
        bestMove, bestScore = 0, -1
        for m in range(1, 5):
            if (self.board.validMove(tilenumbers, m)):
                score, newtiles = self.board.moveTileNumbers(tilenumbers[:], m)
                score, critical = self.evaluate(newtiles)
                newtiles = self.board.setCell(newtiles, critical[0], critical[1], 2)
                if depth != 0:
                    my_m, my_s = self.nextMoveRecur(newtiles[:], depth - 1, maxDepth)
                    score += my_s * pow(base, maxDepth - depth + 1)
                if score > bestScore:
                    bestMove = m
                    bestScore = score

        return bestMove, bestScore

    def evaluate(self, tilenumbers, commonRatio=0.25):

        maxVal = 0.
        criticalTile = (-1, -1)

        for i in range(8):
            linearWeightedVal = 0
            invert = False if i < 4 else True
            weight = 1.
            ctile = (-1, -1)

            cond = i % 4
            for y in range(4):
                for x in range(4):
                    if cond == 0:
                        b_x = 4 - 1 - x if invert else x
                        b_y = y
                    elif cond == 1:
                        b_x = x
                        b_y = 4 - 1 - y if invert else y
                    elif cond == 2:
                        b_x = 4 - 1 - x if invert else x
                        b_y = 4 - 1 - y
                    elif cond == 3:
                        b_x = 4 - 1 - x
                        b_y = 4 - 1 - y if invert else y

                    currVal = self.board.getCell(tilenumbers, b_x, b_y)
                    if currVal == 0 and ctile == (-1, -1):
                        ctile = (b_x, b_y)
                    linearWeightedVal += currVal * weight
                    weight *= commonRatio
                invert = not invert

            if linearWeightedVal > maxVal:
                maxVal = linearWeightedVal
                criticalTile = ctile

        return maxVal, criticalTile

    def solveBoard(self, moveinterval=6000):
        boardHWND = self.board.hwnd
        if not boardHWND:
            return False
        bx, by, bw, bh = cv2.boundingRect(self.board.getBoardContour())
        x0, x1, y0, y1 = bx, bx + bw, by, by + bh

        win32gui.SetForegroundWindow(boardHWND)
        shell = win32com.client.Dispatch('WScript.Shell')
        print('Set the focus to the Game Window, and the press this arrow key:')
        keymove = ['UP', 'DOWN', 'LEFT', 'RIGHT']

        delay = moveinterval // 3  # milliseconds delay to cancel board animation effect
        prev_numbers = []
        was2048 = 0
        while True:
            numbers, inframe, outframe = self.board.update()
            if 2048 in numbers and not was2048:
                self.board.refresh_game()
                was2048 = 1
            if numbers != prev_numbers:
                cv2.waitKey(delay)
                # numbers, inframe, outframe = self.board.update()
                if numbers == prev_numbers:  # recheck if has changed
                    print('!')
                    continue
                prev_numbers = numbers
                move = ai.nextMove()
                if move:
                    key = keymove[move - 1]
                    shell.SendKeys('{%s}' % key)
                    print(key)
                    cv2.waitKey(delay)
                    cv2.imshow('CV copy', inframe[y0:y1, x0:x1])
                    cv2.imshow('CV out', outframe[y0:y1, x0:x1])
            cv2.waitKey(delay)
        cv2.destroyWindow('CV copy')
        cv2.destroyWindow('CV out')


# http://gabrielecirulli.github.io/2048/
# http://ov3y.github.io/2048-AI/
board = Board("2048 - Google Chrome")
# board = Board("2048 - Mozilla Firefox")

ai = AI(board)
ai.solveBoard(450)
# board.refresh_game()

print('stopped.')
