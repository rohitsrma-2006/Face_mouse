# Application Settings
APP_NAME = "FaceMouse AI"
WINDOW_SIZE = "500x420"
THEME_MODE = "dark"
COLOR_THEME = "blue"

# Camera Settings (Report §4.2: 30 FPS capture with OpenCV)
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Tracking Settings
INVERT_X = False
INVERT_Y = False

# Dead-band in pixels (Report §4.4: "removes micro-tremors below Δdead = 2.5 px")
DEAD_ZONE = 2.5

# Sensitivity: displacement-to-cursor coordinate gain (Report §4.4, Table 3)
SENSITIVITY = 0.35

# Maximum speed cap (pixels per frame) to prevent overshoot
MAX_SPEED = 20

# Frame skip for intermediate (optical flow) mode
INTERMEDIATE_FRAME_SKIP = 2

# One Euro Filter parameters (Report §4.4: adaptive jitter smoothing)
OEF_MIN_CUTOFF = 0.1       # Lower = smoother; Higher = responsive
OEF_BETA = 0.5             # High-speed lag suppression
OEF_D_CUTOFF = 1.0

# Blink & Gesture FSM Settings (Report §4.5 & Figure 2)
# Baseline threshold τ = 0.21 (Report Figure 2 & Figure 3)
DEFAULT_EAR_THRESHOLD = 0.21
BLINK_THRESHOLD_OFFSET = 0.045   # Adaptive offset from open-eye baseline

# Temporal windows (Report Figure 2):
# Left Click: EAR < τ (100 - 300 ms)
SINGLE_CLICK_MIN_TIME = 0.10     # 100 ms
SINGLE_CLICK_MAX_TIME = 0.30     # 300 ms

# Double Click: 2 bursts within 400 ms
DOUBLE_WINDOW = 0.40             # 400 ms

# Drag Mode Toggle: EAR < τ (> 600 ms)
DRAG_HOLD_TIME = 0.60            # 600 ms

# Dual-Eye Symmetry & Squint Mitigation (Report Table 4)
MAX_EYE_ASYMMETRY = 0.08

# Ambient Illumination Sensitivity Check (Report Table 4 & §5.3.1)
MIN_BRIGHTNESS_THRESHOLD = 35.0

# Refractory Cooldown Periods (Report §4.5)
LEFT_COOLDOWN = 0.45             # Minimum seconds between left clicks
RIGHT_COOLDOWN = 1.0             # Minimum seconds between drag-mode toggles

# Neutral Calibration (Report §4.3: baseline p0 established by averaging 60 frames)
CALIBRATION_FRAMES = 60


def save_setting(key, value):
    import os
    config_path = os.path.abspath(__file__)
    with open(config_path, 'r') as f:
        lines = f.readlines()

    with open(config_path, 'w') as f:
        for line in lines:
            if line.startswith(f"{key} ="):
                f.write(f"{key} = {value}\n")
            else:
                f.write(line)
