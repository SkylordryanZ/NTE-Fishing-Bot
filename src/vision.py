"""
vision.py — AI-powered state detector and HSV pixel scanner for NTE Fishing Bot.
Combines ONNX MobileNetV2 classification for state tracking and
precise OpenCV HSV masking for the minigame mechanics.
"""

import os
import json
import time

import numpy as np
import cv2
import onnxruntime as ort

from config import (
    STATE_IDLE, STATE_WAITING, STATE_HOOKED,
    STATE_MINIGAME, STATE_CAUGHT,
    STATE_SHOP, STATE_INVENTORY, STATE_SOLD,
    ROI_MINIGAME_BAR_REL
)

# ------------------------------------------------------------------ #
# Constants                                                            #
# ------------------------------------------------------------------ #
IMG_SIZE     = 224
MODEL_PATH   = "model/state_classifier.onnx"
CLASSES_PATH = "model/classes.json"

# ImageNet normalisation (matches training)
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Map lowercase class name → state constant
_NAME_TO_STATE = {
    "caught":    STATE_CAUGHT,
    "hooked":    STATE_HOOKED,
    "idle":      STATE_IDLE,
    "minigame":  STATE_MINIGAME,
    "waiting":   STATE_WAITING,
    "shop":      STATE_SHOP,
    "inventory": STATE_INVENTORY,
    "sold":      STATE_SOLD,
}


