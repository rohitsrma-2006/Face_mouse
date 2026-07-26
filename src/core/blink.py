import math
import time
import pyautogui
from src.config import *


class BlinkDetector:
    def __init__(self):
        self.closed_frames = 0

        self.last_left_click = 0
        self.last_right_click = 0
        self.last_blink_time = 0

        self.drag_mode = False
        
        # This will be overridden by calibration
        self.blink_threshold = 0.22

    def set_threshold(self, threshold):
        self.blink_threshold = threshold

    def distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def ear(self, eye):
        horizontal = self.distance(eye[0], eye[3])
        v1 = self.distance(eye[1], eye[5])
        v2 = self.distance(eye[2], eye[4])

        if horizontal == 0:
            return 0

        return (v1 + v2) / (2.0 * horizontal)

    def update(self, left_eye, right_eye):
        left_ear = self.ear(left_eye)
        right_ear = self.ear(right_eye)

        avg_ear = (left_ear + right_ear) / 2.0

        now = time.time()
        action = None

        if avg_ear < self.blink_threshold:
            self.closed_frames += 1

            # Long blink = drag toggle
            if self.closed_frames >= HOLD_BLINK_FRAMES:
                if now - self.last_right_click > RIGHT_COOLDOWN:

                    if not self.drag_mode:
                        pyautogui.mouseDown()
                        self.drag_mode = True
                        action = "DRAG ON"
                    else:
                        pyautogui.mouseUp()
                        self.drag_mode = False
                        action = "DRAG OFF"

                    self.last_right_click = now
                    self.closed_frames = 0

        else:
            # Eyes reopened
            if QUICK_BLINK_FRAMES <= self.closed_frames < HOLD_BLINK_FRAMES:

                # Double blink
                if now - self.last_blink_time < DOUBLE_WINDOW:
                    pyautogui.doubleClick()
                    action = "DOUBLE CLICK"

                else:
                    if now - self.last_left_click > LEFT_COOLDOWN:
                        pyautogui.click()
                        action = "LEFT CLICK"
                        self.last_left_click = now

                self.last_blink_time = now

            self.closed_frames = 0

        return avg_ear, action