# Passport & Photo Print Sheet Arranger Pro (Portable Edition)
**made by : Jaimin Rabari Mo.9574782643**

A professional, 100% offline desktop application to capture from live webcam, load photo files, crop, straighten with single-degree rotation, apply studio touch-ups, replace backgrounds, stamp exam name/date bars, and arrange photos onto **4×6″ (Inkjet Photo Paper), 8×12″, 8×10″, 5×7″, and A4** sheets with direct Windows Inkjet printing.

---

## 🌟 Key Features

### 1. 📷 Live Studio Webcam Capture
- **Real-Time Studio Feed:** Capture customer photos directly from your USB camera or laptop webcam using DirectShow hardware acceleration.
- **Biometric Face Oval Guide:** Cyan dashed guide overlay showing exact eye-level and chin alignment boundaries for compliant passport photos.
- **Snap & Review Workflow:** Review the captured frame with **"✅ Use This Photo"** or **"↺ Retake"** before loading into the studio.

### 2. 🌐 Government & International Visa/Passport Presets
Instantly switches crop aspect ratio and sheet layout for official specifications:
- **`Standard (1.5″ × 2″ / 3:4)`**: 8 photos on 4×6″ ($38.1 \times 50.8\text{ mm}$).
- **`India Passport / PAN / OCI (35×45 mm)`**: Official 7:9 ratio for Indian IDs ($35.0 \times 45.0\text{ mm}$).
- **`US Visa / US Passport (2″ × 2″ Square)`**: Official 1:1 square format (6 photos on 4×6″, $50.8 \times 50.8\text{ mm}$).
- **`Schengen / UK / Europe Visa (35×45 mm)`**: Compliant European biometric ratio.
- **`Canada Visa (50×70 mm)`**: Official Canadian passport/visa proportion ($50 \times 70\text{ mm}$).
- **`Stamp / Token Size (25×30 mm)`**: 15 photos on 4×6″ for school/office identity cards.

### 3. 🖨️ Direct Inkjet Printing & Official Windows Printer Dialog
- **Mandatory 4×6″ Inkjet Paper Support**: Designed specifically for 4×6″ (10×15 cm) glossy inkjet photo paper (Epson L805, L850, Canon Pixma G-series, HP Ink Tank).
- **Official Printer Driver Preferences**: One-click button to open your printer driver's native properties window (Epson/Canon) to select **Premium Glossy Paper**, **High Quality / Best Photo**, and color profiles.
- **Color Mode Selection**: Select **Full Color** or **Grayscale (B&W)** directly in the print dialog.
- **Direct GDI Spooling**: Spools the raw 300/600 DPI bitmap directly to the printer device context without third-party viewer compression.
- **Windows Photo Print Wizard Fallback**: Option to launch the native Windows photo printing wizard.

### 4. 🏷️ Name & Date of Photo (DOP) Stamp (Indian Govt Exams)
- **Mandatory Exam Formatting**: UPSC, SSC CGL/CHSL, Railway RRB, State Police, NEET, and Defense exams require a bottom name and date strip.
- **Automated Generation**: Clean white bottom strip with centered bold black text:
  - **Candidate Full Name** (e.g., `RAHUL SHARMA`)
  - **Date of Photo (DOP)** (pre-filled with today's date, e.g., `DOP: 24/11/2026`)
- Real-time live preview on the sheet.

### 5. 🎨 100% Offline Background Replacement / Remover
- **Zero Internet Required**: Runs completely offline using OpenCV GrabCut with adaptive Gaussian edge feathering.
- **Official Studio Background Colors**:
  - `⚪ Pure Studio White` (`#FFFFFF`) — standard passport & visa requirement.
  - `🔵 Sky Blue` (`#87CEEB`) — standard for school & college identity forms.
  - `🔘 Light Grey` (`#E2E8F0`) — standard for European Schengen visas.
  - `🎨 Choose Custom Studio Color...` — full-width color picker.
  - `↺ Original` — restores original photo background with one click.

### 6. 📂 Uncluttered, Spacious Accordion Interface
Organized into clean, collapsible accordion sections so the interface stays spacious:
- **1. Photo Source & Rotation** (Always visible at top: Choose File + Take Photo buttons)
- **▼ 2. Passport & Visa Presets** (Open by default)
- **▶ 3. Background Color (Offline)** (Closed by default)
- **▶ 4. Name & Date Stamp (Govt Exams)** (Closed by default)
- **▼ 5. Photo Touch & Color** (Open by default)
- **▶ 6. Border Settings** (Closed by default)
- **▶ 7. Spacing & Margin Settings** (Closed by default)
- **▼ 8. Paper Size & Resolution** (Open by default)

### 7. 📐 Precision Single-Degree Rotation Slider
- Fine-tune angle from **`-180°` to `+180°` in $1^\circ$ increments**.
- Bicubic rotation from source without image degradation.
- Quick buttons: `↺ -90°`, `0° Reset`, `↻ +90°`, `↺ Crop`.

### 8. 🎨 Photo Touch & Color Enhancement
- **☀️ Brightness:** `-50%` to `+50%`.
- **🌓 Contrast:** `-50%` to `+50%`.
- **🎨 Saturation:** `-50%` to `+50%`.
- **🔍 Sharpness:** Boost facial feature clarity (`0` to `+50`).
- **✨ Auto Studio Touch:** 1-click balanced touch-up.

### 9. 📄 Multi-Paper Size Layout Engine
- **`4 × 6 inch (8 Photos)`** *(Default)*: 4R photo paper.
- **`8 × 12 inch (32 Photos)`**: 8R/S8R studio sheets.
- **`8 × 10 inch (20 Photos)`**: 10R sheets.
- **`5 × 7 inch (8 Photos)`**: 5R sheets.
- **`A4 Sheet (28 Photos)`**: International document paper.

### 10. ✂️ Inter-Photo Spacing & Scissor Corridors
- **Spacing Slider:** `0.0 mm` to `6.0 mm` space between photos.
- **Outer Margin Slider:** `0.0 mm` to `6.0 mm`.
- **Dashed Scissor Cut Guides:** Centered between photos for clean cutting.

---

## 🔒 Certified Windows Metadata & Icon
The portable executable is packaged with:
- **Application Icon:** High-resolution multi-size `.ico` studio camera icon.
- **Version Metadata:** 
  - Company: `Jaimin Rabari`
  - Product: `Passport & Photo Print Sheet Arranger Pro`
  - Version: `1.0.0.0`
  - Copyright: `Copyright (C) 2026 Jaimin Rabari. All rights reserved.`
  - Original Filename: `PhotoSheetArranger_4x6.exe`

---

## 🚀 Quick Usage Guide

1. Double-click **`PhotoSheetArranger_4x6.exe`**.
2. Click **"📂 Choose File..."** or **"📷 Take Photo..."** to capture from webcam.
3. Select your **Passport/Visa Preset** (e.g., *India Passport 35×45 mm*, *US Visa 2×2″*, or *Standard 1.5×2″*).
4. (Optional) Expand **Background Color** to switch to white or blue.
5. (Optional) Expand **Name & Date Stamp** if printing for government exams.
6. Drag the crop box on the canvas to frame the face.
7. Click **"🖨️ Direct Print Sheet (4×6″ Inkjet)"** to print immediately, or **"💾 Export Sheet (JPG)"** to save.
