"""
Passport & Photo Print Sheet Arranger Pro (Portable Edition)
made by : Jaimin Rabari Mo.9574782643

Professional GUI application to crop, customize border/color,
adjust spacing/gaps between photos for easy scissor cutting,
and arrange photos onto selectable paper formats (4×6″, 8×12″, 5×7″, 8×10″, A4).
"""

import os
import sys
import math
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageOps

# Set CustomTkinter theme - LIGHT MODE ONLY
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ProfessionalPhotoEditor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Passport & Photo Print Sheet Arranger Pro - by Jaimin Rabari")
        self.geometry("1340x840")
        self.minsize(1120, 720)

        # State Variables
        self.original_image = None       # PIL Image in full original resolution
        self.display_image = None        # Scaled PIL Image for crop canvas
        self.cropped_photo = None        # Resulting cropped PIL Image
        self.sheet_image = None          # Resulting print sheet PIL Image
        
        # Crop Geometry (Normalized to 0.0 - 1.0 of original image)
        self.crop_norm_x = 0.1
        self.crop_norm_y = 0.1
        self.crop_norm_w = 0.6
        self.crop_norm_h = 0.8  # constrained to 1.5:2 (0.75 aspect ratio)
        
        # Interactive Crop dragging state
        self.drag_mode = None  # None, "move", "nw", "ne", "sw", "se"
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.orig_crop_rect = None
        self.canvas_scale = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        # Customization Settings
        self.border_enabled = ctk.BooleanVar(value=True)
        self.border_width = ctk.IntVar(value=4)       # In pixels relative to 300 DPI
        self.border_color = "#FFFFFF"                  # Default crisp white
        
        # Spacing / Gap & Margin Settings (for physical cutting)
        self.gap_mm = ctk.DoubleVar(value=2.0)         # Inter-photo space in mm (0 to 6)
        self.margin_mm = ctk.DoubleVar(value=2.0)      # Outer sheet margin in mm (0 to 6)

        # Paper Size Presets
        self.PAPER_PRESETS = {
            "4 × 6 inch (8 Photos)": {"w": 6.0, "h": 4.0, "cols": 4, "rows": 2, "label": "4×6″ (8 Photos)"},
            "8 × 12 inch (32 Photos)": {"w": 12.0, "h": 8.0, "cols": 8, "rows": 4, "label": "8×12″ (32 Photos)"},
            "8 × 10 inch (20 Photos)": {"w": 10.0, "h": 8.0, "cols": 5, "rows": 4, "label": "8×10″ (20 Photos)"},
            "5 × 7 inch (8 Photos)": {"w": 7.0, "h": 5.0, "cols": 4, "rows": 2, "label": "5×7″ (8 Photos)"},
            "A4 Sheet (28 Photos)": {"w": 11.69, "h": 8.27, "cols": 7, "rows": 4, "label": "A4 (28 Photos)"},
        }
        self.selected_paper = ctk.StringVar(value="4 × 6 inch (8 Photos)")

        # Guides & Print
        self.cut_guides_enabled = ctk.BooleanVar(value=True)
        self.cut_guide_color = "#B0B0B0"               # Light gray dashed
        self.dpi_selection = ctk.IntVar(value=300)     # 300 or 600

        # Color presets
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
    # UI Layout Construction (LIGHT MODE)
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
            text="Passport & ID Photo Print Studio",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64748B"
        )
        spec_lbl.pack(side=tk.RIGHT)

    def _build_main_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 1. Left Sidebar: Settings & Controls (Fixed width: 340)
        self.sidebar = ctk.CTkScrollableFrame(container, width=340, corner_radius=12, fg_color="#FFFFFF")
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

    def _build_sidebar_controls(self):
        # Section 1: Photo Import & Transformation
        s1_title = ctk.CTkLabel(self.sidebar, text="1. Photo Source", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0F172A")
        s1_title.pack(anchor="w", pady=(4, 6))

        btn_open = ctk.CTkButton(
            self.sidebar,
            text="📂 Choose Photo...",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.load_image
        )
        btn_open.pack(fill=tk.X, pady=(0, 4))

        self.lbl_photo_status = ctk.CTkLabel(
            self.sidebar,
            text="No photo loaded yet",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=320,
            justify="left"
        )
        self.lbl_photo_status.pack(anchor="w", pady=(0, 6))

        # Rotate buttons row
        rotate_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        rotate_row.pack(fill=tk.X, pady=(0, 10))

        btn_rot_ccw = ctk.CTkButton(
            rotate_row, text="↺ 90° Left", width=95, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.rotate_photo(-90)
        )
        btn_rot_ccw.pack(side=tk.LEFT, padx=(0, 4), expand=True, fill=tk.X)

        btn_rot_cw = ctk.CTkButton(
            rotate_row, text="↻ 90° Right", width=95, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=lambda: self.rotate_photo(90)
        )
        btn_rot_cw.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)

        btn_reset_crop = ctk.CTkButton(
            rotate_row, text="Reset", width=65, height=28,
            fg_color="#F1F5F9", text_color="#0F172A",
            hover_color="#E2E8F0",
            border_width=1, border_color="#CBD5E1",
            command=self.reset_crop_box
        )
        btn_reset_crop.pack(side=tk.LEFT, padx=(4, 0))

        # Divider
        self._add_separator(self.sidebar)

        # Section 2: Border & Colors
        s2_title = ctk.CTkLabel(self.sidebar, text="2. Border & Colors", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0F172A")
        s2_title.pack(anchor="w", pady=(4, 6))

        border_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Enable Photo Border",
            variable=self.border_enabled,
            command=self.update_sheet,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        border_switch.pack(anchor="w", pady=(0, 8))

        # Border Width
        bw_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bw_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(bw_row, text="Border Width:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_border_val = ctk.CTkLabel(bw_row, text="4 px", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_border_val.pack(side=tk.RIGHT)

        self.slider_border = ctk.CTkSlider(
            self.sidebar,
            from_=1, to=20,
            number_of_steps=19,
            variable=self.border_width,
            command=self._on_border_slider
        )
        self.slider_border.pack(fill=tk.X, pady=(0, 10))

        # Border Color Picker & Swatches
        bc_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bc_header.pack(fill=tk.X, pady=(0, 6))
        ctk.CTkLabel(bc_header, text="Border Color:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        
        self.btn_color_swatch = ctk.CTkButton(
            bc_header,
            text="",
            width=42,
            height=26,
            corner_radius=6,
            fg_color=self.border_color,
            hover_color=self.border_color,
            border_width=2,
            border_color="#94A3B8",
            command=self.choose_custom_color
        )
        self.btn_color_swatch.pack(side=tk.RIGHT)

        # Quick Palette Swatches
        palette_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        palette_frame.pack(fill=tk.X, pady=(0, 10))
        for hex_code, name in self.color_presets:
            btn_chip = ctk.CTkButton(
                palette_frame,
                text="",
                width=28,
                height=26,
                corner_radius=6,
                fg_color=hex_code,
                hover_color=hex_code,
                border_width=1,
                border_color="#94A3B8",
                command=lambda c=hex_code: self.set_border_color(c)
            )
            btn_chip.pack(side=tk.LEFT, padx=3, pady=2)

        # Divider
        self._add_separator(self.sidebar)

        # Section 3: Photo Spacing & Cutting Margins
        s3_title = ctk.CTkLabel(self.sidebar, text="3. Spacing & Cutting Space", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0F172A")
        s3_title.pack(anchor="w", pady=(4, 4))
        
        spacing_desc = ctk.CTkLabel(
            self.sidebar,
            text="Adds space between photos for easy physical scissor cutting.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B",
            wraplength=320,
            justify="left"
        )
        spacing_desc.pack(anchor="w", pady=(0, 8))

        # Gap between photos slider
        gap_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        gap_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(gap_row, text="Space Between Photos:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_gap_val = ctk.CTkLabel(gap_row, text="2.0 mm", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        self.lbl_gap_val.pack(side=tk.RIGHT)

        self.slider_gap = ctk.CTkSlider(
            self.sidebar,
            from_=0.0, to=6.0,
            number_of_steps=12,
            variable=self.gap_mm,
            command=self._on_gap_slider
        )
        self.slider_gap.pack(fill=tk.X, pady=(0, 6))

        # Outer Sheet Margin slider
        margin_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        margin_row.pack(fill=tk.X, pady=(0, 2))
        ctk.CTkLabel(margin_row, text="Outer Edge Margin:", font=ctk.CTkFont(size=12)).pack(side=tk.LEFT)
        self.lbl_margin_val = ctk.CTkLabel(margin_row, text="2.0 mm", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_margin_val.pack(side=tk.RIGHT)

        self.slider_margin = ctk.CTkSlider(
            self.sidebar,
            from_=0.0, to=6.0,
            number_of_steps=12,
            variable=self.margin_mm,
            command=self._on_margin_slider
        )
        self.slider_margin.pack(fill=tk.X, pady=(0, 8))

        # Real-time Photo Dimension badge
        self.dims_card = ctk.CTkFrame(self.sidebar, corner_radius=8, fg_color="#F1F5F9", border_width=1, border_color="#E2E8F0")
        self.dims_card.pack(fill=tk.X, pady=(0, 10))

        self.lbl_photo_dims = ctk.CTkLabel(
            self.dims_card,
            text="Each Photo: 1.40″ × 1.87″ (35.6 × 47.5 mm)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1E3A8A"
        )
        self.lbl_photo_dims.pack(padx=8, pady=6)

        # Quick preset buttons for spacing
        preset_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        preset_row.pack(fill=tk.X, pady=(0, 8))

        btn_g0 = ctk.CTkButton(
            preset_row, text="0mm (Tight)", width=95, height=26,
            fg_color="#F1F5F9", text_color="#0F172A",
            border_width=1, border_color="#CBD5E1",
            hover_color="#E2E8F0",
            command=lambda: self.set_spacing_preset(0.0, 0.0)
        )
        btn_g0.pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)

        btn_g2 = ctk.CTkButton(
            preset_row, text="2mm (Ideal)", width=95, height=26,
            fg_color="#F1F5F9", text_color="#0F172A",
            border_width=1, border_color="#CBD5E1",
            hover_color="#E2E8F0",
            command=lambda: self.set_spacing_preset(2.0, 2.0)
        )
        btn_g2.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        btn_g4 = ctk.CTkButton(
            preset_row, text="4mm (Wide)", width=95, height=26,
            fg_color="#F1F5F9", text_color="#0F172A",
            border_width=1, border_color="#CBD5E1",
            hover_color="#E2E8F0",
            command=lambda: self.set_spacing_preset(4.0, 3.0)
        )
        btn_g4.pack(side=tk.LEFT, padx=(3, 0), expand=True, fill=tk.X)

        # Divider
        self._add_separator(self.sidebar)

        # Section 4: Paper Size, Layout & Print Quality
        s4_title = ctk.CTkLabel(self.sidebar, text="4. Paper Size & Resolution", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0F172A")
        s4_title.pack(anchor="w", pady=(4, 6))

        # Paper Size Selection
        paper_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        paper_row.pack(fill=tk.X, pady=(0, 8))
        ctk.CTkLabel(paper_row, text="Paper Layout:", font=ctk.CTkFont(size=12, weight="bold")).pack(side=tk.LEFT)

        paper_menu = ctk.CTkOptionMenu(
            paper_row,
            values=list(self.PAPER_PRESETS.keys()),
            variable=self.selected_paper,
            command=self._on_paper_change,
            width=185,
            height=28
        )
        paper_menu.pack(side=tk.RIGHT)

        # Scissor Cut Guides
        cut_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Scissor Cut Guides (Dashed Lines)",
            variable=self.cut_guides_enabled,
            command=self.update_sheet,
            font=ctk.CTkFont(size=12)
        )
        cut_switch.pack(anchor="w", pady=(0, 8))

        # Resolution (DPI)
        dpi_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
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

        self.lbl_dpi_info = ctk.CTkLabel(
            self.sidebar,
            text="Canvas: 1800 × 1200 px @ 300 DPI (4×6″)",
            font=ctk.CTkFont(size=10),
            text_color="#64748B",
            justify="left"
        )
        self.lbl_dpi_info.pack(anchor="w", pady=(0, 12))

        # Divider
        self._add_separator(self.sidebar)

        # Section 5: Export Action
        self.btn_export = ctk.CTkButton(
            self.sidebar,
            text="💾  Export 4×6 Sheet (JPG)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            fg_color="#16A34A",
            hover_color="#15803D",
            command=self.export_sheet_jpg
        )
        self.btn_export.pack(fill=tk.X, pady=(6, 4))
        self.btn_export.configure(state="disabled")

        self.lbl_export_tip = ctk.CTkLabel(
            self.sidebar,
            text="Tip: When printing, select your chosen paper size and choose 'Actual Size / 100%' (do not fit to frame) for exact photo dimensions.",
            font=ctk.CTkFont(size=10),
            text_color="#64748B",
            wraplength=320,
            justify="left"
        )
        self.lbl_export_tip.pack(anchor="w", pady=(4, 8))

    def _add_separator(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color="#E2E8F0")
        sep.pack(fill=tk.X, pady=10)

    # -------------------------------------------------------------
    # Crop Studio Panel (Stage 1)
    # -------------------------------------------------------------
    def _build_crop_panel(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        top_bar.pack(fill=tk.X, padx=12, pady=(10, 4))
        
        lbl = ctk.CTkLabel(top_bar, text="① Interactive Crop Studio", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0F172A")
        lbl.pack(side=tk.LEFT)
        
        hint = ctk.CTkLabel(top_bar, text="Aspect Ratio: 1.5 : 2.0 (3:4)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563EB")
        hint.pack(side=tk.RIGHT)

        instruction = ctk.CTkLabel(
            parent,
            text="🖱️ Drag inside the box to reposition. Drag corner handles to resize.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        instruction.pack(anchor="w", padx=12, pady=(0, 6))

        # Canvas for interactive crop
        self.crop_canvas = tk.Canvas(
            parent,
            bg="#E2E8F0",
            highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.crop_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # Mouse Bindings for interactive crop
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

        # Sheet Canvas
        self.preview_canvas = tk.Canvas(
            parent,
            bg="#E2E8F0",
            highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.preview_canvas.bind("<Configure>", lambda e: self.render_sheet_preview())

    # -------------------------------------------------------------
    # Image Operations & Events
    # -------------------------------------------------------------
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
            self.original_image = img.convert("RGB")
            
            filename = os.path.basename(file_path)
            w, h = self.original_image.size
            self.lbl_photo_status.configure(text=f"Loaded: {filename}\nOriginal: {w} × {h} px")
            
            self.reset_crop_box()
            self.btn_export.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error Opening Image", f"Could not load image:\n{e}")

    def rotate_photo(self, angle):
        if not self.original_image:
            return
        
        self.original_image = self.original_image.rotate(-angle, expand=True)
        self.reset_crop_box()

    def reset_crop_box(self):
        if not self.original_image:
            return

        orig_w, orig_h = self.original_image.size
        target_ratio = 1.5 / 2.0  # 0.75

        if orig_w / orig_h > target_ratio:
            box_h = orig_h * 0.8
            box_w = box_h * target_ratio
        else:
            box_w = orig_w * 0.8
            box_h = box_w / target_ratio

        self.crop_norm_w = box_w / orig_w
        self.crop_norm_h = box_h / orig_h
        self.crop_norm_x = (1.0 - self.crop_norm_w) / 2.0
        self.crop_norm_y = (1.0 - self.crop_norm_h) / 2.0

        self.render_crop_canvas()
        self.update_sheet()

    def _on_border_slider(self, val):
        self.lbl_border_val.configure(text=f"{int(val)} px")
        self.update_sheet()

    def set_border_color(self, hex_color):
        self.border_color = hex_color
        self.btn_color_swatch.configure(fg_color=hex_color, hover_color=hex_color)
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

    def set_spacing_preset(self, gap, margin):
        self.gap_mm.set(gap)
        self.margin_mm.set(margin)
        self.lbl_gap_val.configure(text=f"{gap:.1f} mm")
        self.lbl_margin_val.configure(text=f"{margin:.1f} mm")
        self.update_sheet()

    def _on_paper_change(self, value):
        cfg = self.PAPER_PRESETS.get(value, self.PAPER_PRESETS["4 × 6 inch (8 Photos)"])
        total_photos = cfg["cols"] * cfg["rows"]
        paper_short = cfg["label"].split('(')[0].strip()
        self.lbl_sheet_badge.configure(text=f"{total_photos} Photos ({cfg['cols']} Col × {cfg['rows']} Row)")
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
        self.tk_crop_img = ImageTk.PhotoImage(disp_img)
        self.crop_canvas.create_image(self.canvas_offset_x, self.canvas_offset_y, anchor="nw", image=self.tk_crop_img)

        bx0 = self.canvas_offset_x + self.crop_norm_x * disp_w
        by0 = self.canvas_offset_y + self.crop_norm_y * disp_h
        bx1 = bx0 + self.crop_norm_w * disp_w
        by1 = by0 + self.crop_norm_h * disp_h

        # 1. Dimmed outer masks
        mask_color = "#000000"
        stipple_pat = "gray50"
        
        self.crop_canvas.create_rectangle(
            self.canvas_offset_x, self.canvas_offset_y,
            self.canvas_offset_x + disp_w, by0,
            fill=mask_color, stipple=stipple_pat, outline=""
        )
        self.crop_canvas.create_rectangle(
            self.canvas_offset_x, by1,
            self.canvas_offset_x + disp_w, self.canvas_offset_y + disp_h,
            fill=mask_color, stipple=stipple_pat, outline=""
        )
        self.crop_canvas.create_rectangle(
            self.canvas_offset_x, by0,
            bx0, by1,
            fill=mask_color, stipple=stipple_pat, outline=""
        )
        self.crop_canvas.create_rectangle(
            bx1, by0,
            self.canvas_offset_x + disp_w, by1,
            fill=mask_color, stipple=stipple_pat, outline=""
        )

        # 2. Inside Rule of Thirds Guide Lines
        third_w = (bx1 - bx0) / 3.0
        third_h = (by1 - by0) / 3.0
        for i in range(1, 3):
            self.crop_canvas.create_line(
                bx0 + i * third_w, by0,
                bx0 + i * third_w, by1,
                fill="#FFFFFF", dash=(2, 4)
            )
            self.crop_canvas.create_line(
                bx0, by0 + i * third_h,
                bx1, by0 + i * third_h,
                fill="#FFFFFF", dash=(2, 4)
            )

        # 3. Crop Box Border (Vibrant Blue)
        self.crop_canvas.create_rectangle(bx0, by0, bx1, by1, outline="#2563EB", width=2)

        # 4. Corner Handles
        handle_len = 16
        handle_w = 4
        handle_color = "#2563EB"

        self.crop_canvas.create_line(bx0, by0, bx0 + handle_len, by0, fill=handle_color, width=handle_w)
        self.crop_canvas.create_line(bx0, by0, bx0, by0 + handle_len, fill=handle_color, width=handle_w)

        self.crop_canvas.create_line(bx1, by0, bx1 - handle_len, by0, fill=handle_color, width=handle_w)
        self.crop_canvas.create_line(bx1, by0, bx1, by0 + handle_len, fill=handle_color, width=handle_w)

        self.crop_canvas.create_line(bx0, by1, bx0 + handle_len, by1, fill=handle_color, width=handle_w)
        self.crop_canvas.create_line(bx0, by1, bx0, by1 - handle_len, fill=handle_color, width=handle_w)

        self.crop_canvas.create_line(bx1, by1, bx1 - handle_len, by1, fill=handle_color, width=handle_w)
        self.crop_canvas.create_line(bx1, by1, bx1, by1 - handle_len, fill=handle_color, width=handle_w)

    def _get_crop_box_pixels(self):
        if not self.original_image or self.canvas_scale <= 0:
            return None
        orig_w, orig_h = self.original_image.size
        disp_w = orig_w * self.canvas_scale
        disp_h = orig_h * self.canvas_scale

        bx0 = self.canvas_offset_x + self.crop_norm_x * disp_w
        by0 = self.canvas_offset_y + self.crop_norm_y * disp_h
        bx1 = bx0 + self.crop_norm_w * disp_w
        by1 = by0 + self.crop_norm_h * disp_h
        return bx0, by0, bx1, by1

    def _on_crop_hover(self, event):
        if not self.original_image:
            return
        box = self._get_crop_box_pixels()
        if not box:
            return

        bx0, by0, bx1, by1 = box
        mx, my = event.x, event.y
        tol = 14

        if abs(mx - bx0) <= tol and abs(my - by0) <= tol:
            self.crop_canvas.config(cursor="top_left_corner")
        elif abs(mx - bx1) <= tol and abs(my - by0) <= tol:
            self.crop_canvas.config(cursor="top_right_corner")
        elif abs(mx - bx0) <= tol and abs(my - by1) <= tol:
            self.crop_canvas.config(cursor="bottom_left_corner")
        elif abs(mx - bx1) <= tol and abs(my - by1) <= tol:
            self.crop_canvas.config(cursor="bottom_right_corner")
        elif bx0 <= mx <= bx1 and by0 <= my <= by1:
            self.crop_canvas.config(cursor="fleur")
        else:
            self.crop_canvas.config(cursor="arrow")

    def _on_crop_press(self, event):
        if not self.original_image:
            return
        box = self._get_crop_box_pixels()
        if not box:
            return

        bx0, by0, bx1, by1 = box
        mx, my = event.x, event.y
        tol = 14

        if abs(mx - bx0) <= tol and abs(my - by0) <= tol:
            self.drag_mode = "nw"
        elif abs(mx - bx1) <= tol and abs(my - by0) <= tol:
            self.drag_mode = "ne"
        elif abs(mx - bx0) <= tol and abs(my - by1) <= tol:
            self.drag_mode = "sw"
        elif abs(mx - bx1) <= tol and abs(my - by1) <= tol:
            self.drag_mode = "se"
        elif bx0 <= mx <= bx1 and by0 <= my <= by1:
            self.drag_mode = "move"
        else:
            self.drag_mode = None
            return

        self.drag_start_x = mx
        self.drag_start_y = my
        self.orig_crop_rect = (self.crop_norm_x, self.crop_norm_y, self.crop_norm_w, self.crop_norm_h)

    def _on_crop_drag(self, event):
        if not self.drag_mode or not self.original_image:
            return

        orig_w, orig_h = self.original_image.size
        disp_w = orig_w * self.canvas_scale
        disp_h = orig_h * self.canvas_scale

        if disp_w <= 0 or disp_h <= 0:
            return

        delta_x = (event.x - self.drag_start_x) / disp_w
        delta_y = (event.y - self.drag_start_y) / disp_h

        ox, oy, ow, oh = self.orig_crop_rect
        target_ratio = 1.5 / 2.0  # 0.75

        if self.drag_mode == "move":
            new_x = max(0.0, min(1.0 - ow, ox + delta_x))
            new_y = max(0.0, min(1.0 - oh, oy + delta_y))
            self.crop_norm_x = new_x
            self.crop_norm_y = new_y

        elif self.drag_mode in ("se", "ne", "sw", "nw"):
            if self.drag_mode == "se":
                new_w = max(0.15, min(1.0 - ox, ow + delta_x))
                new_h = (new_w * orig_w / target_ratio) / orig_h
                if oy + new_h > 1.0:
                    new_h = 1.0 - oy
                    new_w = (new_h * orig_h * target_ratio) / orig_w
                self.crop_norm_w = new_w
                self.crop_norm_h = new_h

            elif self.drag_mode == "sw":
                new_w = max(0.15, min(ox + ow, ow - delta_x))
                new_h = (new_w * orig_w / target_ratio) / orig_h
                if oy + new_h > 1.0:
                    new_h = 1.0 - oy
                    new_w = (new_h * orig_h * target_ratio) / orig_w
                self.crop_norm_x = (ox + ow) - new_w
                self.crop_norm_w = new_w
                self.crop_norm_h = new_h

            elif self.drag_mode == "ne":
                new_w = max(0.15, min(1.0 - ox, ow + delta_x))
                new_h = (new_w * orig_w / target_ratio) / orig_h
                if (oy + oh) - new_h < 0.0:
                    new_h = oy + oh
                    new_w = (new_h * orig_h * target_ratio) / orig_w
                self.crop_norm_y = (oy + oh) - new_h
                self.crop_norm_w = new_w
                self.crop_norm_h = new_h

            elif self.drag_mode == "nw":
                new_w = max(0.15, min(ox + ow, ow - delta_x))
                new_h = (new_w * orig_w / target_ratio) / orig_h
                if (oy + oh) - new_h < 0.0:
                    new_h = oy + oh
                    new_w = (new_h * orig_h * target_ratio) / orig_w
                self.crop_norm_x = (ox + ow) - new_w
                self.crop_norm_y = (oy + oh) - new_h
                self.crop_norm_w = new_w
                self.crop_norm_h = new_h

        self.render_crop_canvas()
        self.update_sheet()

    def _on_crop_release(self, event):
        self.drag_mode = None
        self.update_sheet()

    # -------------------------------------------------------------
    # Sheet Generation & Preview (Supports Any Paper Size!)
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

        # Paper Configuration
        paper_cfg = self.PAPER_PRESETS.get(self.selected_paper.get(), self.PAPER_PRESETS["4 × 6 inch (8 Photos)"])
        paper_w_in = paper_cfg["w"]
        paper_h_in = paper_cfg["h"]
        cols = paper_cfg["cols"]
        rows = paper_cfg["rows"]

        dpi = self.dpi_selection.get()
        sheet_w = int(round(paper_w_in * dpi))
        sheet_h = int(round(paper_h_in * dpi))

        # Convert user mm to pixels
        px_per_mm = dpi / 25.4
        gap_px = int(round(self.gap_mm.get() * px_per_mm))
        margin_px = int(round(self.margin_mm.get() * px_per_mm))

        # Available space after subtracting inter-photo gaps and outer margins
        total_gaps_x = (cols - 1) * gap_px + 2 * margin_px
        total_gaps_y = (rows - 1) * gap_px + 2 * margin_px

        avail_w = max(100, sheet_w - total_gaps_x)
        avail_h = max(100, sheet_h - total_gaps_y)

        # Max width & height per photo slot
        max_pw = avail_w / cols
        max_ph = avail_h / rows

        # Maintain exact 1.5 : 2.0 (0.75) aspect ratio
        target_ratio = 1.5 / 2.0  # 0.75
        if max_pw / max_ph > target_ratio:
            photo_h = int(round(max_ph))
            photo_w = int(round(photo_h * target_ratio))
        else:
            photo_w = int(round(max_pw))
            photo_h = int(round(photo_w / target_ratio))

        # Physical dimensions display
        w_inch = photo_w / dpi
        h_inch = photo_h / dpi
        w_mm = w_inch * 25.4
        h_mm = h_inch * 25.4

        self.lbl_photo_dims.configure(
            text=f"Photo: {w_inch:.2f}″ × {h_inch:.2f}″ ({w_mm:.1f} × {h_mm:.1f} mm) | 3:4"
        )
        self.lbl_dpi_info.configure(
            text=f"Canvas: {sheet_w} × {sheet_h} px @ {dpi} DPI ({paper_cfg['label'].split('(')[0].strip()})"
        )

        # High-definition Lanczos resize of cropped photo
        single_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)

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

        # Center the grid on the sheet
        grid_total_w = cols * photo_w + (cols - 1) * gap_px
        grid_total_h = rows * photo_h + (rows - 1) * gap_px

        start_x = (sheet_w - grid_total_w) // 2
        start_y = (sheet_h - grid_total_h) // 2

        # Record photo coordinates for scissor cut guides
        photo_rects = []

        # Paste all photos
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
                # Vertical cut lines down the exact center of each gap
                for c in range(1, cols):
                    prev_right = photo_rects[0][c - 1][2]
                    curr_left = photo_rects[0][c][0]
                    cut_x = (prev_right + curr_left) // 2
                    for y in range(0, sheet_h, dash_step):
                        draw.line([(cut_x, y), (cut_x, min(y + dash_len, sheet_h))], fill=guide_color, width=lw)

                # Horizontal cut lines across the exact center between rows
                for r in range(1, rows):
                    prev_bottom = photo_rects[r - 1][0][3]
                    curr_top = photo_rects[r][0][1]
                    cut_y = (prev_bottom + curr_top) // 2
                    for x in range(0, sheet_w, dash_step):
                        draw.line([(x, cut_y), (min(x + dash_len, sheet_w), cut_y)], fill=guide_color, width=lw)

                # Outer boundary cut lines
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

        # Draw drop shadow (Light mode: soft slate shadow)
        shadow_offset = 6
        self.preview_canvas.create_rectangle(
            pos_x + shadow_offset, pos_y + shadow_offset,
            pos_x + disp_w + shadow_offset, pos_y + disp_h + shadow_offset,
            fill="#94A3B8",
            outline=""
        )

        # Draw sheet image
        self.preview_canvas.create_image(pos_x, pos_y, anchor="nw", image=self.tk_sheet_preview)

    def export_sheet_jpg(self):
        if self.sheet_image is None:
            return

        dpi = self.dpi_selection.get()
        gap = self.gap_mm.get()
        paper_cfg = self.PAPER_PRESETS.get(self.selected_paper.get(), self.PAPER_PRESETS["4 × 6 inch (8 Photos)"])
        total_photos = paper_cfg["cols"] * paper_cfg["rows"]
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
            # Save at 98% quality, exact DPI headers, and 4:4:4 color preservation
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
                f"• Photo Count: {total_photos} photos ({paper_cfg['cols']} Col × {paper_cfg['rows']} Row)\n"
                f"• Inter-Photo Spacing: {gap:.1f} mm\n\n"
                f"👤 Developer:\nJaimin Rabari (Mo. 9574782643)\n\n"
                f"🖨️ Printing Tip:\n"
                f"When printing, select paper size '{paper_cfg['label'].split('(')[0].strip()}' and choose 'Actual Size / 100%'\n"
                f"(do not select 'Fit to paper') to get exact physical dimensions."
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not save file:\n{e}")

def main():
    app = ProfessionalPhotoEditor()
    app.mainloop()

if __name__ == "__main__":
    main()
