import math
import time
import pyautogui
from src.config import *


class BlinkDetector:
    def __init__(self):
        # Tracking closure start time and frame counts
        self.closed_start_time = None
        self.closed_frames = 0

        self.last_left_click = 0
        self.last_right_click = 0
        self.last_blink_time = 0

        self.drag_mode = False
        
        # Initial default threshold τ = 0.21 (Report §4.5 & Figure 2)
        self.blink_threshold = DEFAULT_EAR_THRESHOLD

    def set_threshold(self, threshold):
        self.blink_threshold = threshold

    def distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def ear(self, eye):
        horizontal = self.distance(eye[0], eye[3])
        v1 = self.distance(eye[1], eye[5])
        v2 = self.distance(eye[2], eye[4])

        if horizontal == 0:
            return 0.0

        return (v1 + v2) / (2.0 * horizontal)

    def release_drag(self):
        """Fail-safe release of mouse-down state on stop or face loss (Report §5.3.1)."""
        if self.drag_mode:
            try:
                pyautogui.mouseUp()
            except Exception:
                pass
            self.drag_mode = False
            self.closed_start_time = None
            self.closed_frames = 0

    def update(self, left_eye, right_eye):
        left_ear = self.ear(left_eye)
        right_ear = self.ear(right_eye)

        # Dual-eye symmetry validation (Report Table 4: mitigates involuntary squints / laughter)
        eye_asymmetry = abs(left_ear - right_ear)
        is_symmetric = eye_asymmetry <= MAX_EYE_ASYMMETRY

        avg_ear = (left_ear + right_ear) / 2.0
        now = time.time()
        action = None

        # Eyes are closed if EAR drops below threshold and passes symmetry check
        if avg_ear < self.blink_threshold and is_symmetric:
            if self.closed_start_time is None:
                self.closed_start_time = now
            self.closed_frames += 1

            closure_duration = now - self.closed_start_time

            # Drag Mode Toggle: EAR < τ (> 600 ms) per Report Figure 2
            if closure_duration >= DRAG_HOLD_TIME:
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
                    # Reset so drag doesn't immediately re-toggle in the same continuous hold
                    self.closed_start_time = now
                    self.closed_frames = 0

        else:
            # Eyes reopened — evaluate completed blink gesture if eyes were closed
            if self.closed_start_time is not None:
                closure_duration = now - self.closed_start_time

                # Single / Double Click: EAR < τ (100 - 300 ms) per Report Figure 2
                if SINGLE_CLICK_MIN_TIME <= closure_duration <= SINGLE_CLICK_MAX_TIME:
                    # Double Click: 2 bursts within 400 ms per Report Figure 2
                    if (now - self.last_blink_time) <= DOUBLE_WINDOW:
                        pyautogui.doubleClick()
                        action = "DOUBLE CLICK"
                        self.last_blink_time = 0  # Consume the burst
                    else:
                        if now - self.last_left_click > LEFT_COOLDOWN:
                            pyautogui.click()
                            action = "LEFT CLICK"
                            self.last_left_click = now
                        self.last_blink_time = now

                self.closed_start_time = None
                self.closed_frames = 0

        return avg_ear, action
