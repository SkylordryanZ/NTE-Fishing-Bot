import pydirectinput
import pyautogui
import time
from config import *

class InputSimulator:
    def __init__(self):
        # Fail-safe: Move mouse to corner to stop
        pyautogui.FAILSAFE = True
        # Remove artificial delays for faster response in mini-game
        pydirectinput.PAUSE = 0

    def press_f(self):
        print("Pressing F")
        pydirectinput.keyDown(KEY_F)
        time.sleep(0.1)
        pydirectinput.keyUp(KEY_F)

    def press_r(self):
        print("Pressing R (Open Shop)")
        pydirectinput.keyDown(KEY_R)
        time.sleep(0.1)
        pydirectinput.keyUp(KEY_R)

    def press_esc(self):
        print("Pressing ESC")
        pydirectinput.keyDown(KEY_ESC)
        time.sleep(0.1)
        pydirectinput.keyUp(KEY_ESC)

    def press_q(self):
        print("Pressing Q (Open Inventory)")
        pydirectinput.keyDown(KEY_Q)
        time.sleep(0.1)
        pydirectinput.keyUp(KEY_Q)

    def pull_left(self, duration):
        pydirectinput.keyDown(KEY_A)
        time.sleep(duration)
        pydirectinput.keyUp(KEY_A)

    def pull_right(self, duration):
        pydirectinput.keyDown(KEY_D)
        time.sleep(duration)
        pydirectinput.keyUp(KEY_D)

    def hold_left(self):
        pydirectinput.keyDown(KEY_A)
        pydirectinput.keyUp(KEY_D)

    def hold_right(self):
        pydirectinput.keyDown(KEY_D)
        pydirectinput.keyUp(KEY_A)

    def release_all(self):
        pydirectinput.keyUp(KEY_A)
        pydirectinput.keyUp(KEY_D)
        pydirectinput.keyUp(KEY_F)

    def click_at(self, x, y):
        print(f"Clicking at {x}, {y}")
        pydirectinput.click(x, y)

    def click_center(self):
        # Click center of screen to dismiss result
        print("Clicking to dismiss screen")
        pyautogui.click(960, 540)

    def click_shop_bait(self):
        print("Clicking Bait Slot")
        pydirectinput.click(MACRO_COORD_SHOP_BAIT[0], MACRO_COORD_SHOP_BAIT[1])

    def click_shop_max(self):
        print("Clicking MAX bait")
        pydirectinput.click(MACRO_COORD_SHOP_MAX[0], MACRO_COORD_SHOP_MAX[1])

    def click_purchase(self):
        print("Clicking PURCHASE")
        pydirectinput.click(MACRO_COORD_SHOP_PURCHASE[0], MACRO_COORD_SHOP_PURCHASE[1])

    def click_shop_confirm(self):
        print("Clicking CONFIRM PURCHASE")
        pydirectinput.click(MACRO_COORD_SHOP_CONFIRM[0], MACRO_COORD_SHOP_CONFIRM[1])

    def click_shop_empty(self):
        print("Clicking Empty Area (Dismiss)")
        pydirectinput.click(MACRO_COORD_SHOP_EMPTY[0], MACRO_COORD_SHOP_EMPTY[1])

    def click_inv_tab_hold(self):
        print("Clicking Fish Hold Tab")
        pydirectinput.click(MACRO_COORD_FISH_HOLD[0], MACRO_COORD_FISH_HOLD[1])

    def click_quick_sell(self):
        print("Clicking Quick Sell")
        pydirectinput.click(MACRO_COORD_SELL_BTN[0], MACRO_COORD_SELL_BTN[1])

    def click_confirm_sell(self):
        print("Clicking Confirm Sell")
        pydirectinput.click(MACRO_COORD_CONFIRM_SELL[0], MACRO_COORD_CONFIRM_SELL[1])

    def stop_all(self):
        self.release_all()
