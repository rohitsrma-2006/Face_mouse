# FaceMouse AI

FaceMouse AI is an advanced, real-time computer vision application that allows you to control your computer's mouse cursor using your head movements and facial expressions. Built with a sleek, modern UI and powered by a highly optimized AI tracking engine, it offers a hands-free navigation experience.

## ✨ Features

* **3D Head Pose Tracking:** Uses advanced AI to estimate your head's Yaw and Pitch in 3D space, translating it into smooth, natural, "joystick-like" mouse movements.
* **Sub-Pixel Cursor Smoothing:** Processes raw head angles through a VR-grade 1€ Filter *before* movement calculation, while accumulating fractional pixels for buttery-smooth precision at all speeds.
* **Zero-Latency Mouse Engine:** Utilizes raw Windows API (`ctypes`) for instantaneous cursor response, bypassing standard input lag.
* **Adaptive Blink Detection:** Automatically calibrates to your unique eye shape (Eye Aspect Ratio) during startup to detect blinks accurately.
    * **Left Click:** A quick, standard blink.
    * **Double Click:** Two rapid blinks.
    * **Drag Mode:** Hold your eyes closed for a moment to toggle drag-and-drop mode.
* **Optical Flow CPU Saver:** Features an "Intermediate" tracking mode that skips heavy neural network processing on alternate frames, using lightweight optical flow to maintain a 30+ FPS cursor while slashing CPU usage by up to 50%.
* **Beautiful Dashboard:** A dark-themed, CustomTkinter-powered interface displaying live analytics, your camera feed, and intuitive controls.

## 🚀 Installation

1. **Clone or Download the Repository:**
   ```bash
   git clone https://github.com/yourusername/FaceMouse_AI.git
   cd FaceMouse_AI
   ```

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Usage

Start the application by running the main entry script:

```bash
python main.py
```

### Controls & Navigation
* **Calibrate:** Keep your head centered and look at the screen when the app starts up. It will calibrate your resting head position and your baseline Eye Aspect Ratio.
* **Spacebar:** Pauses and unpauses the tracking engine.
* **'R' Key:** Recalibrates your center position and blink threshold.
* **'ESC' Key:** Exits the application securely.

### Customization
You can easily tweak the AI's behavior by modifying the constants in `src/config.py`:
* `SENSITIVITY` and `MAX_SPEED` to change how fast the cursor moves.
* `DEAD_ZONE_ANGLE` to adjust how much you need to move your head before the cursor responds.
* `OEF_MIN_CUTOFF` and `OEF_BETA` to tune the cursor smoothing filter.

## 🛠️ Project Architecture

* `main.py` - Application entry point.
* `src/ui/app.py` - The CustomTkinter graphical interface.
* `src/core/tracker.py` - The heart of the AI engine handling the tracking loop.
* `src/core/pose.py` - 3D head pose estimation logic.
* `src/core/blink.py` - Eye Aspect Ratio (EAR) calculations and click logic.
* `src/core/mouse_control.py` - Windows API integration for moving the cursor.

## 📦 Building as an Executable (.exe)

To package FaceMouse AI into a standalone `.exe` file for Windows without needing Python installed, you can use **PyInstaller**. 

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the executable using the following command (this ensures `customtkinter` and `mediapipe` assets are correctly bundled and the console window is hidden):
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" --add-data "venv/Lib/site-packages/mediapipe;mediapipe/" main.py
   ```
3. Your compiled application will be available in the `dist/main/` directory.

## 📝 License
[MIT License](LICENSE) (or add your preferred license here).
