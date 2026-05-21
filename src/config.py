# Resolution: 1920x1080
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Monitor selection (0 = prompt to click, 1-N = specific monitor)
MONITOR_INDEX = 3 

# Regions of Interest (ROI) - [y_start_ratio, y_end_ratio, x_start_ratio, x_end_ratio]
# Bottom right button area
ROI_F_BUTTON_REL = [0.81, 0.91, 0.88, 0.96]

# Top center text area for "Fish on the hook"
ROI_HOOK_TEXT_REL = [0.18, 0.28, 0.41, 0.58]

# Mini-game bar area
ROI_MINIGAME_BAR_REL = [0.05, 0.09, 0.30, 0.70]

# Health Circles [y1, y2, x1, x2]
ROI_STAMINA_REL = [0.02, 0.12, 0.23, 0.30] # Left side
ROI_LINE_REL = [0.02, 0.12, 0.70, 0.77]    # Right side

# Template ROIs (absolute pixel ranges for 1920x1080)
# These match the Zone.jpg files provided by the user
TEMPLATE_ROI_IDLE = [915, 1080, 1348, 1920]   # Bottom Right (165x572)
TEMPLATE_ROI_WAITING = [919, 1080, 1453, 1920] # Bottom Right (161x467)
TEMPLATE_ROI_HOOKED = [0, 310, 0, 1920]        # Top (310x1920)
TEMPLATE_ROI_CAUGHT = [945, 1080, 0, 1920]      # Bottom (135x1920)
TEMPLATE_ROI_MINIGAME = [0, 191, 0, 1920]      # Top (191x1920)
TEMPLATE_ROI_SHOP = [30, 80, 50, 160]          # Top Left Title
TEMPLATE_ROI_INVENTORY = [30, 100, 150, 400]   # Top Title / Tabs
TEMPLATE_ROI_SOLD = [600, 750, 800, 1100]      # "Sold" Text area

# Shop Macro Coordinates
MACRO_COORD_SHOP_BAIT = (154, 256)
MACRO_COORD_SHOP_MAX = (1821, 948)
MACRO_COORD_SHOP_PURCHASE = (1619, 1033)
MACRO_COORD_SHOP_CONFIRM = (1171, 702)
MACRO_COORD_SHOP_EMPTY = (1136, 837)

# Inventory / Sell Coordinates
MACRO_COORD_FISH_HOLD = (146, 413)
MACRO_COORD_SELL_BTN = (1063, 969)
MACRO_COORD_CONFIRM_SELL = (1171, 702)
COLOR_WHITE = (255, 255, 255)
COLOR_CYAN_HOOK = (220, 200, 50)  # Blue-ish button
COLOR_YELLOW_INDICATOR = (100, 235, 255) # Yellow
COLOR_GREEN_BAR = (180, 255, 100) # Green-ish

# Thresholds
THRESHOLD_F_BUTTON = 0.8
THRESHOLD_COLOR_MATCH = 50 # Max Euclidean distance in BGR space

# Keys
KEY_F = 'f'
KEY_A = 'a'
KEY_D = 'd'
KEY_R = 'r'
KEY_ESC = 'esc'
KEY_Q = 'q'

# State Names
STATE_IDLE = "IDLE"
STATE_WAITING = "WAITING"
STATE_HOOKED = "HOOKED"
STATE_MINIGAME = "MINIGAME"
STATE_CAUGHT = "CAUGHT"
STATE_SHOP = "SHOP"
STATE_INVENTORY = "INVENTORY"
STATE_SOLD = "SOLD"
STATE_AUTO_SELL = "AUTO_SELL"
STATE_AUTO_SHOP = "AUTO_SHOP"

# Screenshot Recorder
SAVE_SCREENSHOTS = False          # Toggle screenshot collection on/off
RAWDATA_DIR = "CaptureData"          # Main directory for all categorized images
SCREENSHOT_INTERVAL_SEC = 1.0    # Capture one screenshot per second

# ------------------------------------------------------------------ #
# Macro Coordinates (Data Collection Mode)
# ------------------------------------------------------------------ #
MACRO_COORD_TIME_SYSTEM = (1666, 613)
MACRO_COORD_WEATHER_1 = (695, 961)
MACRO_COORD_WEATHER_2 = (956, 957)
MACRO_COORD_WEATHER_3 = (1210, 955)
MACRO_COORD_CONFIRM = (1687, 1012)
MACRO_COORD_START_FISHING = (1604, 940)

# Auto-Sell Macro Coordinates
MACRO_COORD_FISH_HOLD = (146, 413)
MACRO_COORD_SELL_BTN = (1063, 969)
MACRO_COORD_CONFIRM_SELL = (1171, 702)

# Feature Settings
AUTO_SELL_THRESHOLD = 1000
total_fish_session = 0

