import pyautogui
import ctypes

class MouseController:
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()

        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False

    def move_relative(self, dx, dy):
        try:
            # Check position to trigger failsafe if needed (pyautogui features)
            pyautogui.position()
            
            # Use native Windows ctypes for zero-latency, buttery smooth movement
            # 0x0001 is MOUSEEVENTF_MOVE
            # It naturally stops at screen borders without throwing errors
            ctypes.windll.user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)

        except pyautogui.FailSafeException:
            pass