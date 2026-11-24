"""
Passport & Photo Print Sheet Arranger Pro (Portable Edition)
made by : Jaimin Rabari Mo.9574782643

Professional GUI application with:
- Government & International Visa/Passport Presets (India 35x45mm, US Visa 2x2", Schengen, Canada, Stamp)
- Name & Date of Photo (DOP) Stamp for Indian Government Exams (UPSC, SSC, Railway, Police)
- 100% Offline AI/GrabCut Background Replacement (Pure White, Sky Blue, Light Grey, Custom)
- Direct Windows Printer Dialog with mandatory 4x6 inch inkjet photo paper support & driver properties
- Single-degree precision photo rotation slider (-180° to +180°)
- Expandable / Collapsible accordion sections keeping UI spacious and uncluttered
- Brightness, contrast, saturation, and sharpness enhancement tools
- Inter-photo spacing & scissor cutting guides
- Multi-paper size engine (4×6″, 8×12″, 5×7″, 8×10″, A4)
"""

import os
import sys
import math
import tempfile
import datetime
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageOps, ImageEnhance, ImageFont, ImageFilter, ImageWin
import cv2
import numpy as np

# Windows Printing support via pywin32
try:
    import win32print
    import win32ui
    import win32con
    import win32api
    WIN32_PRINT_AVAILABLE = True
except ImportError:
    WIN32_PRINT_AVAILABLE = False

