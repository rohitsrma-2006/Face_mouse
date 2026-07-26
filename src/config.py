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
RIGHT_COOLDOWN = 1.0
QUICK_BLINK_FRAMES = 2
HOLD_BLINK_FRAMES = 10
DOUBLE_WINDOW = 0.55