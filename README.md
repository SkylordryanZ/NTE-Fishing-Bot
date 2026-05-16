# NTE Fishing Bot (AI Vision Edition)

> [!CAUTION]
> **USE AT YOUR OWN RISK**: This bot is for educational purposes only. Using automation in online games may violate Terms of Service and could lead to account restrictions.

An autonomous fishing bot for PC games, powered by an ONNX MobileNetV2 AI model and precise HSV pixel tracking. This project was developed as a way to apply computer vision and machine learning concepts to a real-world, applicable challenge.

### 🚀 Quick Start (For Users)
If you just want to use the bot, it comes **pre-trained and ready to go**. 
- The included model in the `model/` folder has been trained on a foundational dataset to recognize game states accurately.
- While it works out of the box, you can always use the built-in **Data Collection** and **Training Hub** to refine the AI for your specific graphics settings or new locations!

> [!NOTE]
> **Economy Requirements**: Since the bot cannot yet read your current balance, ensure you have a decent amount of **Scale Coin** and at least **100 bait** before starting the fully autonomous loop. This ensures the first few "Buy" cycles succeed while the bot begins its sell-and-buy routine.

---

## 📂 Folder Structure

```
NTE Fishing/
├── run.bat                   # Main Launcher (Auto-elevates Admin)
├── requirements.txt          # Bot dependencies
├── .gitignore                # Excludes venv, training data, etc.
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
- **Data Collection Modes**: Integrated recorder for dataset expansion.
- **Refined UI**: Centralized menu system that reprints for easy navigation.

### 2. `vision.py`
Handles all visual processing.
- **`__init__`**: Loads the `state_classifier.onnx` AI model into memory.
- **`get_state(img, last_state)`**: Feeds the screenshot to the AI and enforces one-way logical state transitions.
- **`scan_minigame(img)`**: Uses high-precision HSV color masking and UI templates to track the fishing bar.

### 3. `capture.py`
- **`ScreenCapturer`**: Uses the `mss` library for high-speed primary monitor capture.

### 4. `input_sim.py`
- **`InputSimulator`**: Uses `pydirectinput` for hardware-level scancode injection, bypassing DirectX software layers.

---

## 🧠 Training & Improvement (Manual Process)

You can improve the bot's accuracy by providing it with new examples from your own gameplay.

1. **Auto-Capture**: While fishing, enter the Dev Menu (**8**) and toggle Auto-Capture. The bot will automatically categorize photos into `CaptureData/` based on its predictions.
2. **Curate**: Skim `CaptureData/` to ensure the AI guessed correctly.
3. **Move**: Drag verified photos into `Train/TrainingData/`.
4. **Train**: Run `Train/train.bat` to rebuild the model.

> **Hardware Optimization**: Run `Train/benchmark.bat` once to find the perfect `BATCH_SIZE` and `NUM_WORKERS` for your PC.

---

## 🎮 How to Play

1. **Launch**: Double click `run.bat` (Auto-elevates to Admin).
2. **Start/Resume**: Press **5** to activate the AI loop.
3. **Pause**: Press **6** to halt all actions immediately.
4. **Configure**: Press **7** to:
   - Select your target monitor.
   - Set bait count.
   - Set Auto-Sell thresholds.
   - Setup inventory/shop macros (Auto-Sell & Auto-Shop).
5. **Dev/Train**: Press **8** to access data collection and testing tools.
6. **Exit**: Press **9** to close the bot.

---

## 🤖 Data Collection Mode (72-Minute Farm)

Automate weather cycles to capture a full 24-hour day cycle:

1. **Setup Macro**: Open Dev Menu (**8**) → Setup Macros (Weather). Save coordinates for Time System, Weathers, and Confirm buttons.
2. **Start Collection**: Open Dev Menu (**8**) → Toggle Data Collection Mode.
3. **Automated Cycle**:
   - Bot fishes for **24 minutes** per weather state.
   - Automatically handles menu navigation to change weather.
   - Shuts down recording after **72 minutes** while continuing to fish.
