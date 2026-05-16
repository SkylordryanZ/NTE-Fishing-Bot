"""
test_sell.py — Verifies the full inventory sell sequence.
Run from the project root:  python src/testing/test_sell.py
Make sure you are in-game and IDLE before running.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
from input_sim import InputSimulator
from vision import Vision
from capture import ScreenCapturer
from config import *


def test_sell():
    print(">>> Sell Test starting in 3 seconds...")
    print(">>> Be in-game and IDLE.")
    time.sleep(3)

    inputs   = InputSimulator()
    vision   = Vision()
    capturer = ScreenCapturer()

    # 1. Open Inventory
    inputs.press_q()
    time.sleep(2.0)

    # 2. Sell Sequence
    time.sleep(1.5)
    inputs.click_inv_tab_hold()
    time.sleep(1.5)
    inputs.click_quick_sell()
    time.sleep(1.5)
    inputs.click_confirm_sell()
    time.sleep(2.0)

    # 3. Dismiss Sold Screen
    inputs.click_center()
    time.sleep(1.0)
    inputs.press_esc()

    print(">>> Test Complete — should be back in IDLE.")


if __name__ == "__main__":
    test_sell()
