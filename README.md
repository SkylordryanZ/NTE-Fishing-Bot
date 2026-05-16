# NTE Fishing Bot (AI Vision Edition)

An autonomous fishing bot for PC games, powered by an ONNX MobileNetV2 AI model and precise HSV pixel tracking. This bot intelligently watches the screen, dynamically predicts the game state, and handles the intricate fishing minigames using simulated hardware inputs.

---

## 📂 Folder Structure

```
NTE Fishing/
├── run.bat                   # Main Launcher (Auto-elevates Admin)
├── requirements.txt          # Bot dependencies
├── README.md                 # This documentation
│
├── Train/                    # AI TRAINING HUB
│   ├── train.bat             # Start AI Training
│   ├── train.py              # Main training logic
│   ├── benchmark.bat         # Hardware Optimizer
│   ├── benchmark.py          # Benchmark logic
│   ├── requirements_train.txt # AI/Torch dependencies
│   ├── training_config.json  # Saved hardware settings
│   └── TrainingData/         # THE MASTER DATASET
│
├── model/                    # THE AI MODEL (Bot reads from here)
│   ├── state_classifier.onnx
│   └── classes.json
│
├── CaptureData/              # Main Output & Data Collection Folder
│   ├── Idle/                 # Screenshots categorized by AI live!
│   └── ...

```

---

## ⚙️ Core Modules (`src/`)

### 1. `bot.py`
The brain of the operation. It manages a strict State Machine that moves from `IDLE` → `WAITING` → `HOOKED` → `MINIGAME` → `CAUGHT`.
- **Anti-Jam Timeout System**: Tracks `elapsed_in_state`. If the AI glitches or the game UI bugs out, the bot forcefully triggers the next button press (e.g., 5s, 15s, 20s timeouts) to unjam itself.
- **Auto-Capture Mode (`5`)**: Triggers `recorder.py` to continuously save what the AI sees.
- **State Cooldowns**: Enforces a strict `1.0s` delay before accepting a new state, preventing false positives from rapid screen flashes.

### 2. `vision.py`
Handles all visual processing.
- **`__init__`**: Loads the `state_classifier.onnx` AI model into memory.
- **`get_state(img, last_state)`**: Feeds the screenshot to the AI, calculates softmax confidence, and strictly enforces one-way logical state transitions to prevent hallucinations (e.g., impossible to jump from `MINIGAME` backwards to `HOOKED`).
- **`scan_minigame(img)`**: When the AI enters `MINIGAME`, control passes to this pixel-scanner. It slices a strip of the screen and uses highly calibrated HSV color masking to calculate the distance between the Yellow indicator and the Teal target bar.

### 3. `capture.py`
- **`ScreenCapturer`**: Uses the `mss` library to grab screenshots of the primary monitor in raw BGR numpy arrays. It is significantly faster than standard `PIL.ImageGrab`.

### 4. `input_sim.py`
- **`InputSimulator`**: Standard python keyboard libraries do not work in DirectX games. This class uses `ctypes.windll.user32.SendInput` to inject raw hardware-level scancodes, completely bypassing Windows software layers so the game registers the inputs perfectly.

### 5. `recorder.py`
- **`ScreenshotRecorder`**: Runs in a background daemon thread. When Auto-Capture is active, it saves 1 frame per second to `RawData/`. 
- **`invalidate_recent(state, since_time)`**: If the bot's Anti-Jam timeout triggers, this function scrubs the `RawData/` folder and isolates any screenshots taken during the "jammed" period into an `Unknown` folder so they don't accidentally poison your dataset.

---

## 🧠 Continuous Learning (AI Training)

The bot gets smarter over time.

1. **Auto-Capture**: While fishing normally, press `5` to toggle Auto-Capture ON/OFF. The bot will automatically categorize photos into `CaptureData/` based on its own AI predictions.
2. **Curate**: After fishing, open `CaptureData/`. Quickly skim the folders to ensure the AI guessed correctly.
3. **Move**: Drag the good photos into the `TrainingData/` folder (into their matching state subfolders).
4. **Train**: Double-click the `train.bat` inside the `Train/` folder. It will automatically rebuild the AI model in the `model/` folder.

> **Hardware Optimization**: Run `benchmark.bat` inside the `Train/` folder once. It will sweep through PyTorch dataloader configurations to find the perfect `BATCH_SIZE` and `NUM_WORKERS` for your specific PC.

---

## 🎮 How to Play

1. **Launch**: Double click `run.bat` (It will automatically request Admin).
2. **Start**: Press `1` to activate the AI loop.
3. **Set Bait**: Press `4` and enter how much bait you have. The bot will automatically sell fish to the vendor when you drop to 5 bait remaining!
4. **Pause**: Press `2` to halt all actions immediately. (This also automatically pauses the Auto-Capture recorder).
5. **Resume**: Press `1` to resume the bot (The recorder will resume automatically if Auto-Capture was ON).
6. **Train**: Press `5` to toggle Auto-Capture recording.
7. **Select Monitor**: Press `7` to change which monitor the bot watches. Simply click your mouse on the game screen!

---

## 🤖 Data Collection Mode (72-Minute Farm)

If you are gathering massive amounts of data for a new location, you can automate the entire process of changing the weather to capture a full 24-hour day cycle:

1. **Setup Macro (Press `8`)**: The bot will ask you to hover your mouse and press `M` to save coordinates for:
   - The "Time System" button in your menu.
   - 3 different Weather buttons.
   - The "Confirm" button.
   - The "Start Fishing" button (that appears after you press F to interact).
2. **Start Collection (Press `9`)**: 
   - The bot will force **Auto-Capture ON**.
   - It will assume you are starting on Weather 1, and will fish normally for **24 minutes**.
   - After 24 minutes, it waits for the `IDLE` state, opens your menu, changes to Weather 2, and fishes for another 24 minutes.
   - It repeats this for Weather 3 (another 24 minutes).
   - **After exactly 72 minutes, it will automatically turn off the recording and Data Collection Mode, but it will CONTINUE normal fishing!** (Perfect for leaving overnight).
