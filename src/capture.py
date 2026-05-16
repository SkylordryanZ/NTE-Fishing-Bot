import mss
import numpy as np
import cv2
import ctypes
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MONITOR_INDEX

# Enable DPI awareness to get the true physical resolution on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class ScreenCapturer:
    def __init__(self):
        self.sct = mss.mss()
        if MONITOR_INDEX == 0:
            self.select_monitor_by_click()
        elif MONITOR_INDEX >= len(self.sct.monitors):
            print(f"Error: Monitor index {MONITOR_INDEX} out of range. Defaulting to 1.")
            self.monitor = self.sct.monitors[1]
            print(f"Targeting Monitor 1: {self.monitor['width']}x{self.monitor['height']} at ({self.monitor['left']}, {self.monitor['top']})")
        else:
            self.monitor = self.sct.monitors[MONITOR_INDEX]
            print(f"Targeting Monitor {MONITOR_INDEX}: {self.monitor['width']}x{self.monitor['height']} at ({self.monitor['left']}, {self.monitor['top']})")

    def select_monitor_by_click(self):
        import time
        import os
        import re
        
        print("\n" + "="*50)
        print("  MONITOR SETUP")
        print("  Please CLICK anywhere on the monitor where the game is running...")
        print("="*50 + "\n")
        
        # wait for left click release (debounce)
        while ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
            time.sleep(0.01)
        
        while True:
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                
                selected_idx = 1
                for i, mon in enumerate(self.sct.monitors):
                    if i == 0: continue
                    if mon["left"] <= pt.x < mon["left"] + mon["width"]:
                        if mon["top"] <= pt.y < mon["top"] + mon["height"]:
                            selected_idx = i
                            break
                
                print(f">>> Selected Monitor {selected_idx} ({self.sct.monitors[selected_idx]['width']}x{self.sct.monitors[selected_idx]['height']})!")
                self.monitor = self.sct.monitors[selected_idx]
                
                # Update config.py so it remembers
                try:
                    config_path = os.path.join(os.path.dirname(__file__), "config.py")
                    with open(config_path, "r") as f:
                        content = f.read()
                    content = re.sub(r"MONITOR_INDEX\s*=\s*\d+", f"MONITOR_INDEX = {selected_idx}", content)
                    with open(config_path, "w") as f:
                        f.write(content)
                    print(">>> Monitor saved to config.py for next time.")
                except Exception as e:
                    print(f"Could not save monitor to config: {e}")
                
                # Debounce the click before continuing
                while ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                    time.sleep(0.01)
                break
            time.sleep(0.01)

    def capture(self, region=None):
        """
        Captures a region of the screen.
        region: [y_start, y_end, x_start, x_end] or None for full screen
        """
        if region:
            monitor_region = {
                "top": self.monitor["top"] + region[0],
                "left": self.monitor["left"] + region[2],
                "width": region[3] - region[2],
                "height": region[1] - region[0]
            }
            screenshot = self.sct.grab(monitor_region)
        else:
            screenshot = self.sct.grab(self.monitor)
            
        # Convert to numpy array and BGR format for OpenCV
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

if __name__ == "__main__":
    capturer = ScreenCapturer()
    img = capturer.capture()
    cv2.imwrite("full_capture_test.png", img)
    print("Test capture saved to full_capture_test.png")
