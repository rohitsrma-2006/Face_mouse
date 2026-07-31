# Application Settings
APP_NAME = "FaceMouse AI"
WINDOW_SIZE = "500x420"
THEME_MODE = "dark"
COLOR_THEME = "blue"

# Camera Settings
CAMERA_INDEX = 0

# Tracking Settings
DEAD_ZONE = 8
SENSITIVITY = 1.8
MAX_SPEED = 40
INTERMEDIATE_FRAME_SKIP = 2

# One Euro Filter parameters (for smoothing)
OEF_MIN_CUTOFF = 0.05     # Decreasing removes jitter but adds lag
OEF_BETA = 0.5            # Increasing removes lag but adds jitter
OEF_D_CUTOFF = 1.0

# Blink Settings
BLINK_THRESHOLD_OFFSET = 0.05 # How much below the average open eye EAR to trigger a blink
LEFT_COOLDOWN = 0.45

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
RIGHT_COOLDOWN = 1.0
QUICK_BLINK_FRAMES = 2
HOLD_BLINK_FRAMES = 10
DOUBLE_WINDOW = 0.55