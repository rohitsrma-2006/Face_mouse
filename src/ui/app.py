import os
import customtkinter as ctk
from PIL import Image, ImageTk

from src.config import *
from src.core.tracker import FaceTracker


class FloatingOverlay(ctk.CTkToplevel):
    def __init__(self, parent, tracker, on_open_dashboard):
        super().__init__(parent)
        self.tracker = tracker
        self.on_open_dashboard = on_open_dashboard
        
        self.title("FaceMouse Action Menu")
        self.geometry("300x320")
        
        # Position in top right corner
        self.geometry(f"+{self.winfo_screenwidth() - 320}+50")
        
        # Make it always on top and remove standard borders
        self.wm_attributes("-topmost", True)
        self.overrideredirect(True) 
        
        self.configure(fg_color="#1e293b")
        
        # Status Light
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=(20, 10))
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", font=("Segoe UI", 28), text_color="#22c55e")
        self.status_dot.pack(side="left", padx=8)
        
        self.status_text = ctk.CTkLabel(self.status_frame, text="TRACKING", font=("Segoe UI", 20, "bold"), text_color="#f8fafc")
        self.status_text.pack(side="left")

        # Massive Buttons (Hit Targets)
        self.btn_pause = ctk.CTkButton(
            self, text="PAUSE / RESUME", font=("Segoe UI", 20, "bold"), 
            height=70, corner_radius=16, fg_color="#eab308", hover_color="#ca8a04", text_color="#0f172a",
            command=self.toggle_pause
        )
        self.btn_pause.pack(fill="x", padx=15, pady=8)

        self.btn_dashboard = ctk.CTkButton(
            self, text="SETTINGS HUB", font=("Segoe UI", 20, "bold"), 
            height=70, corner_radius=16, fg_color="#3b82f6", hover_color="#2563eb",
            command=self.open_dashboard
        )
        self.btn_dashboard.pack(fill="x", padx=15, pady=8)

        self.btn_exit = ctk.CTkButton(
            self, text="EXIT APP", font=("Segoe UI", 20, "bold"), 
            height=70, corner_radius=16, fg_color="#ef4444", hover_color="#dc2626",
            command=self.exit_app
        )
        self.btn_exit.pack(fill="x", padx=15, pady=8)

        self.update_status()

    def toggle_pause(self):
        if self.tracker.paused:
            self.tracker.paused = False
        else:
            self.tracker.paused = True

    def open_dashboard(self):
        self.on_open_dashboard()

    def exit_app(self):
        self.tracker.stop()
        self.master.destroy()
        
    def update_status(self):
        if self.tracker.paused:
            self.status_dot.configure(text_color="#ef4444")
            self.status_text.configure(text="PAUSED")
        else:
            self.status_dot.configure(text_color="#22c55e")
            self.status_text.configure(text="TRACKING")
            
        self.after(200, self.update_status)


class FaceMouseUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.tracking = False
        self.tracker = FaceTracker()

        self.setup_window()
        self.create_layout()
        self.update_preview()
        self.update_live_metrics()
        
        # AUTO-START (Zero-Touch Rule)
        self.start_tracking()

        self.overlay = None

    def setup_window(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("FaceMouse AI Accessibility Hub")
        self.geometry("1600x940")
        self.minsize(1500, 860)
        self.configure(fg_color="#090d16")

        icon_path = "assets/app.ico"
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    def create_layout(self):
        # ---------------- SIDEBAR ----------------
        self.sidebar = ctk.CTkFrame(self, width=340, fg_color="#0d1320", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.logo = ctk.CTkLabel(self.sidebar, text="FaceMouse AI", font=("Segoe UI", 40, "bold"), text_color="#ffffff")
        self.logo.pack(pady=(38, 0))
        self.subtitle = ctk.CTkLabel(self.sidebar, text="Accessibility Edition", font=("Segoe UI", 15), text_color="#7dd3fc")
        self.subtitle.pack(pady=(6, 30))

        self.line = ctk.CTkFrame(self.sidebar, height=2, fg_color="#132033")
        self.line.pack(fill="x", padx=28, pady=(0, 28))

        # Status
        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#111827", corner_radius=24, border_width=1, border_color="#16345f")
        self.status_card.pack(fill="x", padx=24)
        self.status_title = ctk.CTkLabel(self.status_card, text="SYSTEM STATUS", font=("Segoe UI", 14, "bold"), text_color="#38bdf8")
        self.status_title.pack(pady=(22, 12))
        self.status_label = ctk.CTkLabel(self.status_card, text="● TRACKING", font=("Segoe UI", 32, "bold"), text_color="#22c55e")
        self.status_label.pack(pady=(0, 22))

        # Minimize to Overlay Button (Massive Hit Target)
        self.btn_overlay = ctk.CTkButton(
            self.sidebar, 
            text="MINIMIZE TO OVERLAY", 
            height=80, 
            corner_radius=18, 
            fg_color="#8b5cf6", 
            hover_color="#7c3aed", 
            font=("Segoe UI", 18, "bold"), 
            command=self.show_overlay
        )
        self.btn_overlay.pack(fill="x", padx=24, pady=(28, 14))

        # Exit App Button (Massive Hit Target)
        self.btn_exit_main = ctk.CTkButton(
            self.sidebar, 
            text="EXIT APPLICATION", 
            height=60, 
            corner_radius=18, 
            fg_color="#dc2626", 
            hover_color="#b91c1c", 
            font=("Segoe UI", 18, "bold"), 
            command=self.destroy
        )
        self.btn_exit_main.pack(fill="x", padx=24, pady=(0, 14))

        # Live Metrics Card
        self.analytics_card = ctk.CTkFrame(self.sidebar, fg_color="#111827", corner_radius=24, border_width=1, border_color="#16345f")
        self.analytics_card.pack(fill="x", padx=24, pady=28)
        self.analytics_title = ctk.CTkLabel(self.analytics_card, text="LIVE METRICS", font=("Segoe UI", 15, "bold"), text_color="#38bdf8")
        self.analytics_title.pack(pady=(22, 14))

        self.ear_label = ctk.CTkLabel(self.analytics_card, text="Blink Threshold: --", font=("Segoe UI", 14), text_color="#cbd5e1")
        self.ear_label.pack(anchor="w", padx=24)
        
        self.ear_progress = ctk.CTkProgressBar(self.analytics_card, height=12, progress_color="#38bdf8", fg_color="#1e293b")
        self.ear_progress.set(0)
        self.ear_progress.pack(fill="x", padx=24, pady=(5, 15))

        self.pose_label = ctk.CTkLabel(self.analytics_card, text="Yaw: --   |   Pitch: --", font=("Consolas", 14), text_color="#cbd5e1")
        self.pose_label.pack(pady=(0, 22))

        # ---------------- MAIN CONTENT ----------------
        self.main_frame = ctk.CTkFrame(self, fg_color="#090d16")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=22, pady=22)

        # Tab navigation font is larger now for accessibility
        self.tabview = ctk.CTkTabview(
            self.main_frame, corner_radius=24, fg_color="#111827", 
            segmented_button_fg_color="#1e293b", segmented_button_selected_color="#38bdf8", 
            segmented_button_selected_hover_color="#7dd3fc", text_color="#ffffff",
        )
        self.tabview._segmented_button.configure(font=("Segoe UI", 18, "bold"))
        self.tabview.pack(fill="both", expand=True)

        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_settings = self.tabview.add("Advanced Settings")

        # --- Dashboard Tab ---
        self.camera_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="#0d1320", corner_radius=30)
        self.camera_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.camera_title = ctk.CTkLabel(self.camera_frame, text="Neural Camera Feed", font=("Segoe UI", 28, "bold"), text_color="#ffffff")
        self.camera_title.pack(pady=(24, 16))
        self.camera_label = ctk.CTkLabel(self.camera_frame, text="")
        self.camera_label.pack(expand=True, pady=(0, 26))

        # --- Settings Tab ---
        self.settings_container = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        self.settings_container.pack(fill="both", expand=True, padx=50, pady=50)

        ctk.CTkLabel(self.settings_container, text="Advanced Tracking Parameters", font=("Segoe UI", 28, "bold")).pack(anchor="w", pady=(0, 30))

        # Create Accessible settings controls with massive Hit Targets
        self.create_accessible_setting("Cursor Speed (Sensitivity)", 0.5, 5.0, 0.5, self.tracker.sensitivity, self.update_sensitivity)
        self.create_accessible_setting("Smoothing (Lower = Smoother, Higher = Twitchy)", 0.01, 1.0, 0.05, self.tracker.dx_filter.min_cutoff, self.update_smoothing)
        self.create_accessible_setting("Dead Zone (Degrees of freedom)", 0.0, 5.0, 0.5, self.tracker.dead_zone, self.update_dead_zone)

    def create_accessible_setting(self, label_text, min_val, max_val, step, default_val, command):
        frame = ctk.CTkFrame(self.settings_container, fg_color="#0d1320", corner_radius=20)
        frame.pack(fill="x", pady=15)
        
        label = ctk.CTkLabel(frame, text=label_text, font=("Segoe UI", 20))
        label.pack(side="left", padx=25, pady=25)
        
        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(side="right", padx=25)
        
        val_label = ctk.CTkLabel(controls, text=f"{default_val:.2f}", font=("Segoe UI", 24, "bold"), text_color="#38bdf8", width=80)
        
        def decrease():
            current = float(val_label.cget("text"))
            new_val = max(min_val, current - step)
            val_label.configure(text=f"{new_val:.2f}")
            command(new_val)
            
        def increase():
            current = float(val_label.cget("text"))
            new_val = min(max_val, current + step)
            val_label.configure(text=f"{new_val:.2f}")
            command(new_val)

        # Massive Buttons replacing Tiny Sliders
        btn_minus = ctk.CTkButton(controls, text="➖", font=("Segoe UI", 24, "bold"), width=80, height=60, corner_radius=12, fg_color="#334155", hover_color="#475569", command=decrease)
        btn_minus.pack(side="left", padx=10)
        
        val_label.pack(side="left", padx=15)
        
        btn_plus = ctk.CTkButton(controls, text="➕", font=("Segoe UI", 24, "bold"), width=80, height=60, corner_radius=12, fg_color="#334155", hover_color="#475569", command=increase)
        btn_plus.pack(side="left", padx=10)

    def update_sensitivity(self, val):
        self.tracker.sensitivity = val

    def update_smoothing(self, val):
        self.tracker.dx_filter.min_cutoff = val
        self.tracker.dy_filter.min_cutoff = val

    def update_dead_zone(self, val):
        self.tracker.dead_zone = val

    def start_tracking(self):
        if not self.tracking:
            self.tracking = True
            self.tracker.start("full")

    def show_overlay(self):
        # Withdraw main window and show overlay
        self.withdraw()
        if self.overlay is None or not self.overlay.winfo_exists():
            self.overlay = FloatingOverlay(self, self.tracker, self.show_dashboard)
        else:
            self.overlay.deiconify()

    def show_dashboard(self):
        # Hide overlay and restore main window
        if self.overlay is not None:
            self.overlay.withdraw()
        self.deiconify()

    def update_live_metrics(self):
        if self.tracking and self.tracker.calibrated:
            ear = self.tracker.current_ear
            thresh = self.tracker.blink_threshold
            
            self.ear_label.configure(text=f"EAR: {ear:.3f} (Thresh: {thresh:.3f})")
            prog = max(0.0, min(1.0, (ear - 0.10) / 0.30))
            self.ear_progress.set(prog)
            
            if ear < thresh:
                self.ear_progress.configure(progress_color="#ef4444")
            else:
                self.ear_progress.configure(progress_color="#38bdf8")

            yaw = self.tracker.current_yaw
            pitch = self.tracker.current_pitch
            self.pose_label.configure(text=f"Yaw: {yaw:5.1f}°   |   Pitch: {pitch:5.1f}°")
            
            if self.tracker.paused:
                self.status_label.configure(text="● PAUSED", text_color="#ef4444")
            else:
                self.status_label.configure(text="● TRACKING", text_color="#22c55e")
                
        elif not self.tracking:
            self.ear_label.configure(text="Blink Threshold: --")
            self.ear_progress.set(0)
            self.ear_progress.configure(progress_color="#38bdf8")
            self.pose_label.configure(text="Yaw: --   |   Pitch: --")

        self.after(50, self.update_live_metrics)

    def update_preview(self):
        frame = self.tracker.latest_frame
        if frame is not None:
            image = Image.fromarray(frame)
            image = image.resize((1024, 680))
            photo = ImageTk.PhotoImage(image=image)
            self.camera_label.configure(image=photo)
            self.camera_label.image = photo

        self.after(30, self.update_preview)

if __name__ == "__main__":
    app = FaceMouseUI()
    app.mainloop()