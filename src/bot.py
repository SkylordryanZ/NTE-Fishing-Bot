import time
import cv2
import ctypes
import os
from capture import ScreenCapturer
from vision import Vision
from input_sim import InputSimulator
from recorder import ScreenshotRecorder
from config import *
import importlib

def reload_config():
    """Reloads config.py dynamically and updates bot.py's global variables."""
    import config
    try:
        importlib.reload(config)
        # Update the global namespace of bot.py with the newly reloaded configuration values
        for key, val in vars(config).items():
            if not key.startswith('_'):
                globals()[key] = val
        print(">>> Configuration reloaded successfully! Changes applied instantly.")
    except Exception as e:
        print(f"!!! Error reloading configuration: {e}")

# ------------------------------------------------------------------ #
# Windows low-level key detection                                      #
# ------------------------------------------------------------------ #
def is_key_pressed(vk_code):
    return ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000

VK_1     = 0x31
VK_2     = 0x32
VK_3     = 0x33
VK_4     = 0x34
VK_5     = 0x35  # Start / Resume
VK_6     = 0x36  # Pause
VK_7     = 0x37  # Configuration
VK_8     = 0x38  # Training and data collection (DEV DEBUG)
VK_9     = 0x39  # Exit


# Manual Overrides
VK_Y   = 0x59  # IDLE
VK_U   = 0x55  # WAITING
VK_I   = 0x49  # HOOKED
VK_O   = 0x4F  # MINIGAME
VK_P   = 0x50  # CAUGHT
VK_ESC = 0x1B
VK_M   = 0x4D


# ------------------------------------------------------------------ #
# UI Helpers                                                           #
# ------------------------------------------------------------------ #
def print_main_menu():
    print("\n[CONTROLS]")
    print("  5 — Start / Resume")
    print("  6 — Pause")
    print("  7 — Configuration")
    print("      → Select Target Monitor")
    print("      → Set bait count")
    print("      → Set Auto-Sell Threshold (default: 1000)")
    print("      → Setup Macros (Auto-Sell)")
    print("      → Setup Macros (Auto-Shop)")
    print("  8 — Training and data collection (DEV DEBUG)")
    print("      → Toggle Auto-Capture ON/OFF")
    print("      → Setup Macros (Weather)")
    print("      → Toggle Data Collection Mode (Auto-Weather)")
    print("      → Test auto sell")
    print("      → Test minigame")
    print("  9 — Exit")

    print("\n[MANUAL OVERRIDES]")
    print("  Y: IDLE | U: WAITING | I: HOOKED | O: MINIGAME | P: CAUGHT")


# ------------------------------------------------------------------ #
# Shop Macro Setup                                                     #
# ------------------------------------------------------------------ #
def setup_shop_macro():
    print("\n" + "="*55)
    print("  AUTO-SHOP MACRO SETUP")
    print("="*55)
    
    def get_pos():
        while True:
            if is_key_pressed(VK_M): # M
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                time.sleep(0.5) # debounce
                return pt.x, pt.y
            time.sleep(0.01)

    coords = {}
    print("\n1. [AUTO-SHOP] Open Shop (R), hover over the Bait you want to buy and press M.")
    coords['SHOP_BAIT'] = get_pos()
    print(f"   Saved: {coords['SHOP_BAIT']}")

    print("\n2. [AUTO-SHOP] Hover over the 'MAX' or quantity slider and press M.")
    coords['SHOP_MAX'] = get_pos()
    print(f"   Saved: {coords['SHOP_MAX']}")

    print("\n3. [AUTO-SHOP] Hover over the 'Purchase' button and press M.")
    coords['SHOP_PURCHASE'] = get_pos()
    print(f"   Saved: {coords['SHOP_PURCHASE']}")

    print("\n4. [AUTO-SHOP] Hover over the 'Confirm Purchase' button (if any) and press M.")
    coords['SHOP_CONFIRM'] = get_pos()
    print(f"   Saved: {coords['SHOP_CONFIRM']}")

    print("\n5. [AUTO-SHOP] Hover over an empty area (to dismiss popups) and press M.")
    coords['SHOP_EMPTY'] = get_pos()
    print(f"   Saved: {coords['SHOP_EMPTY']}")
    
    # Save to config.py
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
        with open(config_path, "r") as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            if "MACRO_COORD_SHOP_BAIT =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_BAIT = {coords['SHOP_BAIT']}\n")
            elif "MACRO_COORD_SHOP_MAX =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_MAX = {coords['SHOP_MAX']}\n")
            elif "MACRO_COORD_SHOP_PURCHASE =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_PURCHASE = {coords['SHOP_PURCHASE']}\n")
            elif "MACRO_COORD_SHOP_EMPTY =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_EMPTY = {coords['SHOP_EMPTY']}\n")
            else:
                new_lines.append(line)
                
        with open(config_path, "w") as f:
            f.writelines(new_lines)
        print("\n>>> Shop coordinates saved to config.py!")
        reload_config()
    except Exception as e:
        print(f"Error saving shop macro coords: {e}")