# Set CustomTkinter theme - DEDICATED LIGHT MODE ONLY
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class ProfessionalPhotoEditor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Passport & Photo Print Sheet Arranger Pro - by Jaimin Rabari")
        self.geometry("1380x870")
        self.minsize(1160, 740)

        # Set App Window & Taskbar Icon
        try:
            icon_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
            if os.path.exists(icon_file):
                self.iconbitmap(icon_file)
        except Exception:
            pass

        # State Variables
        self.base_image = None           # Clean loaded image (EXIF-transposed)
        self.rotated_image = None        # Rotated PIL Image
        self.working_image = None        # Rotated + BG Replaced PIL Image
        self.original_image = None       # Alias used for crop canvas coordinates
        self.display_image = None        # Scaled PIL Image for crop canvas
        self.cropped_photo = None        # Resulting cropped PIL Image
        self.sheet_image = None          # Resulting print sheet PIL Image

        # Crop Geometry (Normalized to 0.0 - 1.0 of original image)
        self.crop_norm_x = 0.1
        self.crop_norm_y = 0.1
        self.crop_norm_w = 0.6
        self.crop_norm_h = 0.8
        self.drag_mode = None            # None, "move", "nw", "ne", "sw", "se"
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.orig_crop_rect = None
        self.canvas_scale = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0

        # Feature 1: Government & International Visa/Passport Presets
        self.PHOTO_PRESETS = {
            "Standard (1.5″ × 2″ / 3:4)": {
                "ratio": 1.5 / 2.0, "w_in": 1.5, "h_in": 2.0, "w_mm": 38.1, "h_mm": 50.8,
                "label": "1.5″ × 2″ (38×51 mm)", "cols_4x6": 4, "rows_4x6": 2, "cols_8x12": 8, "rows_8x12": 4
            },
            "India Passport / PAN / OCI (35×45 mm)": {
                "ratio": 35.0 / 45.0, "w_in": 35.0 / 25.4, "h_in": 45.0 / 25.4, "w_mm": 35.0, "h_mm": 45.0,
                "label": "35×45 mm (India Passport/PAN)", "cols_4x6": 4, "rows_4x6": 2, "cols_8x12": 8, "rows_8x12": 4
            },
            "US Visa / Passport (2″ × 2″ Square)": {
                "ratio": 1.0, "w_in": 2.0, "h_in": 2.0, "w_mm": 50.8, "h_mm": 50.8,
                "label": "2″ × 2″ Square (51×51 mm)", "cols_4x6": 3, "rows_4x6": 2, "cols_8x12": 6, "rows_8x12": 4
            },
            "Schengen / UK Visa (35×45 mm)": {
                "ratio": 35.0 / 45.0, "w_in": 35.0 / 25.4, "h_in": 45.0 / 25.4, "w_mm": 35.0, "h_mm": 45.0,
                "label": "35×45 mm (Schengen/UK)", "cols_4x6": 4, "rows_4x6": 2, "cols_8x12": 8, "rows_8x12": 4
            },
            "Canada Visa (50×70 mm)": {
                "ratio": 50.0 / 70.0, "w_in": 50.0 / 25.4, "h_in": 70.0 / 25.4, "w_mm": 50.0, "h_mm": 70.0,
                "label": "50×70 mm (Canada)", "cols_4x6": 2, "rows_4x6": 2, "cols_8x12": 4, "rows_8x12": 4
            },
            "Stamp / Token Size (25×30 mm)": {
                "ratio": 25.0 / 30.0, "w_in": 25.0 / 25.4, "h_in": 30.0 / 25.4, "w_mm": 25.0, "h_mm": 30.0,
                "label": "25×30 mm (Stamp / ID)", "cols_4x6": 5, "rows_4x6": 3, "cols_8x12": 10, "rows_8x12": 6
            }
        }
        self.selected_photo_preset = ctk.StringVar(value="Standard (1.5″ × 2″ / 3:4)")

        # Feature 2: Name & Date of Photo (DOP) Stamp for Govt Exams
        self.dop_enabled = ctk.BooleanVar(value=False)
        self.dop_name = ctk.StringVar(value="CANDIDATE NAME")
        today_str = datetime.date.today().strftime("%d/%m/%Y")
        self.dop_date = ctk.StringVar(value=f"DOP: {today_str}")

        # Feature 3: Offline Background Replacement / Remover
        self.bg_mode = ctk.StringVar(value="original")  # original, white, blue, grey, custom
        self.bg_custom_color = "#FFFFFF"
        self.cached_fg_mask = None  # Cache GrabCut mask for fast color switching


        # Rotation state (single degree precision)
        self.rotate_angle_var = ctk.DoubleVar(value=0.0)  # -180° to +180°

        # Photo Touch & Color Enhancement Settings
        self.brightness_var = ctk.DoubleVar(value=0.0)    # -50 to +50
        self.contrast_var = ctk.DoubleVar(value=0.0)      # -50 to +50
        self.saturation_var = ctk.DoubleVar(value=0.0)    # -50 to +50
        self.sharpness_var = ctk.DoubleVar(value=0.0)     # 0 to 50

        # Border Settings
        self.border_enabled = ctk.BooleanVar(value=True)
        self.border_width = ctk.IntVar(value=4)          # In pixels relative to 300 DPI
        self.border_color = "#FFFFFF"                     # Default crisp white

        # Spacing / Gap & Margin Settings (for physical cutting)
        self.gap_mm = ctk.DoubleVar(value=2.0)            # Inter-photo space in mm (0 to 6)
        self.margin_mm = ctk.DoubleVar(value=2.0)         # Outer sheet margin in mm (0 to 6)

        # Paper Size Presets
        self.PAPER_PRESETS = {
            "4 × 6 inch (8 Photos)": {"w": 6.0, "h": 4.0, "cols": 4, "rows": 2, "label": "4×6″ (8 Photos)"},
            "8 × 12 inch (32 Photos)": {"w": 12.0, "h": 8.0, "cols": 8, "rows": 4, "label": "8×12″ (32 Photos)"},
            "8 × 10 inch (20 Photos)": {"w": 10.0, "h": 8.0, "cols": 5, "rows": 4, "label": "8×10″ (20 Photos)"},
            "5 × 7 inch (8 Photos)": {"w": 7.0, "h": 5.0, "cols": 4, "rows": 2, "label": "5×7″ (8 Photos)"},
            "A4 Sheet (28 Photos)": {"w": 11.69, "h": 8.27, "cols": 7, "rows": 4, "label": "A4 (28 Photos)"},
        }
        self.selected_paper = ctk.StringVar(value="4 × 6 inch (8 Photos)")

        # Guides & Print Resolution
        self.cut_guides_enabled = ctk.BooleanVar(value=True)
        self.cut_guide_color = "#B0B0B0"
        self.dpi_selection = ctk.IntVar(value=300)        # 300 or 600

        # Color presets for borders & backgrounds
        self.color_presets = [
            ("#FFFFFF", "White"),
            ("#F1F5F9", "Off-White"),
            ("#CBD5E1", "Light Gray"),
            ("#475569", "Slate"),
            ("#0F172A", "Black"),
            ("#1E3A8A", "Navy Blue"),
            ("#B91C1C", "Red"),
            ("#D97706", "Gold"),
        ]

        self._build_header()
        self._build_main_layout()

    # -------------------------------------------------------------
    # UI Layout Construction (LIGHT MODE - SPACIOUS & CLEAN)
    # -------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(
            self,
            height=58,
            corner_radius=0,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#E2E8F0"
        )
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Left: App Icon & Title
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side=tk.LEFT, padx=16, pady=8)

        icon_lbl = ctk.CTkLabel(title_box, text="📸", font=ctk.CTkFont(size=22))
        icon_lbl.pack(side=tk.LEFT, padx=(0, 8))

        title_lbl = ctk.CTkLabel(
            title_box,
            text="Photo Arranger Pro",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#0F172A"
        )
        title_lbl.pack(side=tk.LEFT)

        # Center beside title: "made by : Jaimin Rabari Mo.9574782643" (BOLD)
        credit_box = ctk.CTkFrame(
            header,
            fg_color="#EFF6FF",
            corner_radius=8,
            border_width=1,
            border_color="#BFDBFE"
        )
        credit_box.pack(side=tk.LEFT, padx=(20, 16), pady=8)

        credit_lbl = ctk.CTkLabel(
            credit_box,
            text="made by : Jaimin Rabari Mo.9574782643",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1D4ED8"
        )
        credit_lbl.pack(padx=14, pady=4)

        # Right: Specification Subtitle
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side=tk.RIGHT, padx=16)

        spec_lbl = ctk.CTkLabel(
            right_box,
            text="Passport & Visa Studio Print Engine",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64748B"
        )
        spec_lbl.pack(side=tk.RIGHT)

    def _build_main_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 1. Left Sidebar: Settings & Controls (Scrollable accordion layout)
        self.sidebar = ctk.CTkScrollableFrame(container, width=350, corner_radius=12, fg_color="#FFFFFF")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self._build_sidebar_controls()

        # 2. Main Content Split View: Center (Interactive Crop) and Right (Live Sheet Preview)
        self.content_view = ctk.CTkFrame(container, corner_radius=12, fg_color="transparent")
        self.content_view.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.content_view.grid_columnconfigure(0, weight=1)
        self.content_view.grid_columnconfigure(1, weight=1)
        self.content_view.grid_rowconfigure(0, weight=1)

        # Stage 1: Crop Studio (Center)
        crop_card = ctk.CTkFrame(self.content_view, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        crop_card.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        self._build_crop_panel(crop_card)

        # Stage 2: Sheet Live Preview (Right)
        preview_card = ctk.CTkFrame(self.content_view, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0")
        preview_card.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        self._build_preview_panel(preview_card)

    def _create_accordion_section(self, parent, title_text, is_open=False):
        """Creates a modern collapsible accordion section with comfortable inner padding."""
        sec_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sec_frame.pack(fill=tk.X, pady=(0, 6))

        arrow = "▼" if is_open else "▶"
        header_btn = ctk.CTkButton(
            sec_frame,
            text=f"{arrow}  {title_text}",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            anchor="w",
            fg_color="#F8FAFC",
            text_color="#0F172A",
            hover_color="#F1F5F9",
            border_width=1,
            border_color="#CBD5E1",
            corner_radius=8
        )
        header_btn.pack(fill=tk.X)

        content_box = ctk.CTkFrame(
            sec_frame,
            fg_color="#FFFFFF",
            corner_radius=8,
            border_width=1,
            border_color="#E2E8F0"
        )
        content_frame = ctk.CTkFrame(content_box, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        state = {"open": is_open}

        def toggle():
            if state["open"]:
                content_box.pack_forget()
                header_btn.configure(text=f"▶  {title_text}", fg_color="#F8FAFC")
                state["open"] = False
            else:
                content_box.pack(fill=tk.X, pady=(4, 0))
                header_btn.configure(text=f"▼  {title_text}", fg_color="#EFF6FF")
                state["open"] = True

        header_btn.configure(command=toggle)

        if is_open:
            header_btn.configure(fg_color="#EFF6FF")
            content_box.pack(fill=tk.X, pady=(4, 0))

        return content_frame

    def _build_sidebar_controls(self):
        # =========================================================
        # Section 1: Photo Source & Straighten Rotation (Always Open)
        # =========================================================
        s1_title = ctk.CTkLabel(self.sidebar, text="1. Photo Source & Rotation", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0F172A")
        s1_title.pack(anchor="w", pady=(4, 6))

        # Photo Source Buttons (Choose File + Webcam Capture)
        btn_src_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_src_row.pack(fill=tk.X, pady=(0, 4))

        btn_open = ctk.CTkButton(
            btn_src_row,
            text="📂 Choose File...",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.load_image
        )
        btn_open.pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)

        btn_webcam = ctk.CTkButton(
            btn_src_row,
            text="📷 Take Photo...",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            command=self.open_webcam_dialog
        )
        btn_webcam.pack(side=tk.LEFT, padx=(3, 0), expand=True, fill=tk.X)

        self.lbl_photo_status = ctk.CTkLabel(
            self.sidebar,
            text="No photo loaded yet",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=320,
            justify="left"
        )
        self.lbl_photo_status.pack(anchor="w", pady=(0, 8))

        # Precision Rotation Slider (-180° to +180° in 1° steps)
        rot_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        rot_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(rot_row, text="📐 Straighten / Rotate:", font=ctk.CTkFont(size=12, weight="bold")).pack(side=tk.LEFT)
        self.lbl_rotate_val = ctk.CTkLabel(rot_row, text="0°", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_rotate_val.pack(side=tk.RIGHT)

        self.slider_rotate = ctk.CTkSlider(
            self.sidebar,
            from_=-180, to=180,
            number_of_steps=360,
            variable=self.rotate_angle_var,
            command=self._on_rotate_slider
        )
        self.slider_rotate.pack(fill=tk.X, pady=(0, 6))

        # Quick Rotation & Reset Buttons
        rotate_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        rotate_row.pack(fill=tk.X, pady=(0, 10))

        btn_rot_ccw = ctk.CTkButton(
            rotate_row, text="↺ -90°", width=68, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.step_rotation(-90)
        )
        btn_rot_ccw.pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)

        btn_rot_zero = ctk.CTkButton(
            rotate_row, text="0° Reset", width=72, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=self.reset_rotation
        )
        btn_rot_zero.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        btn_rot_cw = ctk.CTkButton(
            rotate_row, text="↻ +90°", width=68, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.step_rotation(90)
        )
        btn_rot_cw.pack(side=tk.LEFT, padx=(3, 3), expand=True, fill=tk.X)

        btn_reset_crop = ctk.CTkButton(
            rotate_row, text="↺ Crop", width=60, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=self.reset_crop_box
        )
        btn_reset_crop.pack(side=tk.LEFT, padx=(0, 0))

        self._add_separator(self.sidebar)

        # =========================================================
        # Section 2: Passport & Visa Presets (Open by Default)
        # =========================================================
        sec_preset = self._create_accordion_section(self.sidebar, "2. Passport & Visa Presets", is_open=True)

        ctk.CTkLabel(
            sec_preset,
            text="Official dimensions & aspect ratios for IDs and visas:",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(anchor="w", pady=(0, 4))

        self.preset_menu = ctk.CTkOptionMenu(
            sec_preset,
            values=list(self.PHOTO_PRESETS.keys()),
            variable=self.selected_photo_preset,
            command=self._on_photo_preset_change,
            height=30
        )
        self.preset_menu.pack(fill=tk.X, pady=(0, 6))

        self.lbl_preset_detail = ctk.CTkLabel(
            sec_preset,
            text="Standard 1.5″ × 2″ (38.1 × 50.8 mm) • 3:4 Ratio",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1D4ED8"
        )
        self.lbl_preset_detail.pack(anchor="w", pady=(0, 4))

        # =========================================================
        # Section 3: Offline Background Replacement (Closed by Default)
        # =========================================================
        sec_bg = self._create_accordion_section(self.sidebar, "3. Background Color (Offline)", is_open=False)

        ctk.CTkLabel(
            sec_bg,
            text="Replace background 100% offline with official studio colors:",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=310,
            justify="left"
        ).pack(anchor="w", pady=(0, 6))

        # Row 1: Original & Pure White (2 buttons)
        bg_btn_row1 = ctk.CTkFrame(sec_bg, fg_color="transparent")
        bg_btn_row1.pack(fill=tk.X, pady=(0, 4))

        ctk.CTkButton(
            bg_btn_row1, text="↺ Original", height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#F1F5F9", text_color="#0F172A", hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.set_background_color("original")
        ).pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)

        ctk.CTkButton(
            bg_btn_row1, text="⚪ Pure White", height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#FFFFFF", text_color="#0F172A", hover_color="#F8FAFC",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.set_background_color("#FFFFFF")
        ).pack(side=tk.LEFT, padx=(3, 0), expand=True, fill=tk.X)

        # Row 2: Sky Blue & Light Grey (2 buttons)
        bg_btn_row2 = ctk.CTkFrame(sec_bg, fg_color="transparent")
        bg_btn_row2.pack(fill=tk.X, pady=(0, 4))

        ctk.CTkButton(
            bg_btn_row2, text="🔵 Sky Blue", height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#E0F2FE", text_color="#0369A1", hover_color="#BAE6FD",
            border_width=1, border_color="#7DD3FC",
            command=lambda: self.set_background_color("#87CEEB")
        ).pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)

        ctk.CTkButton(
            bg_btn_row2, text="🔘 Light Grey", height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#F1F5F9", text_color="#334155", hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.set_background_color("#E2E8F0")
        ).pack(side=tk.LEFT, padx=(3, 0), expand=True, fill=tk.X)

        # Row 3: Custom Color Picker (Full Width, never cramped!)
        ctk.CTkButton(
            sec_bg, text="🎨 Choose Custom Studio Color...", height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#F8FAFC", text_color="#0F172A", hover_color="#F1F5F9",
            border_width=1, border_color="#CBD5E1",
            command=self.choose_custom_background
        ).pack(fill=tk.X, pady=(2, 6))

        self.lbl_bg_status = ctk.CTkLabel(
            sec_bg,
            text="Current Background: Original photo",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.lbl_bg_status.pack(anchor="w", pady=(0, 2))

        # =========================================================
        # Section 4: Name & Date Stamp (Govt Exams) (Closed by Default)
        # =========================================================
        sec_dop = self._create_accordion_section(self.sidebar, "4. Name & Date Stamp (Govt Exams)", is_open=False)

        dop_switch = ctk.CTkSwitch(
            sec_dop,
            text="Enable Bottom Name & Date Bar",
            variable=self.dop_enabled,
            command=self.update_sheet,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        dop_switch.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            sec_dop,
            text="Mandatory format for UPSC, SSC, Railway, State Police & Exams:",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=310,
            justify="left"
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(sec_dop, text="Candidate Full Name:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        entry_name = ctk.CTkEntry(sec_dop, textvariable=self.dop_name, height=28)
        entry_name.pack(fill=tk.X, pady=(2, 6))
        entry_name.bind("<KeyRelease>", lambda e: self.update_sheet())

        ctk.CTkLabel(sec_dop, text="Date of Photo (DOP):", font=ctk.CTkFont(size=11)).pack(anchor="w")
        entry_date = ctk.CTkEntry(sec_dop, textvariable=self.dop_date, height=28)
        entry_date.pack(fill=tk.X, pady=(2, 4))
        entry_date.bind("<KeyRelease>", lambda e: self.update_sheet())

        # =========================================================
        # Section 5: Photo Touch & Color Correction (Open by Default)
        # =========================================================
        sec_touch = self._create_accordion_section(self.sidebar, "5. Photo Touch & Color", is_open=True)

        touch_desc = ctk.CTkLabel(
            sec_touch,
            text="Fine-tune lighting, skin tones, and sharpness for crisp prints:",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=310,
            justify="left"
        )
        touch_desc.pack(anchor="w", pady=(0, 6))

        # Brightness
        b_row = ctk.CTkFrame(sec_touch, fg_color="transparent")
        b_row.pack(fill=tk.X, pady=(0, 1))
        ctk.CTkLabel(b_row, text="☀️ Brightness:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_brightness_val = ctk.CTkLabel(b_row, text="0%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_brightness_val.pack(side=tk.RIGHT)

        self.slider_brightness = ctk.CTkSlider(
            sec_touch,
            from_=-50, to=50,
            number_of_steps=100,
            variable=self.brightness_var,
            command=self._on_enhancement_change
        )
        self.slider_brightness.pack(fill=tk.X, pady=(0, 6))

        # Contrast
        c_row = ctk.CTkFrame(sec_touch, fg_color="transparent")
        c_row.pack(fill=tk.X, pady=(0, 1))
        ctk.CTkLabel(c_row, text="🌓 Contrast:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_contrast_val = ctk.CTkLabel(c_row, text="0%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_contrast_val.pack(side=tk.RIGHT)

        self.slider_contrast = ctk.CTkSlider(
            sec_touch,
            from_=-50, to=50,
            number_of_steps=100,
            variable=self.contrast_var,
            command=self._on_enhancement_change
        )
        self.slider_contrast.pack(fill=tk.X, pady=(0, 6))

        # Saturation
        s_row = ctk.CTkFrame(sec_touch, fg_color="transparent")
        s_row.pack(fill=tk.X, pady=(0, 1))
        ctk.CTkLabel(s_row, text="🎨 Saturation:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_saturation_val = ctk.CTkLabel(s_row, text="0%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_saturation_val.pack(side=tk.RIGHT)

        self.slider_saturation = ctk.CTkSlider(
            sec_touch,
            from_=-50, to=50,
            number_of_steps=100,
            variable=self.saturation_var,
            command=self._on_enhancement_change
        )
        self.slider_saturation.pack(fill=tk.X, pady=(0, 6))

        # Sharpness
        sh_row = ctk.CTkFrame(sec_touch, fg_color="transparent")
        sh_row.pack(fill=tk.X, pady=(0, 1))
        ctk.CTkLabel(sh_row, text="🔍 Sharpness:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_sharpness_val = ctk.CTkLabel(sh_row, text="0", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_sharpness_val.pack(side=tk.RIGHT)

        self.slider_sharpness = ctk.CTkSlider(
            sec_touch,
            from_=0, to=50,
            number_of_steps=50,
            variable=self.sharpness_var,
            command=self._on_enhancement_change
        )
        self.slider_sharpness.pack(fill=tk.X, pady=(0, 8))

        # Quick Actions
        touch_btn_row = ctk.CTkFrame(sec_touch, fg_color="transparent")
        touch_btn_row.pack(fill=tk.X, pady=(0, 2))

        btn_auto = ctk.CTkButton(
            touch_btn_row, text="✨ Auto Studio Touch", height=28,
            fg_color="#EFF6FF", text_color="#1D4ED8", hover_color="#DBEAFE",
            border_width=1, border_color="#BFDBFE",
            command=self.auto_enhance
        )
        btn_auto.pack(side=tk.LEFT, padx=(0, 4), expand=True, fill=tk.X)

        btn_reset_touch = ctk.CTkButton(
            touch_btn_row, text="↺ Reset", width=70, height=28,
            fg_color="#F1F5F9", text_color="#0F172A", hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=self.reset_enhancements
        )
        btn_reset_touch.pack(side=tk.LEFT, padx=(4, 0))

        # =========================================================
        # Section 6: Border Settings (Closed by Default)
        # =========================================================
        sec_border = self._create_accordion_section(self.sidebar, "6. Photo Border Settings", is_open=False)

        border_switch = ctk.CTkSwitch(
            sec_border,
            text="Draw Photo Border",
            variable=self.border_enabled,
            command=self.update_sheet,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        border_switch.pack(anchor="w", pady=(0, 8))

        bw_row = ctk.CTkFrame(sec_border, fg_color="transparent")
        bw_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(bw_row, text="Border Width:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_border_val = ctk.CTkLabel(bw_row, text="4 px", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_border_val.pack(side=tk.RIGHT)

        self.slider_border = ctk.CTkSlider(
            sec_border, from_=1, to=16, number_of_steps=15,
            variable=self.border_width, command=self._on_border_slider
        )
        self.slider_border.pack(fill=tk.X, pady=(0, 8))

        ctk.CTkLabel(sec_border, text="Border Color Palette:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        palette_frame = ctk.CTkFrame(sec_border, fg_color="transparent")
        palette_frame.pack(fill=tk.X, pady=(0, 6))

        for color_hex, label in self.color_presets[:6]:
            btn = ctk.CTkButton(
                palette_frame, text="", width=24, height=24,
                fg_color=color_hex, hover_color=color_hex,
                border_width=1, border_color="#94A3B8", corner_radius=6,
                command=lambda c=color_hex: self.set_border_color(c)
            )
            btn.pack(side=tk.LEFT, padx=3)

        custom_btn = ctk.CTkButton(
            palette_frame, text="🎨 Pick...", width=60, height=24,
            font=ctk.CTkFont(size=11), fg_color="#F1F5F9", text_color="#0F172A",
            border_width=1, border_color="#CBD5E1", hover_color="#E2E8F0",
            command=self.choose_custom_color
        )
        custom_btn.pack(side=tk.LEFT, padx=4)

        # =========================================================
        # Section 7: Spacing & Margin Settings (Closed by Default)
        # =========================================================
        sec_space = self._create_accordion_section(self.sidebar, "7. Spacing & Margin Settings", is_open=False)

        spacing_desc = ctk.CTkLabel(
            sec_space,
            text="Adds space between photos for clean scissor cutting corridors:",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=310,
            justify="left"
        )
        spacing_desc.pack(anchor="w", pady=(0, 6))

        gap_row = ctk.CTkFrame(sec_space, fg_color="transparent")
        gap_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(gap_row, text="Space Between Photos:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_gap_val = ctk.CTkLabel(gap_row, text="2.0 mm", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_gap_val.pack(side=tk.RIGHT)

        self.slider_gap = ctk.CTkSlider(
            sec_space, from_=0.0, to=6.0, number_of_steps=12,
            variable=self.gap_mm, command=self._on_gap_slider
        )
        self.slider_gap.pack(fill=tk.X, pady=(0, 6))

        margin_row = ctk.CTkFrame(sec_space, fg_color="transparent")
        margin_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(margin_row, text="Outer Edge Margin:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_margin_val = ctk.CTkLabel(margin_row, text="2.0 mm", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_margin_val.pack(side=tk.RIGHT)

        self.slider_margin = ctk.CTkSlider(
            sec_space, from_=0.0, to=6.0, number_of_steps=12,
            variable=self.margin_mm, command=self._on_margin_slider
        )
        self.slider_margin.pack(fill=tk.X, pady=(0, 6))

        # =========================================================
        # Section 8: Paper Size & Resolution (Open by Default)
        # =========================================================
        sec_paper = self._create_accordion_section(self.sidebar, "8. Paper Size & Resolution", is_open=True)

        paper_row = ctk.CTkFrame(sec_paper, fg_color="transparent")
        paper_row.pack(fill=tk.X, pady=(0, 8))
        ctk.CTkLabel(paper_row, text="Paper Layout:", font=ctk.CTkFont(size=12, weight="bold")).pack(side=tk.LEFT)

        paper_menu = ctk.CTkOptionMenu(
            paper_row,
            values=list(self.PAPER_PRESETS.keys()),
            variable=self.selected_paper,
            command=self._on_paper_change,
            width=180,
            height=28
        )
        paper_menu.pack(side=tk.RIGHT)

        cut_switch = ctk.CTkSwitch(
            sec_paper,
            text="Scissor Cut Guides (Dashed)",
            variable=self.cut_guides_enabled,
            command=self.update_sheet,
            font=ctk.CTkFont(size=12)
        )
        cut_switch.pack(anchor="w", pady=(0, 8))

        dpi_row = ctk.CTkFrame(sec_paper, fg_color="transparent")
        dpi_row.pack(fill=tk.X, pady=(0, 4))
        ctk.CTkLabel(dpi_row, text="Print Quality:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)

        dpi_seg = ctk.CTkSegmentedButton(
            dpi_row,
            values=["300 DPI (HD)", "600 DPI (Ultra)"],
            command=self._on_dpi_change,
            height=28
        )
        dpi_seg.set("300 DPI (HD)")
        dpi_seg.pack(side=tk.RIGHT)

        self.lbl_photo_dims = ctk.CTkLabel(
            sec_paper,
            text="Photo: 1.50″ × 2.00″ (38.1 × 50.8 mm) | 3:4",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1E3A8A"
        )
        self.lbl_photo_dims.pack(anchor="w", pady=(4, 1))

        self.lbl_dpi_info = ctk.CTkLabel(
            sec_paper,
            text="Canvas: 1800 × 1200 px @ 300 DPI (4×6″)",
            font=ctk.CTkFont(size=10),
            text_color="#64748B",
            justify="left"
        )
        self.lbl_dpi_info.pack(anchor="w", pady=(0, 2))

        self._add_separator(self.sidebar)

        # =========================================================
        # Primary Action Buttons: Export JPG & Direct Print
        # =========================================================
        self.btn_export = ctk.CTkButton(
            self.sidebar,
            text="💾  Export 4×6 Sheet (JPG)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color="#16A34A",
            hover_color="#15803D",
            command=self.export_sheet_jpg
        )
        self.btn_export.pack(fill=tk.X, pady=(2, 4))
        self.btn_export.configure(state="disabled")

        self.btn_direct_print = ctk.CTkButton(
            self.sidebar,
            text="🖨️  Direct Print Sheet (4×6″ Inkjet)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.open_direct_print_dialog
        )
        self.btn_direct_print.pack(fill=tk.X, pady=(2, 6))
        self.btn_direct_print.configure(state="disabled")

        self.lbl_export_tip = ctk.CTkLabel(
            self.sidebar,
            text="Tip: For inkjet printing, choose 'Actual Size / 100%' and 'Premium Glossy' paper in printer preferences for razor-sharp studio quality.",
            font=ctk.CTkFont(size=10),
            text_color="#64748B",
            wraplength=320,
            justify="left"
        )
        self.lbl_export_tip.pack(anchor="w", pady=(0, 4))

    def _add_separator(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color="#E2E8F0")
        sep.pack(fill=tk.X, pady=8)

    # -------------------------------------------------------------
    # Crop Studio Panel (Stage 1)
    # -------------------------------------------------------------
    def _build_crop_panel(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        top_bar.pack(fill=tk.X, padx=12, pady=(10, 4))

        lbl_title = ctk.CTkLabel(top_bar, text="① Interactive Crop Studio", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0F172A")
        lbl_title.pack(side=tk.LEFT)

        self.lbl_crop_ratio_badge = ctk.CTkLabel(
            top_bar,
            text="Aspect: 3:4 (1.5″ × 2″)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#2563EB"
        )
        self.lbl_crop_ratio_badge.pack(side=tk.RIGHT)

        self.crop_canvas = tk.Canvas(
            parent,
            bg="#E2E8F0",
            highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.crop_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.crop_canvas.bind("<Configure>", lambda e: self.render_crop_canvas())
        self.crop_canvas.bind("<ButtonPress-1>", self._on_crop_press)
        self.crop_canvas.bind("<B1-Motion>", self._on_crop_drag)
        self.crop_canvas.bind("<ButtonRelease-1>", self._on_crop_release)
        self.crop_canvas.bind("<Motion>", self._on_crop_hover)

    # -------------------------------------------------------------
    # Print Sheet Live Preview Panel (Stage 2)
    # -------------------------------------------------------------
    def _build_preview_panel(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        top_bar.pack(fill=tk.X, padx=12, pady=(10, 4))

        self.lbl_preview_title = ctk.CTkLabel(top_bar, text="② Live Print Sheet Preview", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0F172A")
        self.lbl_preview_title.pack(side=tk.LEFT)

        self.lbl_sheet_badge = ctk.CTkLabel(
            top_bar,
            text="8 Photos (4 Col × 2 Row)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#16A34A"
        )
        self.lbl_sheet_badge.pack(side=tk.RIGHT)

        self.preview_canvas = tk.Canvas(
            parent,
            bg="#E2E8F0",
            highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.preview_canvas.bind("<Configure>", lambda e: self.render_sheet_preview())

    # -------------------------------------------------------------
    # Feature 1: Preset Handler
    # -------------------------------------------------------------
    def _on_photo_preset_change(self, preset_name):
        cfg = self.PHOTO_PRESETS.get(preset_name, self.PHOTO_PRESETS["Standard (1.5″ × 2″ / 3:4)"])
        self.lbl_preset_detail.configure(text=f"{cfg['label']} • Ratio: {cfg['ratio']:.2f}")
        self.lbl_crop_ratio_badge.configure(text=f"Aspect: {cfg['label'].split('(')[0].strip()}")
        self.reset_crop_box()

    def get_current_crop_ratio(self):
        cfg = self.PHOTO_PRESETS.get(self.selected_photo_preset.get(), self.PHOTO_PRESETS["Standard (1.5″ × 2″ / 3:4)"])
        return cfg["ratio"]

    # -------------------------------------------------------------
    # Feature 3: Offline AI / GrabCut Background Removal
    # -------------------------------------------------------------
    def set_background_color(self, color_choice):
        self.bg_mode.set(color_choice)
        if color_choice == "original":
            self.lbl_bg_status.configure(text="Current Background: Original photo")
        elif color_choice == "#FFFFFF":
            self.lbl_bg_status.configure(text="Current Background: Pure Studio White")
        elif color_choice == "#87CEEB":
            self.lbl_bg_status.configure(text="Current Background: Sky Blue (Exam/School)")
        elif color_choice == "#E2E8F0":
            self.lbl_bg_status.configure(text="Current Background: Light Grey (Visa)")
        else:
            self.lbl_bg_status.configure(text=f"Current Background: Custom ({color_choice})")

        self.apply_working_pipeline()

    def choose_custom_background(self):
        color = colorchooser.askcolor(color=self.bg_custom_color, title="Choose Custom Background Color")
        if color and color[1]:
            self.bg_custom_color = color[1]
            self.set_background_color(color[1])

    def compute_foreground_mask(self, cv_img):
        """Computes offline foreground segmentation mask using OpenCV GrabCut."""
        h, w = cv_img.shape[:2]
        # Margin for foreground assumption
        mx = max(4, int(w * 0.05))
        my = max(4, int(h * 0.04))
        rect = (mx, my, w - 2 * mx, h - 2 * my)

        mask = np.zeros((h, w), np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)

        try:
            cv2.grabCut(cv_img, mask, rect, bgdModel, fgdModel, iterCount=3, mode=cv2.GC_INIT_WITH_RECT)
            fg_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
            # Feather edge slightly with Gaussian blur for natural hair/shoulders
            fg_mask = cv2.GaussianBlur(fg_mask, (5, 5), 0)
            return fg_mask
        except Exception as e:
            print("GrabCut error:", e)
            return None

    # -------------------------------------------------------------
    # Central Image Processing Pipeline
    # -------------------------------------------------------------
    def apply_working_pipeline(self):
        """Builds self.original_image from base_image -> rotation -> bg removal."""
        if not self.base_image:
            return

        # 1. Rotation
        angle = int(round(self.rotate_angle_var.get()))
        if angle == 0:
            current = self.base_image.copy()
        else:
            current = self.base_image.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True)

        self.rotated_image = current.copy()

        # 2. Background Replacement (Offline)
        bg_mode = self.bg_mode.get()
        if bg_mode != "original":
            try:
                # Convert PIL to CV2 BGR
                cv_img = cv2.cvtColor(np.array(current), cv2.COLOR_RGB2BGR)
                if self.cached_fg_mask is None or self.cached_fg_mask.shape[:2] != cv_img.shape[:2]:
                    self.cached_fg_mask = self.compute_foreground_mask(cv_img)

                if self.cached_fg_mask is not None:
                    # Target background color in RGB
                    bg_hex = bg_mode if bg_mode.startswith("#") else "#FFFFFF"
                    bg_rgb = tuple(int(bg_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

                    # Blend using alpha mask
                    alpha = (self.cached_fg_mask.astype(float) / 255.0)[:, :, np.newaxis]
                    orig_rgb = np.array(current).astype(float)
                    bg_solid = np.full_like(orig_rgb, bg_rgb, dtype=float)
                    blended = (orig_rgb * alpha + bg_solid * (1.0 - alpha)).astype(np.uint8)
                    current = Image.fromarray(blended)
            except Exception as e:
                print("Background blending exception:", e)

        self.working_image = current
        self.original_image = current  # Used for crop canvas coordinates
        self.render_crop_canvas()
        self.update_sheet()

    # -------------------------------------------------------------
    # Image Operations, Enhancements & Touch-up
    # -------------------------------------------------------------
    def apply_enhancements(self, img):
        b = self.brightness_var.get()
        if b != 0:
            factor = max(0.0, 1.0 + (b / 50.0) * 0.5)
            img = ImageEnhance.Brightness(img).enhance(factor)

        c = self.contrast_var.get()
        if c != 0:
            factor = max(0.0, 1.0 + (c / 50.0) * 0.6)
            img = ImageEnhance.Contrast(img).enhance(factor)

        s = self.saturation_var.get()
        if s != 0:
            factor = max(0.0, 1.0 + (s / 50.0) * 0.7)
            img = ImageEnhance.Color(img).enhance(factor)

        sh = self.sharpness_var.get()
        if sh > 0:
            factor = max(0.0, 1.0 + (sh / 25.0))
            img = ImageEnhance.Sharpness(img).enhance(factor)
        return img

    def _on_enhancement_change(self, *args):
        b = int(self.brightness_var.get())
        c = int(self.contrast_var.get())
        s = int(self.saturation_var.get())
        sh = int(self.sharpness_var.get())

        self.lbl_brightness_val.configure(text=f"{b:+d}%" if b != 0 else "0%")
        self.lbl_contrast_val.configure(text=f"{c:+d}%" if c != 0 else "0%")
        self.lbl_saturation_val.configure(text=f"{s:+d}%" if s != 0 else "0%")
        self.lbl_sharpness_val.configure(text=f"+{sh}" if sh > 0 else "0")

        self.render_crop_canvas()
        self.update_sheet()

    def reset_enhancements(self):
        self.brightness_var.set(0)
        self.contrast_var.set(0)
        self.saturation_var.set(0)
        self.sharpness_var.set(0)
        self._on_enhancement_change()

    def auto_enhance(self):
        self.brightness_var.set(6)
        self.contrast_var.set(10)
        self.saturation_var.set(4)
        self.sharpness_var.set(15)
        self._on_enhancement_change()

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[
                ("Image Files", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.tiff"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            img = ImageOps.exif_transpose(img)
            self.base_image = img.convert("RGB")
            self.cached_fg_mask = None

            # Reset rotation slider to 0
            self.rotate_angle_var.set(0)
            self.lbl_rotate_val.configure(text="0°")

            filename = os.path.basename(file_path)
            w, h = self.base_image.size
            self.lbl_photo_status.configure(text=f"Loaded: {filename}\nOriginal: {w} × {h} px")

            self.apply_working_pipeline()
            self.reset_crop_box()
            self.btn_export.configure(state="normal")
            self.btn_direct_print.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error Opening Image", f"Could not load image:\n{e}")

    def _on_rotate_slider(self, val):
        if not self.base_image:
            return
        angle = int(round(val))
        self.lbl_rotate_val.configure(text=f"{angle:+d}°" if angle != 0 else "0°")
        self.cached_fg_mask = None
        self.apply_working_pipeline()

    def step_rotation(self, delta):
        if not self.base_image:
            return
        current = int(round(self.rotate_angle_var.get()))
        new_angle = current + delta
        if new_angle > 180:
            new_angle -= 360
        elif new_angle < -180:
            new_angle += 360
        self.rotate_angle_var.set(new_angle)
        self._on_rotate_slider(new_angle)

    def reset_rotation(self):
        if not self.base_image:
            return
        self.rotate_angle_var.set(0)
        self._on_rotate_slider(0)

    def reset_crop_box(self):
        if not self.original_image:
            return

        orig_w, orig_h = self.original_image.size
        target_ratio = self.get_current_crop_ratio()

        if orig_w / orig_h > target_ratio:
            box_h = orig_h * 0.82
            box_w = box_h * target_ratio
        else:
            box_w = orig_w * 0.82
            box_h = box_w / target_ratio

        self.crop_norm_w = min(0.98, box_w / orig_w)
        self.crop_norm_h = min(0.98, box_h / orig_h)
        self.crop_norm_x = (1.0 - self.crop_norm_w) / 2.0
        self.crop_norm_y = (1.0 - self.crop_norm_h) / 2.0

        self.render_crop_canvas()
        self.update_sheet()

    def _on_border_slider(self, val):
        self.lbl_border_val.configure(text=f"{int(val)} px")
        self.update_sheet()

    def set_border_color(self, hex_color):
        self.border_color = hex_color
        self.update_sheet()

    def choose_custom_color(self):
        color = colorchooser.askcolor(color=self.border_color, title="Choose Photo Border Color")
        if color and color[1]:
            self.set_border_color(color[1])

    def _on_gap_slider(self, val):
        self.lbl_gap_val.configure(text=f"{val:.1f} mm")
        self.update_sheet()

    def _on_margin_slider(self, val):
        self.lbl_margin_val.configure(text=f"{val:.1f} mm")
        self.update_sheet()

    def _on_paper_change(self, value):
        cfg = self.PAPER_PRESETS.get(value, self.PAPER_PRESETS["4 × 6 inch (8 Photos)"])
        preset_cfg = self.PHOTO_PRESETS.get(self.selected_photo_preset.get(), self.PHOTO_PRESETS["Standard (1.5″ × 2″ / 3:4)"])

        # Dynamic photo count based on preset
        cols = preset_cfg.get("cols_4x6", cfg["cols"]) if "4 × 6" in value else cfg["cols"]
        rows = preset_cfg.get("rows_4x6", cfg["rows"]) if "4 × 6" in value else cfg["rows"]
        total_photos = cols * rows

        paper_short = cfg["label"].split('(')[0].strip()
        self.lbl_sheet_badge.configure(text=f"{total_photos} Photos ({cols} Col × {rows} Row)")
        self.btn_export.configure(text=f"💾  Export {paper_short} Sheet (JPG)")
        self.lbl_preview_title.configure(text=f"② {paper_short} Live Print Sheet Preview")
        self.update_sheet()

    def _on_dpi_change(self, value):
        if "600" in value:
            self.dpi_selection.set(600)
        else:
            self.dpi_selection.set(300)
        self.update_sheet()

    # -------------------------------------------------------------
    # Interactive Crop Canvas Rendering & Mouse Interaction
    # -------------------------------------------------------------
    def render_crop_canvas(self):
        self.crop_canvas.delete("all")
        if not self.original_image:
            cw = self.crop_canvas.winfo_width()
            ch = self.crop_canvas.winfo_height()
            if cw > 50 and ch > 50:
                self.crop_canvas.create_text(
                    cw // 2, ch // 2,
                    text="📂 Open a photo to start cropping",
                    fill="#64748B",
                    font=("Segoe UI", 12, "bold")
                )
            return

        cw = self.crop_canvas.winfo_width()
        ch = self.crop_canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        pad = 20
        avail_w = cw - pad * 2
        avail_h = ch - pad * 2

        orig_w, orig_h = self.original_image.size
        scale = min(avail_w / orig_w, avail_h / orig_h)
        self.canvas_scale = scale

        disp_w = int(orig_w * scale)
        disp_h = int(orig_h * scale)

        self.canvas_offset_x = (cw - disp_w) // 2
        self.canvas_offset_y = (ch - disp_h) // 2

        disp_img = self.original_image.resize((disp_w, disp_h), Image.Resampling.BILINEAR)
        disp_img = self.apply_enhancements(disp_img)
        self.tk_crop_img = ImageTk.PhotoImage(disp_img)
        self.crop_canvas.create_image(self.canvas_offset_x, self.canvas_offset_y, anchor="nw", image=self.tk_crop_img)

        # Calculate crop rectangle on canvas
        rx0 = self.canvas_offset_x + int(self.crop_norm_x * disp_w)
        ry0 = self.canvas_offset_y + int(self.crop_norm_y * disp_h)
        rx1 = rx0 + int(self.crop_norm_w * disp_w)
        ry1 = ry0 + int(self.crop_norm_h * disp_h)

        # Dimmed overlays outside crop box
        dim_color = "#000000"
        dim_stipple = "gray50"

        # Top
        self.crop_canvas.create_rectangle(
            self.canvas_offset_x, self.canvas_offset_y,
            self.canvas_offset_x + disp_w, ry0,
            fill=dim_color, stipple=dim_stipple, outline=""
        )
        # Bottom
        self.crop_canvas.create_rectangle(
            self.canvas_offset_x, ry1,
            self.canvas_offset_x + disp_w, self.canvas_offset_y + disp_h,
            fill=dim_color, stipple=dim_stipple, outline=""
        )
        # Left
        self.crop_canvas.create_rectangle(
            self.canvas_offset_x, ry0,
            rx0, ry1,
            fill=dim_color, stipple=dim_stipple, outline=""
        )
        # Right
        self.crop_canvas.create_rectangle(
            rx1, ry0,
            self.canvas_offset_x + disp_w, ry1,
            fill=dim_color, stipple=dim_stipple, outline=""
        )

        # Crop border & rule-of-thirds grid
        self.crop_canvas.create_rectangle(rx0, ry0, rx1, ry1, outline="#2563EB", width=2)

        # Rule of thirds grid lines
        gw = (rx1 - rx0) / 3.0
        gh = (ry1 - ry0) / 3.0
        for i in range(1, 3):
            self.crop_canvas.create_line(rx0 + int(gw * i), ry0, rx0 + int(gw * i), ry1, fill="#93C5FD", dash=(3, 3))
            self.crop_canvas.create_line(rx0, ry0 + int(gh * i), rx1, ry0 + int(gh * i), fill="#93C5FD", dash=(3, 3))

        # Corner drag handles
        handle_sz = 8
        handles = [
            (rx0, ry0, "nw"),
            (rx1, ry0, "ne"),
            (rx0, ry1, "sw"),
            (rx1, ry1, "se"),
        ]
        for hx, hy, tag in handles:
            self.crop_canvas.create_rectangle(
                hx - handle_sz, hy - handle_sz,
                hx + handle_sz, hy + handle_sz,
                fill="#FFFFFF", outline="#1D4ED8", width=2,
                tags=("handle", tag)
            )

    def _get_crop_canvas_coords(self):
        if not self.original_image:
            return 0, 0, 0, 0
        orig_w, orig_h = self.original_image.size
        disp_w = int(orig_w * self.canvas_scale)
        disp_h = int(orig_h * self.canvas_scale)
        rx0 = self.canvas_offset_x + int(self.crop_norm_x * disp_w)
        ry0 = self.canvas_offset_y + int(self.crop_norm_y * disp_h)
        rx1 = rx0 + int(self.crop_norm_w * disp_w)
        ry1 = ry0 + int(self.crop_norm_h * disp_h)
        return rx0, ry0, rx1, ry1

    def _on_crop_hover(self, event):
        if not self.original_image or self.drag_mode:
            return
        rx0, ry0, rx1, ry1 = self._get_crop_canvas_coords()
        h_sz = 10
        x, y = event.x, event.y

        if abs(x - rx0) <= h_sz and abs(y - ry0) <= h_sz:
            self.crop_canvas.config(cursor="top_left_corner")
        elif abs(x - rx1) <= h_sz and abs(y - ry0) <= h_sz:
            self.crop_canvas.config(cursor="top_right_corner")
        elif abs(x - rx0) <= h_sz and abs(y - ry1) <= h_sz:
            self.crop_canvas.config(cursor="bottom_left_corner")
        elif abs(x - rx1) <= h_sz and abs(y - ry1) <= h_sz:
            self.crop_canvas.config(cursor="bottom_right_corner")
        elif rx0 < x < rx1 and ry0 < y < ry1:
            self.crop_canvas.config(cursor="fleur")
        else:
            self.crop_canvas.config(cursor="arrow")

    def _on_crop_press(self, event):
        if not self.original_image:
            return
        rx0, ry0, rx1, ry1 = self._get_crop_canvas_coords()
        h_sz = 12
        x, y = event.x, event.y

        if abs(x - rx0) <= h_sz and abs(y - ry0) <= h_sz:
            self.drag_mode = "nw"
        elif abs(x - rx1) <= h_sz and abs(y - ry0) <= h_sz:
            self.drag_mode = "ne"
        elif abs(x - rx0) <= h_sz and abs(y - ry1) <= h_sz:
            self.drag_mode = "sw"
        elif abs(x - rx1) <= h_sz and abs(y - ry1) <= h_sz:
            self.drag_mode = "se"
        elif rx0 < x < rx1 and ry0 < y < ry1:
            self.drag_mode = "move"
        else:
            self.drag_mode = None

        if self.drag_mode:
            self.drag_start_x = x
            self.drag_start_y = y
            self.orig_crop_rect = (self.crop_norm_x, self.crop_norm_y, self.crop_norm_w, self.crop_norm_h)

    def _on_crop_drag(self, event):
        if not self.drag_mode or not self.original_image:
            return

        orig_w, orig_h = self.original_image.size
        disp_w = orig_w * self.canvas_scale
        disp_h = orig_h * self.canvas_scale

        dx_norm = (event.x - self.drag_start_x) / disp_w
        dy_norm = (event.y - self.drag_start_y) / disp_h

        ox, oy, ow, oh = self.orig_crop_rect
        target_ratio = self.get_current_crop_ratio()
        img_aspect = orig_w / orig_h

        if self.drag_mode == "move":
            new_x = max(0.0, min(1.0 - ow, ox + dx_norm))
            new_y = max(0.0, min(1.0 - oh, oy + dy_norm))
            self.crop_norm_x = new_x
            self.crop_norm_y = new_y
        else:
            if self.drag_mode == "se":
                cand_w = max(0.1, min(1.0 - ox, ow + dx_norm))
                cand_h = (cand_w * orig_w / target_ratio) / orig_h
                if oy + cand_h <= 1.0 and cand_h >= 0.1:
                    self.crop_norm_w = cand_w
                    self.crop_norm_h = cand_h
            elif self.drag_mode == "sw":
                cand_w = max(0.1, min(ox + ow, ow - dx_norm))
                cand_h = (cand_w * orig_w / target_ratio) / orig_h
                cand_x = (ox + ow) - cand_w
                if oy + cand_h <= 1.0 and cand_h >= 0.1 and cand_x >= 0.0:
                    self.crop_norm_x = cand_x
                    self.crop_norm_w = cand_w
                    self.crop_norm_h = cand_h
            elif self.drag_mode == "ne":
                cand_w = max(0.1, min(1.0 - ox, ow + dx_norm))
                cand_h = (cand_w * orig_w / target_ratio) / orig_h
                cand_y = (oy + oh) - cand_h
                if cand_y >= 0.0 and cand_h >= 0.1:
                    self.crop_norm_y = cand_y
                    self.crop_norm_w = cand_w
                    self.crop_norm_h = cand_h
            elif self.drag_mode == "nw":
                cand_w = max(0.1, min(ox + ow, ow - dx_norm))
                cand_h = (cand_w * orig_w / target_ratio) / orig_h
                cand_x = (ox + ow) - cand_w
                cand_y = (oy + oh) - cand_h
                if cand_x >= 0.0 and cand_y >= 0.0 and cand_h >= 0.1:
                    self.crop_norm_x = cand_x
                    self.crop_norm_y = cand_y
                    self.crop_norm_w = cand_w
                    self.crop_norm_h = cand_h

        self.render_crop_canvas()
        self.update_sheet()

    def _on_crop_release(self, event):
        self.drag_mode = None
        self.update_sheet()

    # -------------------------------------------------------------
    # Sheet Generation & Preview (Supports Presets, Stamp & Paper Sizes)
    # -------------------------------------------------------------
    def update_sheet(self):
        if not self.original_image:
            return

        orig_w, orig_h = self.original_image.size
        # Extract pixel crop from original image
        px0 = int(round(self.crop_norm_x * orig_w))
        py0 = int(round(self.crop_norm_y * orig_h))
        px1 = int(round((self.crop_norm_x + self.crop_norm_w) * orig_w))
        py1 = int(round((self.crop_norm_y + self.crop_norm_h) * orig_h))

        px0 = max(0, min(orig_w - 10, px0))
        py0 = max(0, min(orig_h - 10, py0))
        px1 = max(px0 + 10, min(orig_w, px1))
        py1 = max(py0 + 10, min(orig_h, py1))

        cropped = self.original_image.crop((px0, py0, px1, py1))
        cropped = self.apply_enhancements(cropped)

        # Paper & Preset Configuration
        paper_cfg = self.PAPER_PRESETS.get(self.selected_paper.get(), self.PAPER_PRESETS["4 × 6 inch (8 Photos)"])
        preset_cfg = self.PHOTO_PRESETS.get(self.selected_photo_preset.get(), self.PHOTO_PRESETS["Standard (1.5″ × 2″ / 3:4)"])

        paper_w_in = paper_cfg["w"]
        paper_h_in = paper_cfg["h"]
        is_4x6 = "4 × 6" in self.selected_paper.get()
        cols = preset_cfg.get("cols_4x6", paper_cfg["cols"]) if is_4x6 else paper_cfg["cols"]
        rows = preset_cfg.get("rows_4x6", paper_cfg["rows"]) if is_4x6 else paper_cfg["rows"]

        dpi = self.dpi_selection.get()
        sheet_w = int(round(paper_w_in * dpi))
        sheet_h = int(round(paper_h_in * dpi))

        # Convert user mm to pixels
        px_per_mm = dpi / 25.4
        gap_px = int(round(self.gap_mm.get() * px_per_mm))
        margin_px = int(round(self.margin_mm.get() * px_per_mm))

        total_gaps_x = (cols - 1) * gap_px + 2 * margin_px
        total_gaps_y = (rows - 1) * gap_px + 2 * margin_px

        avail_w = max(100, sheet_w - total_gaps_x)
        avail_h = max(100, sheet_h - total_gaps_y)

        max_pw = avail_w / cols
        max_ph = avail_h / rows

        target_ratio = self.get_current_crop_ratio()
        if max_pw / max_ph > target_ratio:
            photo_h = int(round(max_ph))
            photo_w = int(round(photo_h * target_ratio))
        else:
            photo_w = int(round(max_pw))
            photo_h = int(round(photo_w / target_ratio))

        w_inch = photo_w / dpi
        h_inch = photo_h / dpi
        w_mm = w_inch * 25.4
        h_mm = h_inch * 25.4

        self.lbl_photo_dims.configure(
            text=f"Photo: {w_inch:.2f}″ × {h_inch:.2f}″ ({w_mm:.1f} × {h_mm:.1f} mm) | {preset_cfg['label'].split('(')[0].strip()}"
        )
        self.lbl_dpi_info.configure(
            text=f"Canvas: {sheet_w} × {sheet_h} px @ {dpi} DPI ({paper_cfg['label'].split('(')[0].strip()})"
        )

        single_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)

        # Feature 2: Indian Government Exams Name & Date (DOP) Bottom Strip
        if self.dop_enabled.get():
            draw_dop = ImageDraw.Draw(single_photo)
            bar_height = max(28, int(photo_h * 0.18))
            bar_y0 = photo_h - bar_height
            # Pure white strip
            draw_dop.rectangle([0, bar_y0, photo_w, photo_h], fill="#FFFFFF")
            # Top divider line for the strip
            draw_dop.line([(0, bar_y0), (photo_w, bar_y0)], fill="#0F172A", width=max(1, int(dpi / 300)))

            name_text = self.dop_name.get().upper().strip()
            date_text = self.dop_date.get().strip()

            try:
                # Attempt to use standard Windows Arial Bold
                font_size = max(10, int(bar_height * 0.36))
                font_name = ImageFont.truetype("arialbd.ttf", font_size)
                font_date = ImageFont.truetype("arial.ttf", max(9, int(font_size * 0.88)))
            except Exception:
                font_name = ImageFont.load_default()
                font_date = ImageFont.load_default()

            # Center text lines
            bbox_name = draw_dop.textbbox((0, 0), name_text, font=font_name)
            nw = bbox_name[2] - bbox_name[0]
            nh = bbox_name[3] - bbox_name[1]

            bbox_date = draw_dop.textbbox((0, 0), date_text, font=font_date)
            dw = bbox_date[2] - bbox_date[0]
            dh = bbox_date[3] - bbox_date[1]

            pos_nx = max(2, (photo_w - nw) // 2)
            pos_ny = bar_y0 + max(2, int((bar_height - (nh + dh + 4)) // 2))
            pos_dx = max(2, (photo_w - dw) // 2)
            pos_dy = pos_ny + nh + max(2, int(dpi / 150))

            draw_dop.text((pos_nx, pos_ny), name_text, fill="#000000", font=font_name)
            draw_dop.text((pos_dx, pos_dy), date_text, fill="#000000", font=font_date)

        # Apply User Border & Color
        if self.border_enabled.get():
            draw_border = ImageDraw.Draw(single_photo)
            scaled_bw = max(1, int(self.border_width.get() * (dpi / 300.0)))
            draw_border.rectangle(
                [0, 0, photo_w - 1, photo_h - 1],
                outline=self.border_color,
                width=scaled_bw
            )

        # Create Clean Canvas (White photo paper)
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
        draw = ImageDraw.Draw(sheet)

        grid_total_w = cols * photo_w + (cols - 1) * gap_px
        grid_total_h = rows * photo_h + (rows - 1) * gap_px

        start_x = (sheet_w - grid_total_w) // 2
        start_y = (sheet_h - grid_total_h) // 2

        photo_rects = []
        for r in range(rows):
            row_rects = []
            for c in range(cols):
                x = start_x + c * (photo_w + gap_px)
                y = start_y + r * (photo_h + gap_px)
                sheet.paste(single_photo, (x, y))
                row_rects.append((x, y, x + photo_w, y + photo_h))
            photo_rects.append(row_rects)

        # Scissor Cut Guides
        if self.cut_guides_enabled.get():
            guide_color = (180, 180, 180)
            dash_step = max(16, int(dpi / 18))
            dash_len = max(8, int(dpi / 36))
            lw = max(1, int(dpi / 300))

            if gap_px > 0:
                for c in range(1, cols):
                    prev_right = photo_rects[0][c - 1][2]
                    curr_left = photo_rects[0][c][0]
                    cut_x = (prev_right + curr_left) // 2
                    for y in range(0, sheet_h, dash_step):
                        draw.line([(cut_x, y), (cut_x, min(y + dash_len, sheet_h))], fill=guide_color, width=lw)

                for r in range(1, rows):
                    prev_bottom = photo_rects[r - 1][0][3]
                    curr_top = photo_rects[r][0][1]
                    cut_y = (prev_bottom + curr_top) // 2
                    for x in range(0, sheet_w, dash_step):
                        draw.line([(x, cut_y), (min(x + dash_len, sheet_w), cut_y)], fill=guide_color, width=lw)

                grid_left = max(0, photo_rects[0][0][0] - gap_px // 2)
                grid_right = min(sheet_w - 1, photo_rects[0][cols - 1][2] + gap_px // 2)
                grid_top = max(0, photo_rects[0][0][1] - gap_px // 2)
                grid_bottom = min(sheet_h - 1, photo_rects[rows - 1][0][3] + gap_px // 2)

                for x in range(grid_left, grid_right, dash_step):
                    draw.line([(x, grid_top), (min(x + dash_len, grid_right), grid_top)], fill=guide_color, width=lw)
                    draw.line([(x, grid_bottom), (min(x + dash_len, grid_right), grid_bottom)], fill=guide_color, width=lw)
                for y in range(grid_top, grid_bottom, dash_step):
                    draw.line([(grid_left, y), (grid_left, min(y + dash_len, grid_bottom))], fill=guide_color, width=lw)
                    draw.line([(grid_right, y), (grid_right, min(y + dash_len, grid_bottom))], fill=guide_color, width=lw)
            else:
                for c in range(1, cols):
                    x = start_x + c * photo_w
                    for y in range(0, sheet_h, dash_step):
                        draw.line([(x, y), (x, min(y + dash_len, sheet_h))], fill=guide_color, width=lw)

                for r in range(1, rows):
                    y = start_y + r * photo_h
                    for x in range(0, sheet_w, dash_step):
                        draw.line([(x, y), (min(x + dash_len, sheet_w), y)], fill=guide_color, width=lw)

                draw.rectangle([0, 0, sheet_w - 1, sheet_h - 1], outline=(210, 210, 210), width=lw)

        self.sheet_image = sheet
        self.render_sheet_preview()

    def render_sheet_preview(self):
        self.preview_canvas.delete("all")
        if self.sheet_image is None:
            cw = self.preview_canvas.winfo_width()
            ch = self.preview_canvas.winfo_height()
            if cw > 50 and ch > 50:
                self.preview_canvas.create_text(
                    cw // 2, ch // 2,
                    text="Sheet preview will appear here",
                    fill="#64748B",
                    font=("Segoe UI", 12, "bold")
                )
            return

        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        pad = 28
        avail_w = cw - pad * 2
        avail_h = ch - pad * 2

        sw, sh = self.sheet_image.size
        scale = min(avail_w / sw, avail_h / sh)

        disp_w = max(1, int(sw * scale))
        disp_h = max(1, int(sh * scale))

        preview_img = self.sheet_image.resize((disp_w, disp_h), Image.Resampling.BILINEAR)
        self.tk_sheet_preview = ImageTk.PhotoImage(preview_img)

        pos_x = (cw - disp_w) // 2
        pos_y = (ch - disp_h) // 2

        shadow_offset = 6
        self.preview_canvas.create_rectangle(
            pos_x + shadow_offset, pos_y + shadow_offset,
            pos_x + disp_w + shadow_offset, pos_y + disp_h + shadow_offset,
            fill="#94A3B8",
            outline=""
        )
        self.preview_canvas.create_image(pos_x, pos_y, anchor="nw", image=self.tk_sheet_preview)

    # -------------------------------------------------------------
    # Feature 4: Direct Printing & Official Windows Print Dialog
    # -------------------------------------------------------------
    def open_direct_print_dialog(self):
        if self.sheet_image is None:
            messagebox.showwarning("No Sheet", "Please load and crop a photo first before printing.")
            return

        dlg = DirectPrintDialog(self)
        dlg.grab_set()

    def export_sheet_jpg(self):
        if self.sheet_image is None:
            return

        dpi = self.dpi_selection.get()
        gap = self.gap_mm.get()
        paper_cfg = self.PAPER_PRESETS.get(self.selected_paper.get(), self.PAPER_PRESETS["4 × 6 inch (8 Photos)"])
        preset_cfg = self.PHOTO_PRESETS.get(self.selected_photo_preset.get(), self.PHOTO_PRESETS["Standard (1.5″ × 2″ / 3:4)"])

        is_4x6 = "4 × 6" in self.selected_paper.get()
        cols = preset_cfg.get("cols_4x6", paper_cfg["cols"]) if is_4x6 else paper_cfg["cols"]
        rows = preset_cfg.get("rows_4x6", paper_cfg["rows"]) if is_4x6 else paper_cfg["rows"]
        total_photos = cols * rows

        paper_short = paper_cfg["label"].split('(')[0].replace(" ", "").replace("″", "").replace("×", "x").strip()
        default_name = f"{paper_short}_sheet_{total_photos}photos_{dpi}dpi.jpg"

        file_path = filedialog.asksaveasfilename(
            title="Export Print Sheet",
            defaultextension=".jpg",
            initialfile=default_name,
            filetypes=[("JPEG Image (*.jpg)", "*.jpg"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.sheet_image.save(
                file_path,
                "JPEG",
                quality=98,
                dpi=(dpi, dpi),
                subsampling=0
            )

            messagebox.showinfo(
                "Export Complete!",
                f"✅ Your {paper_cfg['label']} print sheet was saved successfully!\n\n"
                f"📁 Destination:\n{file_path}\n\n"
                f"📏 Specifications:\n"
                f"• Sheet Size: {paper_cfg['w']}″ × {paper_cfg['h']}″ ({self.sheet_image.width} × {self.sheet_image.height} px)\n"
                f"• Resolution: {dpi} DPI\n"
                f"• Photo Count: {total_photos} photos ({cols} Col × {rows} Row)\n"
                f"• Inter-Photo Spacing: {gap:.1f} mm\n\n"
                f"👤 Developer:\nJaimin Rabari (Mo. 9574782643)\n\n"
                f"🖨️ Printing Tip:\n"
                f"When printing, select paper size '{paper_cfg['label'].split('(')[0].strip()}' and choose 'Actual Size / 100%'\n"
                f"(do not select 'Fit to paper') to get exact physical dimensions."
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not save file:\n{e}")

    def open_webcam_dialog(self):
        """Opens live studio webcam capture dialog."""
        dlg = WebcamCaptureDialog(self)
        dlg.grab_set()


# =================================================================
# Studio Webcam Live Capture Dialog
# =================================================================
class WebcamCaptureDialog(ctk.CTkToplevel):
    def __init__(self, parent: "ProfessionalPhotoEditor"):
        super().__init__(parent)
        self.parent = parent
        self.title("📷 Studio Live Webcam Capture")
        self.geometry("640x660")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")

        self.cap = None
        self.current_frame_rgb = None
        self.captured_frame_rgb = None
        self.is_frozen = False
        self.loop_id = None
        self.camera_index = 0

        self._build_ui()
        self.start_camera()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

        # Top Bar
        top_bar = ctk.CTkFrame(container, fg_color="transparent")
        top_bar.pack(fill=tk.X, pady=(0, 10))

        title_lbl = ctk.CTkLabel(
            top_bar, text="📷 Live Studio Camera", font=ctk.CTkFont(size=16, weight="bold"), text_color="#0F172A"
        )
        title_lbl.pack(side=tk.LEFT)

        self.lbl_fps_status = ctk.CTkLabel(
            top_bar, text="● Camera Active", font=ctk.CTkFont(size=11, weight="bold"), text_color="#16A34A"
        )
        self.lbl_fps_status.pack(side=tk.RIGHT)

        # Video Canvas
        self.video_canvas = tk.Canvas(
            container,
            width=580,
            height=435,
            bg="#0F172A",
            highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Helper note
        self.lbl_guide_note = ctk.CTkLabel(
            container,
            text="Tip: Center the face within the cyan oval guide for ideal passport composition.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.lbl_guide_note.pack(anchor="w", pady=(0, 10))

        # Bottom Button Area
        self.btn_area = ctk.CTkFrame(container, fg_color="transparent")
        self.btn_area.pack(fill=tk.X)

        self._build_live_buttons()

    def _build_live_buttons(self):
        for widget in self.btn_area.winfo_children():
            widget.destroy()

        self.btn_snap = ctk.CTkButton(
            self.btn_area,
            text="📸  Capture Photo Now",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color="#16A34A",
            hover_color="#15803D",
            command=self.snap_photo
        )
        self.btn_snap.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_cancel = ctk.CTkButton(
            self.btn_area,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            height=42,
            width=100,
            fg_color="#F1F5F9",
            text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            command=self.on_close
        )
        btn_cancel.pack(side=tk.RIGHT)

    def _build_frozen_buttons(self):
        for widget in self.btn_area.winfo_children():
            widget.destroy()

        btn_use = ctk.CTkButton(
            self.btn_area,
            text="✅  Use This Photo",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.use_captured_photo
        )
        btn_use.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_retake = ctk.CTkButton(
            self.btn_area,
            text="↺  Retake",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            width=120,
            fg_color="#F1F5F9",
            text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            command=self.retake_photo
        )
        btn_retake.pack(side=tk.RIGHT)

    def start_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.update_video_loop()
            else:
                self.show_camera_error("Camera could not be opened.\nPlease verify webcam is connected.")
        except Exception as e:
            self.show_camera_error(f"Error accessing camera:\n{e}")

    def show_camera_error(self, msg):
        self.video_canvas.delete("all")
        self.video_canvas.create_text(
            290, 215,
            text=f"⚠️ {msg}",
            fill="#EF4444",
            font=("Segoe UI", 12, "bold"),
            justify="center"
        )
        self.lbl_fps_status.configure(text="● Camera Disconnected", text_color="#EF4444")

    def update_video_loop(self):
        if not self.is_frozen and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.current_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                disp_img = Image.fromarray(self.current_frame_rgb).resize((580, 435), Image.Resampling.BILINEAR)
                self.tk_frame = ImageTk.PhotoImage(disp_img)

                self.video_canvas.delete("all")
                self.video_canvas.create_image(0, 0, anchor="nw", image=self.tk_frame)

                # Biometric Oval Face Guide
                cx, cy = 290, 205
                rx, ry = 110, 145
                self.video_canvas.create_oval(
                    cx - rx, cy - ry, cx + rx, cy + ry,
                    outline="#06B6D4", width=2, dash=(6, 4)
                )
                self.video_canvas.create_line(
                    cx - 70, cy - 25, cx + 70, cy - 25,
                    fill="#22D3EE", width=1, dash=(3, 3)
                )
                self.video_canvas.create_line(
                    cx - 40, cy + ry - 10, cx + 40, cy + ry - 10,
                    fill="#22D3EE", width=1, dash=(3, 3)
                )
                self.video_canvas.create_text(
                    cx, cy - ry - 14,
                    text="ALIGN FACE IN OVAL",
                    fill="#A5F3FC",
                    font=("Segoe UI", 9, "bold")
                )

        if not self.is_frozen:
            self.loop_id = self.after(30, self.update_video_loop)

    def snap_photo(self):
        if self.current_frame_rgb is not None:
            self.is_frozen = True
            self.captured_frame_rgb = self.current_frame_rgb.copy()
            self.lbl_fps_status.configure(text="● Photo Captured (Preview)", text_color="#2563EB")
            self._build_frozen_buttons()

    def retake_photo(self):
        self.is_frozen = False
        self.captured_frame_rgb = None
        self.lbl_fps_status.configure(text="● Camera Active", text_color="#16A34A")
        self._build_live_buttons()
        self.update_video_loop()

    def use_captured_photo(self):
        if self.captured_frame_rgb is not None:
            pil_img = Image.fromarray(self.captured_frame_rgb)
            self.parent.base_image = pil_img
            self.parent.cached_fg_mask = None
            self.parent.rotate_angle_var.set(0)
            self.parent.lbl_rotate_val.configure(text="0°")

            w, h = pil_img.size
            self.parent.lbl_photo_status.configure(
                text=f"Loaded from Webcam\nStudio Capture: {w} × {h} px"
            )

            self.parent.apply_working_pipeline()
            self.parent.reset_crop_box()
            self.parent.btn_export.configure(state="normal")
            self.parent.btn_direct_print.configure(state="normal")
            self.on_close()

    def on_close(self):
        if self.loop_id:
            try:
                self.after_cancel(self.loop_id)
            except Exception:
                pass
            self.loop_id = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.destroy()


# =================================================================
# Direct Print Dialog (Official Windows Printer & 4x6 Inkjet Setup)
# =================================================================
class DirectPrintDialog(ctk.CTkToplevel):
    def __init__(self, parent: ProfessionalPhotoEditor):
        super().__init__(parent)
        self.parent = parent
        self.title("🖨️ Direct Inkjet Print Studio (4×6″ Paper)")
        self.geometry("540x560")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")

        # Discover installed Windows printers
        self.printer_list = []
        self.default_printer = ""
        if WIN32_PRINT_AVAILABLE:
            try:
                printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                self.printer_list = [p[2] for p in printers]
                self.default_printer = win32print.GetDefaultPrinter()
            except Exception as e:
                print("Printer enumeration exception:", e)

        if not self.printer_list:
            self.printer_list = ["Default Windows Printer"]
            self.default_printer = "Default Windows Printer"

        self.selected_printer = ctk.StringVar(value=self.default_printer)
        self.paper_size_var = ctk.StringVar(value="4 × 6 inch (10 × 15 cm / Photo Paper)")
        self.color_mode_var = ctk.StringVar(value="Full Color (Inkjet Photo)")
        self.dpi_print_var = ctk.StringVar(value="300 DPI (HD Quality)")
        self.copies_var = ctk.IntVar(value=1)

        self._build_ui()

    def _build_ui(self):
        pad_frame = ctk.CTkFrame(self, fg_color="transparent")
        pad_frame.pack(fill=tk.BOTH, expand=True, padx=22, pady=18)

        # Header Title
        title_lbl = ctk.CTkLabel(
            pad_frame,
            text="🖨️ Inkjet Photo Direct Print",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#0F172A"
        )
        title_lbl.pack(anchor="w", pady=(0, 2))

        sub_lbl = ctk.CTkLabel(
            pad_frame,
            text="Send high-resolution photo sheets directly to your connected inkjet printer.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        sub_lbl.pack(anchor="w", pady=(0, 12))

        # Printer Selector
        ctk.CTkLabel(pad_frame, text="Select Printer:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A").pack(anchor="w", pady=(0, 2))
        printer_menu = ctk.CTkOptionMenu(
            pad_frame,
            values=self.printer_list,
            variable=self.selected_printer,
            height=32
        )
        printer_menu.pack(fill=tk.X, pady=(0, 8))

        # Paper Size (Mandatory 4x6 selection)
        ctk.CTkLabel(pad_frame, text="Paper Size (Mandatory for Photo Inkjet):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A").pack(anchor="w", pady=(0, 2))
        paper_menu = ctk.CTkOptionMenu(
            pad_frame,
            values=[
                "4 × 6 inch (10 × 15 cm / Photo Paper)",
                "8 × 12 inch (20 × 30 cm)",
                "A4 Sheet (210 × 297 mm)"
            ],
            variable=self.paper_size_var,
            height=32
        )
        paper_menu.pack(fill=tk.X, pady=(0, 8))

        # Color Mode
        ctk.CTkLabel(pad_frame, text="Inkjet Color Mode:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A").pack(anchor="w", pady=(0, 2))
        color_seg = ctk.CTkSegmentedButton(
            pad_frame,
            values=["Full Color (Inkjet Photo)", "Grayscale (Black & White)"],
            variable=self.color_mode_var,
            height=30
        )
        color_seg.pack(fill=tk.X, pady=(0, 8))

        # Print Resolution & Copies Row
        rc_frame = ctk.CTkFrame(pad_frame, fg_color="transparent")
        rc_frame.pack(fill=tk.X, pady=(0, 12))

        r_sub = ctk.CTkFrame(rc_frame, fg_color="transparent")
        r_sub.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ctk.CTkLabel(r_sub, text="Print Quality:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        dpi_menu = ctk.CTkOptionMenu(
            r_sub,
            values=["300 DPI (HD Quality)", "600 DPI (Ultra HD Studio)"],
            variable=self.dpi_print_var,
            height=30
        )
        dpi_menu.pack(fill=tk.X)

        c_sub = ctk.CTkFrame(rc_frame, fg_color="transparent")
        c_sub.pack(side=tk.RIGHT, padx=(6, 0))
        ctk.CTkLabel(c_sub, text="Number of Copies:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        copies_menu = ctk.CTkOptionMenu(
            c_sub,
            values=["1", "2", "3", "4", "5", "10"],
            command=lambda v: self.copies_var.set(int(v)),
            width=100,
            height=30
        )
        copies_menu.pack()

        # Official Printer Properties Button (Calls win32print.DocumentProperties)
        btn_driver_props = ctk.CTkButton(
            pad_frame,
            text="⚙️ Open Official Printer Driver Properties (Epson/Canon)...",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color="#F8FAFC",
            text_color="#0F172A",
            hover_color="#F1F5F9",
            border_width=1,
            border_color="#CBD5E1",
            command=self.open_driver_properties
        )
        btn_driver_props.pack(fill=tk.X, pady=(0, 14))

        # Action Buttons Row
        btn_print_now = ctk.CTkButton(
            pad_frame,
            text="🖨️  Print Now (Direct High-Res Spool)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.execute_direct_gdi_print
        )
        btn_print_now.pack(fill=tk.X, pady=(0, 6))

        btn_wiz = ctk.CTkButton(
            pad_frame,
            text="🖼️  Open Windows Photo Print Wizard (4×6″)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color="#F1F5F9",
            text_color="#334155",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            command=self.execute_photo_wizard
        )
        btn_wiz.pack(fill=tk.X, pady=(0, 6))

    def open_driver_properties(self):
        """Invokes official Windows DocumentProperties dialog for the chosen printer driver."""
        if not WIN32_PRINT_AVAILABLE:
            messagebox.showinfo("Printer Properties", "Windows printer driver interface not available.")
            return

        printer_name = self.selected_printer.get()
        try:
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                # 0 = win32con.DM_IN_PROMPT (4) | win32con.DM_OUT_BUFFER (2)
                mode = win32con.DM_IN_PROMPT | win32con.DM_OUT_BUFFER
                res = win32print.DocumentProperties(int(self.winfo_id()), hprinter, printer_name, None, None, mode)
                if res == 1:
                    messagebox.showinfo("Printer Properties", "Printer preferences updated successfully!")
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            messagebox.showwarning("Driver Dialog", f"Could not open printer driver properties:\n{e}")

    def execute_direct_gdi_print(self):
        """Sends the exact 300/600 DPI bitmap directly to the printer device context."""
        if not WIN32_PRINT_AVAILABLE:
            self.execute_photo_wizard()
            return

        printer_name = self.selected_printer.get()
        copies = self.copies_var.get()
        is_color = "Color" in self.color_mode_var.get()

        try:
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                p_info = win32print.GetPrinter(hprinter, 2)
                devmode = p_info["pDevMode"]
                if devmode:
                    devmode.Color = win32con.DMCOLOR_COLOR if is_color else win32con.DMCOLOR_MONOCHROME
                    devmode.Orientation = win32con.DMORIENT_LANDSCAPE
                    # Configure custom or 4x6 paper if supported
                    try:
                        devmode.PaperSize = win32con.DMPAPER_USER
                        devmode.PaperWidth = 1524   # 152.4 mm (6 inch)
                        devmode.PaperLength = 1016  # 101.6 mm (4 inch)
                    except Exception:
                        pass

                hdc = win32ui.CreateDC()
                hdc.CreatePrinterDC(printer_name)
                hdc.StartDoc("Passport Photo Sheet 4x6")

                img_to_print = self.parent.sheet_image.copy()
                if not is_color:
                    img_to_print = img_to_print.convert("L").convert("RGB")

                for _ in range(copies):
                    hdc.StartPage()
                    printable_w = hdc.GetDeviceCaps(win32con.HORZRES)
                    printable_h = hdc.GetDeviceCaps(win32con.VERTRES)
                    dib = ImageWin.Dib(img_to_print)
                    dib.draw(hdc.GetHandleOutput(), (0, 0, printable_w, printable_h))
                    hdc.EndPage()

                hdc.EndDoc()
                hdc.DeleteDC()

                messagebox.showinfo(
                    "Print Job Sent!",
                    f"✅ Successfully sent {copies} copy(s) to '{printer_name}'!\n\n"
                    f"Paper Size: 4×6 inch (Photo Paper)\n"
                    f"Color Mode: {'Full Color' if is_color else 'Black & White'}\n"
                    f"Orientation: Landscape\n\n"
                    f"Your inkjet printer will begin printing now."
                )
                self.destroy()
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            messagebox.showerror("Printing Error", f"Could not print directly to '{printer_name}':\n{e}\n\nYou can use 'Windows Photo Print Wizard' as a reliable alternative.")

    def execute_photo_wizard(self):
        """Saves a temporary high-res sheet and invokes the Windows Photo Printing Wizard."""
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix="_passport_4x6.jpg")
            os.close(tmp_fd)

            dpi = 300 if "300" in self.dpi_print_var.get() else 600
            self.parent.sheet_image.save(tmp_path, "JPEG", quality=98, dpi=(dpi, dpi))

            if os.name == "nt":
                os.startfile(tmp_path, "print")
                self.destroy()
            else:
                messagebox.showinfo("Export Ready", f"File saved for printing:\n{tmp_path}")
        except Exception as e:
            messagebox.showerror("Print Wizard Error", f"Could not launch photo printing wizard:\n{e}")


def main():
    app = ProfessionalPhotoEditor()
    app.mainloop()


if __name__ == "__main__":
    main()
