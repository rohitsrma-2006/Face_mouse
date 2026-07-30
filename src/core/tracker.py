import cv2
import numpy as np
import mediapipe as mp
import threading
import time

from src.core.mouse_control import MouseController
from src.core.blink import BlinkDetector
from src.core.pose import HeadPoseEstimator
from src.utils import OneEuroFilter
from src.config import *

class FaceTracker:
    def __init__(self):
        self.running = False
        self.thread = None

        self.mouse = MouseController()
        self.blink = BlinkDetector()
        self.pose = HeadPoseEstimator()

        self.mp_face_mesh = mp.solutions.face_mesh

        self.base_yaw = None
        self.base_pitch = None

        self.calibrated = False
        self.paused = False

        self.latest_frame = None
        self.sensitivity = SENSITIVITY

        self.tracking_mode = "full"
        self.frame_counter = 0

        # Memory variables
        self.last_cx = None
        self.last_cy = None
        self.last_status = ""
        self.last_points_2d = None
        self.prev_gray = None

        self.dx_filter = OneEuroFilter(mincutoff=OEF_MIN_CUTOFF, beta=OEF_BETA, dcutoff=OEF_D_CUTOFF)
        self.dy_filter = OneEuroFilter(mincutoff=OEF_MIN_CUTOFF, beta=OEF_BETA, dcutoff=OEF_D_CUTOFF)
        
        # Sub-pixel accumulation
        self.residual_dx = 0.0
        self.residual_dy = 0.0
        
        # Adaptive blink calibration
        self.ear_samples = []
        
        # State exposed to UI
        self.current_ear = 0.0
        self.current_yaw = 0.0
        self.current_pitch = 0.0
        self.blink_threshold = 0.22
        self.dead_zone = 1.5

    def start(self, mode="full"):
        self.tracking_mode = mode
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def accelerate(self, value):
        sign = 1 if value >= 0 else -1
        value = abs(value)
        if value < self.dead_zone: return 0.0
        # Subtract dead zone so it starts from 0 smoothly instead of jumping
        active_val = value - self.dead_zone
        return sign * (active_val ** 1.35) * 2.5 * self.sensitivity

    def calibrate(self, yaw, pitch):
        self.base_yaw = yaw
        self.base_pitch = pitch
        self.calibrated = True
        
        if len(self.ear_samples) > 0:
            avg_open_ear = sum(self.ear_samples) / len(self.ear_samples)
            self.blink_threshold = avg_open_ear - BLINK_THRESHOLD_OFFSET
            self.blink.set_threshold(self.blink_threshold)

    def run(self):
        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        start_time = None
        self.ear_samples = []

        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:

            while self.running:
                success, frame = cap.read()
                if not success: continue

                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                self.frame_counter += 1
                run_ai = True
                
                if self.tracking_mode == "intermediate" and self.frame_counter % INTERMEDIATE_FRAME_SKIP != 0:
                    run_ai = False

                status = self.last_status

                if run_ai:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb)

                    if results.multi_face_landmarks:
                        face = results.multi_face_landmarks[0]
                        lm = face.landmark
                        h, w = frame.shape[:2]

                        # Nose tip, Chin, Left eye corner, Right eye corner, Left mouth, Right mouth
                        model_points_ids = [1, 152, 33, 263, 61, 291]
                        image_points = np.array([
                            (lm[i].x * w, lm[i].y * h) for i in model_points_ids
                        ], dtype=np.float32)
                        
                        self.last_points_2d = image_points.reshape(-1, 1, 2)
                        self.prev_gray = gray

                        yaw, pitch = self.pose.estimate(image_points, frame)
                        self.current_yaw = yaw
                        self.current_pitch = pitch
                        
                        self.last_cx = int(image_points[0][0])
                        self.last_cy = int(image_points[0][1])

                        left_ids = [33, 160, 158, 133, 153, 144]
                        right_ids = [362, 385, 387, 263, 373, 380]
                        left_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in left_ids]
                        right_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in right_ids]

                        # Calibrate
                        if getattr(self, "trigger_recalibration", False):
                            self.calibrated = False
                            start_time = None
                            self.ear_samples = []
                            self.trigger_recalibration = False

                        if not self.calibrated:
                            if start_time is None:
                                start_time = time.time()
                            elapsed = time.time() - start_time
                            remain = max(0, 3 - int(elapsed))
                            status = f"Calibrating... {remain}"
                            
                            ear, _ = self.blink.update(left_eye, right_eye)
                            self.ear_samples.append(ear)

                            if elapsed >= 3:
                                self.calibrate(yaw, pitch)
                                
                        elif self.paused:
                            status = "PAUSED"
                        else:
                            shift_yaw = yaw - self.base_yaw
                            shift_pitch = pitch - self.base_pitch

                            # 1. Smooth the raw angles (positions) instead of the velocities
                            t = time.time()
                            smooth_yaw = self.dx_filter(t, shift_yaw)
                            smooth_pitch = self.dy_filter(t, shift_pitch)

                            # 2. Calculate continuous float velocity
                            dx_float = self.accelerate(smooth_yaw)
                            dy_float = self.accelerate(smooth_pitch)

                            # 3. Add fractional pixels from previous frames
                            total_dx = dx_float + self.residual_dx
                            total_dy = dy_float + self.residual_dy

                            # 4. Extract integer movement and keep the remainder
                            dx = int(total_dx)
                            dy = int(total_dy)
                            self.residual_dx = total_dx - dx
                            self.residual_dy = total_dy - dy

                            dx = max(-MAX_SPEED, min(MAX_SPEED, dx))
                            dy = max(-MAX_SPEED, min(MAX_SPEED, dy))

                            self.mouse.move_relative(dx, dy)

                            ear, action = self.blink.update(left_eye, right_eye)
                            self.current_ear = ear
                            status = f"EAR: {ear:.2f}"
                            if action: status = action
                else:
                    # Optical flow for intermediate skipped frames
                    if self.last_points_2d is not None and self.prev_gray is not None:
                        new_points, st, err = cv2.calcOpticalFlowPyrLK(
                            self.prev_gray, gray, self.last_points_2d, None,
                            winSize=(15, 15), maxLevel=2,
                            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
                        )
                        
                        if st[0][0] == 1:
                            self.last_cx = int(new_points[0][0][0])
                            self.last_cy = int(new_points[0][0][1])
                            
                            yaw, pitch = self.pose.estimate(new_points.reshape(-1, 2), frame)
                            self.current_yaw = yaw
                            self.current_pitch = pitch
                            
                            if self.calibrated and not self.paused:
                                shift_yaw = yaw - self.base_yaw
                                shift_pitch = pitch - self.base_pitch

                                t = time.time()
                                smooth_yaw = self.dx_filter(t, shift_yaw)
                                smooth_pitch = self.dy_filter(t, shift_pitch)

                                dx_float = self.accelerate(smooth_yaw)
                                dy_float = self.accelerate(smooth_pitch)
                                
                                total_dx = dx_float + self.residual_dx
                                total_dy = dy_float + self.residual_dy

                                dx = int(total_dx)
                                dy = int(total_dy)
                                self.residual_dx = total_dx - dx
                                self.residual_dy = total_dy - dy

                                dx = max(-MAX_SPEED, min(MAX_SPEED, dx))
                                dy = max(-MAX_SPEED, min(MAX_SPEED, dy))

                                self.mouse.move_relative(dx, dy)
                                
                        self.last_points_2d = new_points
                        self.prev_gray = gray

                self.last_status = status

                if self.last_cx is not None and self.last_cy is not None:
                    cv2.circle(frame, (self.last_cx, self.last_cy), 6, (0, 255, 0), -1)

                cv2.putText(frame, self.last_status, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize in background thread for better performance
                self.latest_frame = cv2.resize(frame_rgb, (1024, 680))

        cap.release()