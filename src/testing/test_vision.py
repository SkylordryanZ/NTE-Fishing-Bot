"""
test_vision.py — Live state detection tester.
Run from the project root:  python src/testing/test_vision.py
Shows what state the bot currently detects on your screen, updated every second.
Press Ctrl+C to stop.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import cv2
from capture import ScreenCapturer
from vision import Vision
from config import STATE_IDLE


def test_vision():
    print(">>> Vision Test — showing detected state every second.")
    print(">>> Press Ctrl+C to stop.\n")

    capturer = ScreenCapturer()
    vision   = Vision()

    last_state = STATE_IDLE
    while True:
        img   = capturer.capture()
        state = vision.get_state(img, last_state)

        if state != last_state:
            print(f"  State changed: {last_state} → {state}")
            last_state = state

            # Save the frame that triggered the state change
            folder = os.path.join("debug_images")
            os.makedirs(folder, exist_ok=True)
            ts = int(time.time())
            cv2.imwrite(os.path.join(folder, f"transition_{last_state}_{ts}.png"), img)
            print(f"  Frame saved to debug_images/")
        else:
            print(f"  Current state: {state}", end="\r")

        time.sleep(1.0)


if __name__ == "__main__":
    test_vision()