# ------------------------------------------------------------------ #
# Data Collection Macro Setup                                          #
# ------------------------------------------------------------------ #
def setup_collection_macro():
    print("\n" + "="*55)
    print("  DATA COLLECTION MACRO SETUP")
    print("="*55)
    
    def get_pos():
        while True:
            if is_key_pressed(VK_M): # M
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                time.sleep(0.5) # debounce
                return pt.x, pt.y
            time.sleep(0.01)

    coords = {}
    print("\n1. Hover over the 'Time System' button and press M.")
    coords['TIME_SYSTEM'] = get_pos()
    print(f"   Saved: {coords['TIME_SYSTEM']}")
    
    print("\n2. Hover over Weather 1 (Sunny/Base) and press M.")
    coords['WEATHER_1'] = get_pos()
    print(f"   Saved: {coords['WEATHER_1']}")
    
    print("\n3. Hover over Weather 2 and press M.")
    coords['WEATHER_2'] = get_pos()
    print(f"   Saved: {coords['WEATHER_2']}")
    
    print("\n4. Hover over Weather 3 and press M.")
    coords['WEATHER_3'] = get_pos()
    print(f"   Saved: {coords['WEATHER_3']}")
    
    print("\n5. Hover over the 'Confirm' button and press M.")
    coords['CONFIRM'] = get_pos()
    print(f"   Saved: {coords['CONFIRM']}")
    
    print("\n6. Hover over the 'Start Fishing' button (the one AFTER pressing F) and press M.")
    coords['START_FISHING'] = get_pos()
    print(f"   Saved: {coords['START_FISHING']}")

    print("\n7. [AUTO-SELL] Open Inventory (Q), hover over 'Fish Hold' tab and press M.")
    coords['FISH_HOLD'] = get_pos()
    print(f"   Saved: {coords['FISH_HOLD']}")

    print("\n8. [AUTO-SELL] Hover over the 'Sell All/Quick Sell' button and press M.")
    coords['SELL_BTN'] = get_pos()
    print(f"   Saved: {coords['SELL_BTN']}")

    print("\n9. [AUTO-SELL] Hover over the 'Confirm Sale' button and press M.")
    coords['CONFIRM_SELL'] = get_pos()
    print(f"   Saved: {coords['CONFIRM_SELL']}")

    print("\n10. [AUTO-SHOP] Open Shop (R), hover over the Bait you want to buy and press M.")
    coords['SHOP_BAIT'] = get_pos()
    print(f"   Saved: {coords['SHOP_BAIT']}")

    print("\n11. [AUTO-SHOP] Hover over the 'MAX' or quantity slider and press M.")
    coords['SHOP_MAX'] = get_pos()
    print(f"   Saved: {coords['SHOP_MAX']}")

    print("\n12. [AUTO-SHOP] Hover over the 'Purchase' button and press M.")
    coords['SHOP_PURCHASE'] = get_pos()
    print(f"   Saved: {coords['SHOP_PURCHASE']}")

    print("\n13. [AUTO-SHOP] Hover over an empty area (to dismiss popups) and press M.")
    coords['SHOP_EMPTY'] = get_pos()
    print(f"   Saved: {coords['SHOP_EMPTY']}")
    
    # Save to config.py
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
        with open(config_path, "r") as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            if "MACRO_COORD_TIME_SYSTEM =" in line:
                new_lines.append(f"MACRO_COORD_TIME_SYSTEM = {coords['TIME_SYSTEM']}\n")
            elif "MACRO_COORD_WEATHER_1 =" in line:
                new_lines.append(f"MACRO_COORD_WEATHER_1 = {coords['WEATHER_1']}\n")
            elif "MACRO_COORD_WEATHER_2 =" in line:
                new_lines.append(f"MACRO_COORD_WEATHER_2 = {coords['WEATHER_2']}\n")
            elif "MACRO_COORD_WEATHER_3 =" in line:
                new_lines.append(f"MACRO_COORD_WEATHER_3 = {coords['WEATHER_3']}\n")
            elif "MACRO_COORD_CONFIRM =" in line:
                new_lines.append(f"MACRO_COORD_CONFIRM = {coords['CONFIRM']}\n")
            elif "MACRO_COORD_START_FISHING =" in line:
                new_lines.append(f"MACRO_COORD_START_FISHING = {coords['START_FISHING']}\n")
            elif "MACRO_COORD_FISH_HOLD =" in line:
                new_lines.append(f"MACRO_COORD_FISH_HOLD = {coords['FISH_HOLD']}\n")
            elif "MACRO_COORD_SELL_BTN =" in line:
                new_lines.append(f"MACRO_COORD_SELL_BTN = {coords['SELL_BTN']}\n")
            elif "MACRO_COORD_CONFIRM_SELL =" in line:
                new_lines.append(f"MACRO_COORD_CONFIRM_SELL = {coords['CONFIRM_SELL']}\n")
            elif "MACRO_COORD_SHOP_BAIT =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_BAIT = {coords['SHOP_BAIT']}\n")
            elif "MACRO_COORD_SHOP_MAX =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_MAX = {coords['SHOP_MAX']}\n")
            elif "MACRO_COORD_SHOP_PURCHASE =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_PURCHASE = {coords['SHOP_PURCHASE']}\n")
            elif "MACRO_COORD_SHOP_EMPTY =" in line:
                new_lines.append(f"MACRO_COORD_SHOP_EMPTY = {coords['SHOP_EMPTY']}\n")
            else:
                new_lines.append(line)
                
        with open(config_path, "w") as f:
            f.writelines(new_lines)
        print("\n>>> All coordinates saved to config.py!")
        reload_config()
    except Exception as e:
        print(f"Error saving macro coords: {e}")

# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #
def main():
    print("=" * 55)
    print("  NTE Fishing Bot")
    print("  1920x1080 fullscreen required")
    print("=" * 55)

    from vision import Vision
    capturer = ScreenCapturer()
    vision   = Vision()
    inputs   = InputSimulator()
    recorder = ScreenshotRecorder(capturer)

    # ---- State machine ----
    current_state         = STATE_IDLE
    last_action_time      = 0
    state_buffer          = []
    BUFFER_SIZE           = 1       # Immediate transitions
    has_pressed_f_hook    = False
    has_counted_catch     = False
    fish_caught_counter   = 0
    bait_count            = 9999
    bait_sets_to_buy      = 1
    state_entry_time      = time.time()

    # ---- Bot mode ----
    bot_active   = False
    auto_capture = False
    prev_state   = None  # Tracks the previous state for transition detection
    
    # ---- Data collection mode ----
    collection_mode_active = False
    collection_cycle_start = 0
    weather_cycle_index    = 1
    weather_coords = [MACRO_COORD_WEATHER_1, MACRO_COORD_WEATHER_2, MACRO_COORD_WEATHER_3]
    CYCLE_DURATION_SEC = 24 * 60 # 24 minutes

    print_main_menu()

    first_frame = True
    frame_counter = 0
    last_snap_time = 0
    sell_step = 0
    auto_sell_pending = False
    auto_shop_pending = False
    sell_step = 0
    shop_step = 0
    shop_loop_count = 0
    try:
        while True:
            # -------------------------------------------------------- #
            # Hotkey handling                                            #
            # -------------------------------------------------------- #
            # -------------------------------------------------------- #
            # Hotkey handling                                            #
            # -------------------------------------------------------- #
            if is_key_pressed(VK_5) and not bot_active:
                bot_active = True
                if auto_capture:
                    recorder.start()
                    recorder.set_state(current_state)
                mode_str = " [AUTO-CAPTURE]" if auto_capture else ""
                print(f">>> BOT STARTED{mode_str}")

            if is_key_pressed(VK_6) and bot_active:
                bot_active = False
                recorder.stop()
                inputs.release_all()
                print(">>> BOT PAUSED")

            if is_key_pressed(VK_9):
                print(">>> EXITING")
                break

            if is_key_pressed(VK_7):
                # CONFIGURATION SUBMENU
                bot_active = False
                recorder.stop()
                inputs.release_all()
                print("\n" + "="*40)
                print("  CONFIGURATION MENU")
                print("  1 — Select Target Monitor")
                print("  2 — Set Bait Count")
                print("  3 — Set Auto-Sell Threshold")
                print("  4 — Set Bait Sets to Buy (99 each)")
                print("  5 — Setup Macros (Auto-Sell)")
                print("  6 — Setup Macros (Auto-Shop)")
                print("  ESC — Back to Main Menu")
                print("="*40)
                
                while True:
                    if is_key_pressed(VK_1):
                        capturer.select_monitor_by_click()
                        print(">>> Monitor updated!")
                        reload_config()
                        break
                    if is_key_pressed(VK_2):
                        try:
                            val = input("\nEnter total bait count: ")
                            bait_count = int(val)
                            fish_caught_counter = 0
                            print(f">>> Bait set to {bait_count}!")
                        except: print("!!! Invalid.")
                        break
                    if is_key_pressed(VK_3):
                        try:
                            val = input(f"\nEnter Auto-Sell Threshold (current {AUTO_SELL_THRESHOLD}): ")
                            new_val = int(val)
                            config_path = os.path.join(os.path.dirname(__file__), "config.py")
                            with open(config_path, "r") as f:
                                content = f.read()
                            import re
                            content = re.sub(r"AUTO_SELL_THRESHOLD\s*=\s*\d+", f"AUTO_SELL_THRESHOLD = {new_val}", content)
                            with open(config_path, "w") as f:
                                f.write(content)
                            reload_config()
                            print(f">>> Auto-Sell Threshold updated to {new_val}!")
                        except Exception as e:
                            print(f"!!! Invalid value or error saving: {e}")
                        break
                    if is_key_pressed(VK_4):
                        try:
                            val = input("\nEnter bait sets to buy (99 each): ")
                            bait_sets_to_buy = int(val)
                            print(f">>> Will buy {bait_sets_to_buy} sets ({bait_sets_to_buy * 99} bait)!")
                        except: print("!!! Invalid.")
                        break
                    if is_key_pressed(VK_5):
                        setup_collection_macro()
                        break
                    if is_key_pressed(VK_6):
                        setup_shop_macro()
                        break
                    if is_key_pressed(VK_ESC):
                        break
                    time.sleep(0.01)
                print_main_menu()
                print(">>> Press '5' to start.")
                time.sleep(0.5)

            if is_key_pressed(VK_8):
                # TRAINING / DEV SUBMENU
                bot_active = False
                recorder.stop()
                inputs.release_all()
                print("\n" + "="*40)
                print("  DEV / TRAINING MENU")
                print("  1 — Toggle Auto-Capture ON/OFF")
                print("  2 — Setup Macros (Weather)")
                print("  3 — Toggle Data Collection Mode (Auto-Weather)")
                print("  4 — Test Auto-Sell Macro")
                print("  5 — Test Minigame Tracking")
                print("  ESC — Back to Main Menu")
                print("="*40)
                
                while True:
                    if is_key_pressed(VK_1):
                        auto_capture = not auto_capture
                        print(f">>> Auto-Capture: {'ON' if auto_capture else 'OFF'}")
                        break
                    if is_key_pressed(VK_2):
                        setup_collection_macro()
                        break
                    if is_key_pressed(VK_3):
                        collection_mode_active = not collection_mode_active
                        print(f">>> Data Collection: {'ON' if collection_mode_active else 'OFF'}")
                        break
                    if is_key_pressed(VK_4):
                        print(">>> TESTING AUTO-SELL MACRO...")
                        current_state = STATE_AUTO_SELL
                        state_entry_time = time.time()
                        sell_step = 0
                        bot_active = True
                        break
                    if is_key_pressed(VK_5):
                        print(">>> TESTING MINIGAME TRACKING (10s)...")
                        test_start = time.time()
                        last_test_snap = 0
                        while time.time() - test_start < 10:
                            test_img = capturer.capture()
                            x_y, x_t, meta = vision.scan_minigame(test_img, screen_size=(1920, 1080))
                            print(f"  [DEBUG] Yellow: {x_y} | Teal: {x_t}")
                            
                            # Log failures to debug_snaps ONLY during this test
                            if (x_y is None or x_t is None) and (time.time() - last_test_snap > 1.0):
                                last_test_snap = time.time()
                                snap_dir = os.path.join(os.path.dirname(__file__), "..", "debug_snaps")
                                os.makedirs(snap_dir, exist_ok=True)
                                cv2.imwrite(os.path.join(snap_dir, f"test_fail_{int(time.time())}.png"), test_img)
                            
                            time.sleep(0.1)
                        print(">>> Test Finished.")
                        break
                    if is_key_pressed(VK_ESC):
                        break
                    time.sleep(0.01)
                print_main_menu()
                print(">>> Press '5' to start.")
                time.sleep(0.5)

            # Manual State Overrides (Y, U, I, O, P)
            manual_state = None
            if is_key_pressed(VK_Y): manual_state = STATE_IDLE
            elif is_key_pressed(VK_U): manual_state = STATE_WAITING
            elif is_key_pressed(VK_I): manual_state = STATE_HOOKED
            elif is_key_pressed(VK_O): manual_state = STATE_MINIGAME
            elif is_key_pressed(VK_P): manual_state = STATE_CAUGHT

            if manual_state:
                current_state = manual_state
                state_buffer = [manual_state] * BUFFER_SIZE # Fill buffer to lock it in
                recorder.set_state(manual_state)
                state_entry_time = time.time()
                print(f">>> [MANUAL] Overriding state to: {manual_state}")
                time.sleep(0.3) # debounce

            if not bot_active:
                time.sleep(0.05)
                continue

            # -------------------------------------------------------- #
            # 1. State-Adaptive Capture                                  #
            # -------------------------------------------------------- #
            loop_start = time.time()
            
            # For weak PCs: Skip heavy full-screen capture during minigame
            # We only 'peek' at the full screen every 15 frames to check for CAUGHT state
            should_skip_full = (current_state == STATE_MINIGAME and (frame_counter % 15 != 0))
            
            img = None
            if not should_skip_full:
                img = capturer.capture()
                if first_frame:
                    h, w = img.shape[:2]
                    print(f"Capture resolution: {w}x{h}")
                    first_frame = False
            
            frame_counter += 1

            # -------------------------------------------------------- #
            # Anti-Jam Timeout Logic                                     #
            # -------------------------------------------------------- #
            elapsed_in_state = time.time() - state_entry_time
            forced_state = None

            if current_state == STATE_IDLE and elapsed_in_state > 5.0:
                print("\n[!] TIMEOUT in IDLE (5s). Forcing WAITING and pressing F.")
                inputs.press_f()
                forced_state = STATE_WAITING
            elif current_state == STATE_WAITING and elapsed_in_state > 10.0:
                print("\n[!] TIMEOUT in WAITING (10s). Forcing HOOKED and pressing F.")
                inputs.press_f()
                forced_state = STATE_HOOKED
            elif current_state == STATE_HOOKED and elapsed_in_state > 5.0:
                print("\n[!] TIMEOUT in HOOKED (5s). Forcing MINIGAME and pressing F.")
                inputs.press_f()
                forced_state = STATE_MINIGAME
            elif current_state == STATE_MINIGAME and elapsed_in_state > 15.0:
                print("\n[!] TIMEOUT in MINIGAME (15s). Forcing CAUGHT.")
                inputs.release_all()
                forced_state = STATE_CAUGHT
            elif current_state == STATE_CAUGHT and elapsed_in_state > 5.0:
                print("\n[!] TIMEOUT in CAUGHT (5s). Forcing IDLE and clicking center.")
                inputs.click_center()
                forced_state = STATE_IDLE

            if forced_state:
                # Invalidate any photos auto-captured during this jammed period
                recorder.invalidate_recent(current_state, state_entry_time)
                
                current_state = forced_state
                state_buffer = [forced_state] * BUFFER_SIZE
                recorder.set_state(forced_state)
                state_entry_time = time.time()
                last_action_time = time.time()
                continue
            
            # -------------------------------------------------------- #
            # 2. Detect state                                            #
            # -------------------------------------------------------- #
            if not should_skip_full:
                detected = vision.get_state(img, current_state)
                
                # --- STICKY STATES (Don't let vision override these) ---
                if current_state == STATE_AUTO_SELL:
                    detected = STATE_AUTO_SELL
                if current_state == STATE_AUTO_SHOP:
                    detected = STATE_AUTO_SHOP
                
                # Guard: prevent backwards jump from MINIGAME -> HOOKED
                if current_state == STATE_MINIGAME and detected == STATE_HOOKED:
                    detected = STATE_MINIGAME
                
                state_buffer.append(detected)
                if len(state_buffer) > BUFFER_SIZE:
                    state_buffer.pop(0)
            
            new_state = state_buffer[0] if (
                len(state_buffer) == BUFFER_SIZE and
                all(s == state_buffer[0] for s in state_buffer)
            ) else current_state

            state_buffer.append(detected)
            if len(state_buffer) > BUFFER_SIZE:
                state_buffer.pop(0)

            new_state = state_buffer[0] if (
                len(state_buffer) == BUFFER_SIZE and
                all(s == state_buffer[0] for s in state_buffer)
            ) else current_state

            if new_state != current_state:
                # 1.5s cooldown specifically for HOOKED -> MINIGAME transition
                cooldown = 1.5 if (current_state == STATE_HOOKED and new_state == STATE_MINIGAME) else 1.0
                
                if elapsed_in_state < cooldown:
                    new_state = current_state  # Reject transition (cooldown)
                else:
                    print(f"  State: {current_state} → {new_state}")
                    prev_state    = current_state
                    current_state = new_state
                    inputs.release_all()
                    recorder.set_state(current_state)
                    state_entry_time = time.time()

            # -------------------------------------------------------- #
            # 4. State actions                                           #
            # -------------------------------------------------------- #
            if current_state == STATE_IDLE:
                has_pressed_f_hook = False
                
                # Check for PENDING AUTO-SELL
                if auto_sell_pending:
                    print("\n>>> STARTING AUTO-SELL SEQUENCE (From IDLE)...")
                    current_state = STATE_AUTO_SELL
                    state_entry_time = time.time()
                    auto_sell_pending = False
                    sell_step = 0
                    last_action_time = time.time()
                    continue

                if auto_shop_pending:
                    print("\n>>> STARTING AUTO-SHOP SEQUENCE (From IDLE)...")
                    current_state = STATE_AUTO_SHOP
                    state_entry_time = time.time()
                    auto_shop_pending = False
                    shop_step = 0
                    shop_loop_count = 0
                    last_action_time = time.time()
                    continue

                # Check for weather cycle
                if collection_mode_active and (time.time() - collection_cycle_start) > CYCLE_DURATION_SEC:
                    if weather_cycle_index >= 3:
                        print("\n" + "="*40)
                        print(">>> 72-MINUTE DATA COLLECTION COMPLETE!")
                        print(">>> Stopping Auto-Capture. Resuming normal fishing!")
                        print("="*40)
                        auto_capture = False
                        recorder.stop()
                        collection_mode_active = False
                        continue
                        
                    print("\n" + "="*40)
                    print(f">>> 24 MINUTE CYCLE COMPLETE!")
                    print(f">>> Changing to Weather {weather_cycle_index + 1}...")
                    print("="*40)
                    
                    # 1. Open Menu (Esc x 3)
                    for _ in range(3):
                        inputs.press_esc()
                        time.sleep(2.0)
                    
                    # 2. Click Time System
                    if MACRO_COORD_TIME_SYSTEM:
                        inputs.click_at(*MACRO_COORD_TIME_SYSTEM)
                        time.sleep(2.0)
                    
                    # 3. Click Weather
                    current_weather_coords = [MACRO_COORD_WEATHER_1, MACRO_COORD_WEATHER_2, MACRO_COORD_WEATHER_3]
                    target_weather = current_weather_coords[weather_cycle_index]
                    if target_weather:
                        inputs.click_at(*target_weather)
                        time.sleep(2.0)
                    
                    # 4. Click Confirm
                    if MACRO_COORD_CONFIRM:
                        inputs.click_at(*MACRO_COORD_CONFIRM)
                        time.sleep(4.0) # wait for weather transition
                    
                    # 5. Close Menu (Esc x 2)
                    for _ in range(2):
                        inputs.press_esc()
                        time.sleep(2.0)
                    
                    # 6. Interact with fishing spot
                    inputs.press_f()
                    time.sleep(2.0)
                    
                    # 7. Click Start Fishing
                    if MACRO_COORD_START_FISHING:
                        inputs.click_at(*MACRO_COORD_START_FISHING)
                        time.sleep(2.0)
                    
                    # Reset cycle
                    weather_cycle_index += 1
                    collection_cycle_start = time.time()
                    state_entry_time = time.time() # reset idle timeout
                    print(f">>> Weather changed. Resuming collection for next 24 minutes...")
                    continue 

                if time.time() - last_action_time > 0.5:
                    print("Casting...")
                    inputs.press_f()
                    last_action_time = time.time()

            elif current_state == STATE_WAITING:
                pass  # Wait for HOOKED (or SPACE in training mode)

            elif current_state == STATE_HOOKED:
                if not has_pressed_f_hook:
                    print("Fish hooked! Pressing F to reel...")
                    inputs.press_f()
                    has_pressed_f_hook = True
                    last_action_time = time.time()

            elif current_state == STATE_MINIGAME:
                # TURBO-SCAN: Capture ONLY the bar area for 5x speed boost
                h_f, w_f = capturer.monitor["height"], capturer.monitor["width"]
                from config import ROI_MINIGAME_BAR_REL
                ry1, ry2 = int(ROI_MINIGAME_BAR_REL[0]*h_f), int(ROI_MINIGAME_BAR_REL[1]*h_f)
                rx1, rx2 = int(ROI_MINIGAME_BAR_REL[2]*w_f), int(ROI_MINIGAME_BAR_REL[3]*w_f)
                
                # Grab tiny crop directly from GPU/Screen buffer
                bar_img = capturer.capture(region=[ry1, ry2, rx1, rx2])
                
                # Scan the pre-cropped image
                x_yellow, x_teal, meta = vision.scan_minigame(bar_img, is_strip=True, screen_size=(w_f, h_f))
                diff = (x_yellow - x_teal) if (x_yellow is not None and x_teal is not None) else None

                if diff is not None:
                    DEAD_ZONE = 16  # pixels — prevents jitter when nearly aligned
                    if abs(diff) <= DEAD_ZONE:
                        inputs.release_all()
                    elif diff < 0:
                        inputs.hold_right()
                    else:
                        inputs.hold_left()

                    # Performance Log (Every 10 frames for smooth feedback)
                    if frame_counter % 10 == 0:
                        loop_time = time.time() - loop_start
                        fps = 1.0 / loop_time if loop_time > 0 else 0
                        direction = "CENTER" if abs(diff) <= DEAD_ZONE else ("RIGHT" if diff < 0 else "LEFT")
                        
                        perf_str = f" [Perf: {fps:.1f} FPS | {loop_time*1000:.1f}ms]"
                        print(f"  Minigame: diff={diff:+.0f}px → {direction}" + perf_str)
                else:
                    inputs.release_all()

            elif current_state == STATE_CAUGHT:
                if not has_counted_catch:
                    fish_caught_counter += 1
                    
                    # Global Auto-Sell Counter
                    import config
                    config.total_fish_session += 1
                    
                    has_counted_catch = True
                    print(f">>> Fish Caught! {fish_caught_counter}/{bait_count} | Session Total: {config.total_fish_session}/{config.AUTO_SELL_THRESHOLD}")

                # Check if it's time to AUTO-SELL
                import config
                if config.total_fish_session >= config.AUTO_SELL_THRESHOLD:
                    if not auto_sell_pending:
                        print(f"\n>>> SELL THRESHOLD REACHED ({config.total_fish_session})! Will sell once back in IDLE...")
                        auto_sell_pending = True
                
                # Check if it's time to AUTO-SHOP
                if fish_caught_counter >= (bait_count - 5):
                    if not auto_shop_pending:
                        print(f"  [!] Bait low ({fish_caught_counter}/{bait_count}). Will shop once back in IDLE.")
                        auto_shop_pending = True

                if time.time() - last_action_time > 2.0:
                    inputs.click_center()
                    last_action_time = time.time()

            elif current_state == STATE_AUTO_SHOP:
                # Sequence: R -> Bait -> Max -> Purchase -> Empty -> Esc -> Idle
                if time.time() - last_action_time < 3.0:
                    continue
                
                last_action_time = time.time()
                
                if shop_step == 0:
                    inputs.press_r()
                    print("  [Auto-Shop] Step 1: Opening Shop (R)...")
                    shop_step = 1
                elif shop_step == 1:
                    inputs.click_at(MACRO_COORD_SHOP_BAIT[0], MACRO_COORD_SHOP_BAIT[1])
                    print("  [Auto-Shop] Step 2: Clicking Bait Slot...")
                    shop_step = 2
                elif shop_step == 2:
                    inputs.click_at(MACRO_COORD_SHOP_MAX[0], MACRO_COORD_SHOP_MAX[1])
                    print("  [Auto-Shop] Step 3: Clicking MAX...")
                    shop_step = 3
                elif shop_step == 3:
                    inputs.click_at(MACRO_COORD_SHOP_PURCHASE[0], MACRO_COORD_SHOP_PURCHASE[1])
                    print("  [Auto-Shop] Step 4: Clicking Purchase...")
                    shop_step = 4
                elif shop_step == 4:
                    inputs.click_at(MACRO_COORD_SHOP_CONFIRM[0], MACRO_COORD_SHOP_CONFIRM[1])
                    print("  [Auto-Shop] Step 5: Clicking Confirm Purchase...")
                    shop_step = 5
                elif shop_step == 5:
                    inputs.click_at(MACRO_COORD_SHOP_EMPTY[0], MACRO_COORD_SHOP_EMPTY[1])
                    print("  [Auto-Shop] Step 6: Clicking Empty Area...")
                    shop_step = 6
                elif shop_step == 6:
                    inputs.press_esc()
                    print("  [Auto-Shop] Step 7: Closing Shop (ESC)...")
                    shop_step = 7
                else:
                    shop_loop_count += 1
                    if shop_loop_count < bait_sets_to_buy:
                        print(f">>> Set {shop_loop_count}/{bait_sets_to_buy} complete. Relooping...")
                        shop_step = 1 # Back to clicking bait slot or max? User said loop: max -> purchase -> confirm -> empty
                        # Wait, user said: "loop the max quantity -> purchase -> confirm puirchase -> click empty area -> reloop"
                        # So we go back to Step 3 (Clicking MAX)
                        shop_step = 3
                    else:
                        fish_caught_counter = 0
                        bait_count = bait_sets_to_buy * 99
                        print(f">>> AUTO-SHOP COMPLETE! Bought {bait_sets_to_buy} sets. Resuming...")
                        current_state = STATE_IDLE
                        state_entry_time = time.time()
                last_action_time = time.time()

            elif current_state == STATE_INVENTORY:
                print(">>> INVENTORY: Selling all fish...")
                time.sleep(1.5)
                inputs.click_inv_tab_hold()
                time.sleep(1.5)
                inputs.click_quick_sell()
                time.sleep(1.5)
                inputs.click_confirm_sell()
                time.sleep(2.0)

            elif current_state == STATE_SOLD:
                print(">>> SOLD: Heading to Shop...")
                inputs.click_center()
                time.sleep(1.0)
                inputs.press_esc()
                time.sleep(2.0)
                print(">>> Step 2: Buying Bait...")
                inputs.press_r()
                time.sleep(2.0)
                last_action_time = time.time()

            elif current_state == STATE_AUTO_SELL:
                # Slow & Steady Sequence (3s delay between each)
                if time.time() - last_action_time < 3.0:
                    continue
                
                last_action_time = time.time()
                
                if sell_step == 0:
                    inputs.press_q()
                    print("  [Auto-Sell] Step 1: Opening Inventory (Q)...")
                    sell_step = 1
                elif sell_step == 1:
                    inputs.click_at(MACRO_COORD_FISH_HOLD[0], MACRO_COORD_FISH_HOLD[1])
                    print("  [Auto-Sell] Step 2: Clicking Fish Hold...")
                    sell_step = 2
                elif sell_step == 2:
                    inputs.click_at(MACRO_COORD_SELL_BTN[0], MACRO_COORD_SELL_BTN[1])
                    print("  [Auto-Sell] Step 3: Clicking Sell All...")
                    sell_step = 3
                elif sell_step == 3:
                    inputs.click_at(MACRO_COORD_CONFIRM_SELL[0], MACRO_COORD_CONFIRM_SELL[1])
                    print("  [Auto-Sell] Step 4: Clicking Confirm...")
                    # Set last_action_time forward by 7 seconds so the next step waits 10s total (3s standard + 7s extra)
                    last_action_time = time.time() + 7.0
                    sell_step = 4
                elif sell_step == 4:
                    inputs.click_center()
                    print("  [Auto-Sell] Step 5: Clearing notification...")
                    sell_step = 5
                elif sell_step == 5:
                    inputs.press_esc()
                    print("  [Auto-Sell] Step 6: Closing Menu (ESC)...")
                    sell_step = 6
                else:
                    import config
                    config.total_fish_session = 0
                    sell_step = 0
                    print(">>> AUTO-SELL COMPLETE! Resetting counter and resuming...")
                    current_state = STATE_IDLE
                    state_entry_time = time.time()

            # Reset catch-flag when not on CAUGHT screen
            if current_state != STATE_CAUGHT:
                has_counted_catch = False

    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        recorder.stop()
        inputs.stop_all()


if __name__ == "__main__":
    main()
