import pyautogui
import ctypes


class MouseController:
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()

        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False

    def move_relative(self, dx, dy):
        """Dispatches cursor movement with screen boundary checks and native user32 event."""
        try:
            # Query current position to enforce screen-boundary safety (Report §3.3 & §5.3.1)
            curr_x, curr_y = pyautogui.position()
            new_x = max(0, min(self.screen_w - 1, curr_x + int(dx)))
            new_y = max(0, min(self.screen_h - 1, curr_y + int(dy)))

            clamped_dx = new_x - curr_x
            clamped_dy = new_y - curr_y

            # Use native Windows ctypes for zero-latency, buttery smooth movement
            # 0x0001 is MOUSEEVENTF_MOVE
            ctypes.windll.user32.mouse_event(0x0001, int(clamped_dx), int(clamped_dy), 0, 0)

        except pyautogui.FailSafeException:
            pass
        except Exception:
            pass
