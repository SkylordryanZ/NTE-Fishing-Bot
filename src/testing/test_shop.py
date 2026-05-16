"""
test_shop.py — Verifies the full shop purchase sequence.
Run from the project root:  python src/testing/test_shop.py
Make sure you are in-game and IDLE before running.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
from input_sim import InputSimulator
from vision import Vision
from capture import ScreenCapturer
from config import *


def test_shop():
    print(">>> Shop Test starting in 3 seconds...")
    print(">>> Be in-game and IDLE.")
    time.sleep(3)

    inputs   = InputSimulator()
    vision   = Vision()
    capturer = ScreenCapturer()

    # 1. Open Shop
    inputs.press_r()
    time.sleep(2.0)

    # 2. Verify Shop is open
    img   = capturer.capture()
    state = vision.get_state(img, STATE_IDLE)
    if state != STATE_SHOP:
        print(f"  [!] Shop not detected — got: {state}. Continuing anyway...")

    # 3. Buy sequence
    inputs.click_shop_max()
    time.sleep(0.8)
    inputs.click_purchase()
    time.sleep(1.5)

    # 4. Exit
    inputs.press_esc()
    time.sleep(1.0)
    inputs.press_esc()
    print(">>> Test Complete — should be back in IDLE.")


if __name__ == "__main__":
    test_shop()