class Vision:
    """AI-powered state detector backed by an ONNX MobileNetV2 classifier."""

    def __init__(self):
        for path in (MODEL_PATH, CLASSES_PATH):
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"[Vision] Missing: {path}\n"
                    "  Run train.bat first to generate the AI model."
                )

        # Cached bar location so we don't re-scan every frame
        self._bar_cache       = None  # (bar_y, bar_x1, bar_x2)
        self._bar_fail_count  = 0     # consecutive detection failures

        # Load UI Templates for precision 'texture' matching
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.tpl_teal   = cv2.imread(os.path.join(template_dir, "bar_teal.png"), cv2.IMREAD_COLOR)
        self.tpl_yellow = cv2.imread(os.path.join(template_dir, "bar_yellow.png"), cv2.IMREAD_COLOR)
        
        if self.tpl_teal is None or self.tpl_yellow is None:
            print("  [Warning] UI Templates not found! Make sure bar_teal.png and bar_yellow.png exist.")

        with open(CLASSES_PATH) as f:
            classes = json.load(f)   # e.g. ["Caught", "Hooked", "Idle", ...]

        self.idx_to_state = {
            i: _NAME_TO_STATE.get(c.lower(), c)
            for i, c in enumerate(classes)
        }

        # Prefer AMD GPU (DirectML), fall back to CPU
        providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
        try:
            self.session = ort.InferenceSession(MODEL_PATH, providers=providers)
        except Exception:
            self.session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])

        active = self.session.get_providers()
        print(f"[Vision] AI Model loaded — providers: {active}")
        print(f"[Vision] Classes tracked: {classes}")

        self.input_name = self.session.get_inputs()[0].name

    # ---------------------------------------------------------------- #
    # AI State Classifier                                              #
    # ---------------------------------------------------------------- #
    def get_state(self, img: np.ndarray, last_state: str) -> str:
        """
        Classify the full game screenshot.
        Returns one of the STATE_* constants from config.
        """
        tensor  = self._preprocess(img)
        logits  = self.session.run(None, {self.input_name: tensor})[0][0]
        idx     = int(np.argmax(logits))
        
        predicted = self.idx_to_state.get(idx, last_state)

        # Enforce strict logical flow to filter out noisy AI predictions
        ALLOWED_TRANSITIONS = {
            STATE_IDLE:     {STATE_IDLE, STATE_WAITING},
            STATE_WAITING:  {STATE_WAITING, STATE_HOOKED},
            STATE_HOOKED:   {STATE_HOOKED, STATE_MINIGAME},
            STATE_MINIGAME: {STATE_MINIGAME, STATE_CAUGHT},
            STATE_CAUGHT:   {STATE_CAUGHT, STATE_IDLE},
        }

        # Only apply restrictions if we are currently in the main fishing loop
        if last_state in ALLOWED_TRANSITIONS:
            if predicted not in ALLOWED_TRANSITIONS[last_state]:
                # Prediction is impossible according to game logic, ignore it
                return last_state

        return predicted

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """BGR numpy array → float32 NCHW tensor, ImageNet-normalised."""
        rgb      = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        resized  = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE)).astype(np.float32) / 255.0
        normed   = (resized - _MEAN) / _STD
        return normed.transpose(2, 0, 1)[np.newaxis]   # (1, 3, H, W)

    # ---------------------------------------------------------------- #
    # Pixel-Level Minigame Trackers                                    #
    # ---------------------------------------------------------------- #
    def scan_minigame(self, img: np.ndarray, is_strip=False, screen_size=(1920, 1080)):
        """
        Scans for the teal bar and yellow indicator.
        If is_strip=True, 'img' is already a crop of the bar area.
        """
        w_full, h_full = screen_size
        
        if is_strip:
            bar_roi = img
            x1 = int(ROI_MINIGAME_BAR_REL[2] * w_full)
        else:
            # Full frame mode
            h, w = img.shape[:2]
            y1_rel, y2_rel, x1_rel, x2_rel = ROI_MINIGAME_BAR_REL
            ry1, ry2 = int(y1_rel*h), int(y2_rel*h)
            rx1, rx2 = int(x1_rel*w), int(x2_rel*w)
            bar_roi = img[ry1:ry2, rx1:rx2]
            x1 = rx1

        x_yellow, x_teal = None, None
        conf_l, conf_r, conf_y = 0, 0, 0
        loc_l, loc_r, loc_y = None, None, None

        # --- Precision Texture Matching (v3: Dual-Cap Pincer) ---
        if self.tpl_teal is not None and self.tpl_yellow is not None:
            # 1. Match Teal Bar LEFT CAP
            res_l = cv2.matchTemplate(bar_roi, self.tpl_teal, cv2.TM_CCOEFF_NORMED)
            _, conf_l, _, loc_l = cv2.minMaxLoc(res_l)
            
            # 2. Match Teal Bar RIGHT CAP (flip the left cap template)
            tpl_right = cv2.flip(self.tpl_teal, 1)
            res_r = cv2.matchTemplate(bar_roi, tpl_right, cv2.TM_CCOEFF_NORMED)
            _, conf_r, _, loc_r = cv2.minMaxLoc(res_r)
            
            if conf_l > 0.6 and conf_r > 0.6:
                # True Center is exactly between the two caps
                x_left  = loc_l[0] + (self.tpl_teal.shape[1] // 2)
                x_right = loc_r[0] + (self.tpl_teal.shape[1] // 2)
                x_teal  = ((x_left + x_right) // 2) + x1
            elif conf_l > 0.6:
                # Fallback if one cap is obscured
                x_teal = loc_l[0] + (self.tpl_teal.shape[1] // 2) + x1 
            
            # 3. Match Yellow Marker
            res_y = cv2.matchTemplate(bar_roi, self.tpl_yellow, cv2.TM_CCOEFF_NORMED)
            _, conf_y, _, loc_y = cv2.minMaxLoc(res_y)
            if conf_y > 0.6:
                x_yellow = loc_y[0] + (self.tpl_yellow.shape[1] // 2) + x1

        # Return extra info for the 'Crime Scene' logger
        results = {
            'x_yellow': x_yellow, 'x_teal': x_teal,
            'conf_l': conf_l, 'loc_l': loc_l,
            'conf_r': conf_r, 'loc_r': loc_r,
            'conf_y': conf_y, 'loc_y': loc_y,
            'x1': x1
        }
        
        return x_yellow, x_teal, results

    def scan_stamina_circles(self, img: np.ndarray):
        """
        Estimates stamina percentage based on the exact config ROIs.
        """
        h, w = img.shape[:2]
        
        from config import ROI_STAMINA_REL, ROI_LINE_REL
        # Find the center of the left box (Fish)
        fish_cx = int(((ROI_STAMINA_REL[2] + ROI_STAMINA_REL[3]) / 2) * w)
        fish_cy = int(((ROI_STAMINA_REL[0] + ROI_STAMINA_REL[1]) / 2) * h)
        
        # Find the center of the right box (Line)
        line_cx = int(((ROI_LINE_REL[2] + ROI_LINE_REL[3]) / 2) * w)
        line_cy = int(((ROI_LINE_REL[0] + ROI_LINE_REL[1]) / 2) * h)
        
        # The radius of the colored ring is roughly 4% of screen height
        radius = int(h * 0.04)

        def ring_fill_pct(cx, cy, color_lower, color_upper):
            """Count coloured pixels in an annular region around (cx, cy)."""
            y1 = max(0, cy - radius)
            y2 = min(h, cy + radius)
            x1 = max(0, cx - radius)
            x2 = min(w, cx + radius)
            roi = img[y1:y2, x1:x2]
            if roi.size == 0:
                return 0.0

            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_roi, color_lower, color_upper)

            # Only count pixels inside the ring (not the centre icon or background)
            rh, rw = roi.shape[:2]
            ry, rx = np.ogrid[:rh, :rw]
            cy_r, cx_r = rh // 2, rw // 2
            dist = np.sqrt((rx - cx_r)**2 + (ry - cy_r)**2)
            # Inner radius 35%, outer radius 95%
            ring_mask = ((dist > radius * 0.35) & (dist < radius * 0.95)).astype(np.uint8) * 255
            combined = cv2.bitwise_and(mask, ring_mask)

            ring_area = np.sum(ring_mask > 0)
            filled    = np.sum(combined > 0)
            return (filled / ring_area * 100) if ring_area > 0 else 0.0

        # Yellow/White/Red ring detection for Fish
        fish_pct = ring_fill_pct(fish_cx, fish_cy,
            np.array([0, 0, 150]),     # Very broad to catch white/yellow/red
            np.array([45, 255, 255]))

        # Blue/Red ring detection for Line
        line_pct = ring_fill_pct(line_cx, line_cy,
            np.array([0, 0, 150]),     # Broad enough to catch blue and red/yellow
            np.array([130, 255, 255]))

        return round(fish_pct, 1), round(line_pct, 1)

    def scan_health(self, img: np.ndarray):
        """Legacy stamina scanning using fixed relative ROIs. Use scan_stamina_circles() instead."""
        stamina_roi, _ = self.get_roi(img, [0.02, 0.12, 0.23, 0.30])
        stamina_hsv = cv2.cvtColor(stamina_roi, cv2.COLOR_BGR2HSV)
        stamina_mask = cv2.inRange(stamina_hsv, np.array([20, 100, 100]), np.array([40, 255, 255]))
        stamina_pct = np.sum(stamina_mask > 0) / (stamina_roi.size / 3) * 100

        line_roi, _ = self.get_roi(img, [0.02, 0.12, 0.70, 0.77])
        line_hsv = cv2.cvtColor(line_roi, cv2.COLOR_BGR2HSV)
        line_mask = cv2.inRange(line_hsv, np.array([80, 100, 100]), np.array([110, 255, 255]))
        line_pct = np.sum(line_mask > 0) / (line_roi.size / 3) * 100

        return min(100, stamina_pct * 4), min(100, line_pct * 4)

    def get_roi_abs(self, img: np.ndarray, abs_roi: list):
        y1, y2, x1, x2 = abs_roi
        return img[y1:y2, x1:x2], (x1, y1)

    def get_roi(self, img: np.ndarray, rel_roi: list):
        h, w = img.shape[:2]
        y1, y2 = int(rel_roi[0] * h), int(rel_roi[1] * h)
        x1, x2 = int(rel_roi[2] * w), int(rel_roi[3] * w)
        return img[y1:y2, x1:x2], (x1, y1)
