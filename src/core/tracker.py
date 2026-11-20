import cv2
import math
import numpy as np
import mediapipe as mp
import threading
import time

from src.core.mouse_control import MouseController
from src.core.blink import BlinkDetector
from src.utils import OneEuroFilter
from src.config import *


class FaceTracker:
    def __init__(self):
        self.running = False
        self.thread = None

        self.mouse = MouseController()
        self.blink = BlinkDetector()

        self.mp_face_mesh = mp.solutions.face_mesh

        # Calibrated neutral origin p0 = (x0, y0) per Report §4.3
        self.base_x = None
        self.base_y = None

        self.calibrated = False
        self.paused = False

        self.latest_frame = None
        self.sensitivity = SENSITIVITY

        self.tracking_mode = "full"
        self.frame_counter = 0

        # Memory variables
        self.last_cx = None
        self.last_cy = None
        self.last_status = "INITIALIZING"
        self.last_points_2d = None
        self.prev_gray = None

        # Smoothing filters (Report §4.4: dead-band + adaptive 1€/EMA filter)
        self.dx_filter = OneEuroFilter(mincutoff=OEF_MIN_CUTOFF, beta=OEF_BETA, dcutoff=OEF_D_CUTOFF)
        self.dy_filter = OneEuroFilter(mincutoff=OEF_MIN_CUTOFF, beta=OEF_BETA, dcutoff=OEF_D_CUTOFF)
        
        # Sub-pixel accumulation for smooth micro-movements
        self.residual_dx = 0.0
        self.residual_dy = 0.0
        
        # Calibration sample buffers across 60 frames (Report §4.3)
        self.x_samples = []
        self.y_samples = []
        self.ear_samples = []
        
        # State exposed to UI
        self.current_ear = 0.0
        self.current_dx = 0.0
        self.current_dy = 0.0
        self.blink_threshold = DEFAULT_EAR_THRESHOLD
        self.dead_zone = DEAD_ZONE
        self.trigger_recalibration = False

    def start(self, mode="full"):
        self.tracking_mode = mode
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.blink.release_drag()

    def calculate_velocity(self, dx, dy):
        """
        Translates planar displacement into velocity vector with 2.5px dead-band (Report §4.4).
        """
        dist = math.hypot(dx, dy)
        if dist < self.dead_zone:
            return 0.0, 0.0

        effective_dist = dist - self.dead_zone
        # Power curve gives fine control near center and smooth acceleration further out
        scale = (effective_dist / dist) * (1.0 + (effective_dist ** 0.35) * 0.4) * self.sensitivity
        return dx * scale, dy * scale

    def calibrate(self, x0, y0):
        """Establishes neutral resting baseline p0=(x0, y0) from 60-frame averages (Report §4.3)."""
        self.base_x = x0
        self.base_y = y0
        self.calibrated = True
        
        if len(self.ear_samples) > 0:
            avg_open_ear = sum(self.ear_samples) / len(self.ear_samples)
            self.blink_threshold = max(0.15, avg_open_ear - BLINK_THRESHOLD_OFFSET)
            self.blink.set_threshold(self.blink_threshold)

    def run(self):
        # Report §4.2: Digital video capture via OpenCV
        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

        self.x_samples = []
        self.y_samples = []
        self.ear_samples = []

        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:

            while self.running:
                success, frame = cap.read()
                if not success:
                    continue

                # Mirror frame horizontally so head turns match screen direction naturally
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Report Table 4: Check ambient illumination
                brightness = float(np.mean(gray))
                is_low_light = brightness < MIN_BRIGHTNESS_THRESHOLD

                self.frame_counter += 1
                run_ai = True
                
                if self.tracking_mode == "intermediate" and self.frame_counter % INTERMEDIATE_FRAME_SKIP != 0:
                    run_ai = False

                status = self.last_status

                # Handle on-demand recalibration key ('R' or Spacebar)
                if self.trigger_recalibration:
                    self.calibrated = False
                    self.x_samples = []
                    self.y_samples = []
                    self.ear_samples = []
                    self.trigger_recalibration = False

                h, w = frame.shape[:2]

                if run_ai:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb)

                    if results.multi_face_landmarks:
                        face = results.multi_face_landmarks[0]
                        lm = face.landmark

                        # Report §4.2: Landmark 1 (nose tip) as primary planar coordinate vector
                        nose_x = lm[1].x * w
                        nose_y = lm[1].y * h

                        self.last_cx = int(nose_x)
                        self.last_cy = int(nose_y)
                        
                        # Track nose tip for optical flow fallback
                        self.last_points_2d = np.array([[[nose_x, nose_y]]], dtype=np.float32)
                        self.prev_gray = gray

                        # Eye landmark indices for EAR calculation
                        left_ids = [33, 160, 158, 133, 153, 144]
                        right_ids = [362, 385, 387, 263, 373, 380]
                        left_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in left_ids]
                        right_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in right_ids]

                        # Calibration Phase: average 60 frames for neutral rest position & EAR baseline (Report §4.3)
                        if not self.calibrated:
                            self.x_samples.append(nose_x)
                            self.y_samples.append(nose_y)
                            ear, _ = self.blink.update(left_eye, right_eye)
                            self.ear_samples.append(ear)

                            frames_collected = len(self.ear_samples)
                            remain = max(0, CALIBRATION_FRAMES - frames_collected)
                            status = f"Calibrating neutral pose... ({remain} left)"

                            if frames_collected >= CALIBRATION_FRAMES:
                                avg_x = float(np.mean(self.x_samples))
                                avg_y = float(np.mean(self.y_samples))
                                self.calibrate(avg_x, avg_y)
                                status = "Neutral Pose Calibrated"

                        elif self.paused:
                            status = "PAUSED"
                        else:
                            # Planar displacement relative to calibrated neutral point p0 (Report §4.2 & §4.4)
                            raw_dx = nose_x - self.base_x
                            raw_dy = nose_y - self.base_y
                            if INVERT_X: raw_dx = -raw_dx
                            if INVERT_Y: raw_dy = -raw_dy

                            # 1. Temporal smoothing via 1€ filter (Report §4.4)
                            t = time.time()
                            smooth_dx = self.dx_filter(t, raw_dx)
                            smooth_dy = self.dy_filter(t, raw_dy)
                            self.current_dx = smooth_dx
                            self.current_dy = smooth_dy

                            # 2. Dead-band thresholding (Δdead = 2.5 px) & velocity mapping
                            vel_x, vel_y = self.calculate_velocity(smooth_dx, smooth_dy)

                            # 3. Sub-pixel fractional accumulation
                            total_dx = vel_x + self.residual_dx
                            total_dy = vel_y + self.residual_dy

                            step_x = int(total_dx)
                            step_y = int(total_dy)
                            self.residual_dx = total_dx - step_x
                            self.residual_dy = total_dy - step_y

                            # Clamp to maximum speed
                            step_x = max(-MAX_SPEED, min(MAX_SPEED, step_x))
                            step_y = max(-MAX_SPEED, min(MAX_SPEED, step_y))

                            # 4. Dispatch cursor movement
                            if step_x != 0 or step_y != 0:
                                self.mouse.move_relative(step_x, step_y)

                            # 5. Process blink gestures & state machine (Report §4.5)
                            ear, action = self.blink.update(left_eye, right_eye)
                            self.current_ear = ear
                            status = f"EAR: {ear:.2f}"
                            if action:
                                status = action

                    else:
                        # Report §5.3.1 item 5: Face loss handling — safely release drag & suspend
                        self.blink.release_drag()
                        self.last_points_2d = None
                        self.prev_gray = None
                        status = "FACE LOST - Suspended"

                else:
                    # Intermediate mode (Optical Flow) on skipped frames
                    if self.last_points_2d is not None and self.prev_gray is not None:
                        new_points, st, err = cv2.calcOpticalFlowPyrLK(
                            self.prev_gray, gray, self.last_points_2d, None,
                            winSize=(15, 15), maxLevel=2,
                            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
                        )
                        
                        if st[0][0] == 1:
                            nose_x = float(new_points[0][0][0])
                            nose_y = float(new_points[0][0][1])
                            self.last_cx = int(nose_x)
                            self.last_cy = int(nose_y)
                            
                            if self.calibrated and not self.paused:
                                raw_dx = nose_x - self.base_x
                                raw_dy = nose_y - self.base_y
                                if INVERT_X: raw_dx = -raw_dx
                                if INVERT_Y: raw_dy = -raw_dy

                                t = time.time()
                                smooth_dx = self.dx_filter(t, raw_dx)
                                smooth_dy = self.dy_filter(t, raw_dy)
                                self.current_dx = smooth_dx
                                self.current_dy = smooth_dy

                                vel_x, vel_y = self.calculate_velocity(smooth_dx, smooth_dy)
                                
                                total_dx = vel_x + self.residual_dx
                                total_dy = vel_y + self.residual_dy

                                step_x = int(total_dx)
                                step_y = int(total_dy)
                                self.residual_dx = total_dx - step_x
                                self.residual_dy = total_dy - step_y

                                step_x = max(-MAX_SPEED, min(MAX_SPEED, step_x))
                                step_y = max(-MAX_SPEED, min(MAX_SPEED, step_y))

                                if step_x != 0 or step_y != 0:
                                    self.mouse.move_relative(step_x, step_y)
                                    
                        self.last_points_2d = new_points
                        self.prev_gray = gray

                if is_low_light:
                    status += " [LOW LIGHT]"

                self.last_status = status

                # Visual feedback on camera preview
                if self.calibrated and self.base_x is not None and self.base_y is not None:
                    # Draw neutral rest center crosshair (green circle)
                    cv2.circle(frame, (int(self.base_x), int(self.base_y)), int(self.dead_zone * 2), (0, 255, 0), 1)
                    
                    if self.last_cx is not None and self.last_cy is not None:
                        # Draw displacement vector line from neutral rest to current position
                        cv2.line(frame, (int(self.base_x), int(self.base_y)), (self.last_cx, self.last_cy), (0, 255, 255), 2)
                        # Current nose position (cyan)
                        cv2.circle(frame, (self.last_cx, self.last_cy), 5, (255, 255, 0), -1)
                elif self.last_cx is not None and self.last_cy is not None:
                    cv2.circle(frame, (self.last_cx, self.last_cy), 6, (0, 255, 0), -1)

                cv2.putText(frame, self.last_status, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.latest_frame = cv2.resize(frame_rgb, (1024, 680))

        cap.release()
