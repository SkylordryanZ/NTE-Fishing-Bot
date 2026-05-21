"""
recorder.py — Background screenshot saver.
Runs in a daemon thread and saves one screenshot per second to:
    RawData/<STATE>/<timestamp>.png

Usage:
    recorder = ScreenshotRecorder(capturer)
    recorder.set_state("IDLE")
    recorder.start()
    ...
    recorder.set_state("HOOKED")   # changes folder on the fly
    ...
    recorder.stop()
"""
import threading
import time
import os
import cv2
from datetime import datetime
from config import RAWDATA_DIR, SCREENSHOT_INTERVAL_SEC


class ScreenshotRecorder:
    def __init__(self, capturer):
        self.capturer = capturer
        self.rawdata_dir = RAWDATA_DIR
        self._state = "UNKNOWN"
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #
    def set_state(self, state: str):
        """Update the label used for the next saved screenshot."""
        with self._lock:
            self._state = state

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="Recorder")
        self._thread.start()
        print("[Recorder] Started — saving 1 screenshot/sec to RawData/")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("[Recorder] Stopped.")

    def invalidate_recent(self, state: str, since_time: float):
        """Move all screenshots saved for `state` since `since_time` to an Unknown folder."""
        try:
            folder = os.path.join(self.rawdata_dir, state)
            unknown_folder = os.path.join(self.rawdata_dir, "Unknown")
            if not os.path.exists(folder):
                return
            
            os.makedirs(unknown_folder, exist_ok=True)
            import shutil
            
            moved_count = 0
            for filename in os.listdir(folder):
                ext = os.path.splitext(filename)[1].lower()
                if ext not in {".png", ".jpg", ".jpeg"}:
                    continue
                    
                filepath = os.path.join(folder, filename)
                mtime = os.path.getmtime(filepath)
                if mtime >= since_time:
                    dest_path = os.path.join(unknown_folder, f"invalid_{state}_{filename}")
                    shutil.move(filepath, dest_path)
                    moved_count += 1
                    
            if moved_count > 0:
                print(f"[Recorder] Moved {moved_count} suspect images from {state} to Unknown.")
        except Exception as e:
            print(f"[Recorder] Error invalidating files: {e}")

    # ------------------------------------------------------------------ #
    # Internal loop                                                        #
    # ------------------------------------------------------------------ #
    def _run(self):
        while self._running:
            t_start = time.time()
            try:
                with self._lock:
                    state = self._state

                folder = os.path.join(self.rawdata_dir, state)
                os.makedirs(folder, exist_ok=True)

                img = self.capturer.capture()
                # Downscale directly to target model input size (224x224)
                img_resized = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
                
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filepath = os.path.join(folder, f"{ts}.jpg")
                
                # Save as compressed JPEG
                cv2.imwrite(filepath, img_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

            except Exception as e:
                print(f"[Recorder] Error: {e}")

            # Sleep for the remainder of the interval
            elapsed = time.time() - t_start
            time.sleep(max(0.0, SCREENSHOT_INTERVAL_SEC - elapsed))
