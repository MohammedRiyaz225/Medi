import cv2
import easyocr
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import re
from datetime import datetime
import threading
import time

class MedicineScanner:
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback
        self.reader = None
        self.cap = None
        self.scanning = False
        self.scan_window = None

        # Initialize OCR reader in a separate thread
        self.init_ocr_reader()

    def init_ocr_reader(self):
        """Initialize EasyOCR reader"""
        try:
            self.reader = easyocr.Reader(['en'])
            print("OCR Reader initialized successfully")
        except Exception as e:
            print(f"Error initializing OCR reader: {e}")
            messagebox.showerror("Error", "Failed to initialize OCR reader. Please check your installation.")

    def start_scanning(self):
        """Start the camera scanning interface"""
        if not self.reader:
            messagebox.showerror("Error", "OCR reader not initialized")
            return

        self.scan_window = tk.Toplevel(self.parent)
        self.scan_window.title("Medicine Scanner")
        self.scan_window.geometry("800x700")
        self.scan_window.configure(bg='#f0f8ff')

        # Center the window
        self.scan_window.eval('tk::PlaceWindow . center')

        # Create UI elements
        self.create_scanner_interface()

        # Start camera
        self.start_camera()

    def create_scanner_interface(self):
        """Create the scanner interface"""
        # Title
        title_label = tk.Label(self.scan_window, text="📸 Medicine Scanner",
                              font=('Arial', 18, 'bold'),
                              bg='#f0f8ff', fg='#2c3e50')
        title_label.pack(pady=10)

        # Instructions
        instructions = tk.Label(self.scan_window,
                               text="Position the medicine label in front of the camera and click 'Scan'",
                               font=('Arial', 10),
                               bg='#f0f8ff', fg='#7f8c8d')
        instructions.pack(pady=5)

        # Camera frame
        self.camera_frame = tk.Label(self.scan_window,
                                   text="Initializing camera...",
                                   bg='#34495e', fg='white',
                                   font=('Arial', 12))
        self.camera_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Control buttons frame
        control_frame = tk.Frame(self.scan_window, bg='#f0f8ff')
        control_frame.pack(pady=10)

        # Scan button
        self.scan_btn = tk.Button(control_frame, text="📷 Scan Medicine",
                                 command=self.scan_medicine,
                                 font=('Arial', 12, 'bold'),
                                 bg='#e74c3c', fg='white',
                                 width=15, height=2,
                                 relief=tk.FLAT,
                                 cursor='hand2')
        self.scan_btn.pack(side=tk.LEFT, padx=10)

        # Close button
        close_btn = tk.Button(control_frame, text="❌ Close",
                             command=self.close_scanner,
                             font=('Arial', 12, 'bold'),
                             bg='#95a5a6', fg='white',
                             width=15, height=2,
                             relief=tk.FLAT,
                             cursor='hand2')
        close_btn.pack(side=tk.LEFT, padx=10)

        # Results frame
        results_frame = tk.LabelFrame(self.scan_window, text="Scan Results",
                                     font=('Arial', 12, 'bold'),
                                     bg='#f0f8ff', fg='#2c3e50')
        results_frame.pack(pady=10, padx=20, fill=tk.X)

        # Results text area
        self.results_text = tk.Text(results_frame, height=6, width=70,
                                   font=('Courier', 10),
                                   bg='#ffffff', fg='#2c3e50',
                                   wrap=tk.WORD)
        self.results_text.pack(pady=10, padx=10, fill=tk.BOTH)

        # Add to inventory button
        add_btn = tk.Button(results_frame, text="➕ Add to Inventory",
                           command=self.add_to_inventory,
                           font=('Arial', 10, 'bold'),
                           bg='#27ae60', fg='white',
                           width=20, height=2,
                           relief=tk.FLAT,
                           cursor='hand2',
                           state=tk.DISABLED)
        add_btn.pack(pady=10)
        self.add_btn = add_btn

    def start_camera(self):
        """Start camera feed"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Cannot open camera")

            self.scanning = True
            self.update_camera_feed()

        except Exception as e:
            print(f"Camera error: {e}")
            messagebox.showerror("Error", "Failed to start camera. Please check your camera connection.")

    def update_camera_feed(self):
        """Update camera feed in the GUI"""
        if self.scanning and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Resize frame for display
                frame = cv2.resize(frame, (640, 480))

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image and then to PhotoImage
                from PIL import Image, ImageTk
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(img)

                # Update the label
                self.camera_frame.configure(image=img_tk)
                self.camera_frame.image = img_tk

            # Schedule next update
            self.scan_window.after(30, self.update_camera_feed)

    def scan_medicine(self):
        """Capture and scan medicine label"""
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Camera not available")
            return

        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image")
            return

        # Disable scan button during processing
        self.scan_btn.configure(state=tk.DISABLED, text="Processing...")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Processing image...\n")

        # Process in separate thread to avoid blocking UI
        thread = threading.Thread(target=self.process_frame, args=(frame,))
        thread.daemon = True
        thread.start()

    def process_frame(self, frame):
        """Process captured frame with OCR"""
        try:
            # Preprocess image for better OCR
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply some image processing to improve OCR
            processed = cv2.bilateralFilter(gray, 9, 75, 75)
            processed = cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)

            # Perform OCR
            results = self.reader.readtext(processed)

            # Extract and parse text
            extracted_text = []
            for detection in results:
                text = detection[1]
                confidence = detection[2]
                if confidence > 0.3:  # Filter low confidence detections
                    extracted_text.append(text)

            # Parse medicine information
            medicine_info = self.parse_medicine_info(extracted_text)

            # Update UI in main thread
            self.scan_window.after(0, self.update_results, medicine_info, extracted_text)

        except Exception as e:
            print(f"OCR processing error: {e}")
            self.scan_window.after(0, self.update_results, {}, [f"Error: {str(e)}"])

    # def parse_medicine_info(self, text_list):
    #     """Parse medicine information from OCR text"""
    #     info = {
    #         'name': '',
    #         'batch_number': '',
    #         'expiry_date': '',
    #         'quantity': '',
    #         'manufacturer': '',
    #         'description': ''
    #     }
    #
    #     all_text = ' '.join(text_list).upper()
    #
    #     # Try to extract medicine name (usually the first or most prominent text)
    #     if text_list:
    #         # Look for medicine name patterns
    #         for text in text_list:
    #             if len(text) > 3 and not re.search(r'\d{2,}', text):
    #                 if not info['name'] or len(text) > len(info['name']):
    #                     info['name'] = text.strip()
    #
    #     # Extract batch number
    #     batch_patterns = [
    #         r'BATCH[:\s]*([A-Z0-9]+)',
    #         r'LOT[:\s]*([A-Z0-9]+)',
    #         r'B[:\s]*([A-Z0-9]{4,})',
    #         r'BATCH NO[:\s]*([A-Z0-9]+)'
    #     ]
    #
    #     for pattern in batch_patterns:
    #         match = re.search(pattern, all_text)
    #         if match:
    #             info['batch_number'] = match.group(1)
    #             break
    #
    #     # Extract expiry date
    #     date_patterns = [
    #         r'EXP[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
    #         r'EXPIRY[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
    #         r'EXP DATE[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
    #         r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
    #         r'(\d{2,4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})'
    #     ]
    #
    #     for pattern in date_patterns:
    #         match = re.search(pattern, all_text)
    #         if match:
    #             info['expiry_date'] = match.group(1)
    #             break
    #
    #     # Extract quantity
    #     quantity_patterns = [
    #         r'(\d+)\s*(?:TABLETS?|CAPS?|ML|MG|GM?)',
    #         r'QTY[:\s]*(\d+)',
    #         r'QUANTITY[:\s]*(\d+)',
    #         r'(\d+)\s*(?:PCS?|PIECES?)'
    #     ]
    #
    #     for pattern in quantity_patterns:
    #         match = re.search(pattern, all_text)
    #         if match:
    #             info['quantity'] = match.group(1)
    #             break
    #
    #     # Extract manufacturer
    #     mfg_patterns = [
    #         r'MFG[:\s]*([A-Z\s]+)',
    #         r'MANUFACTURED BY[:\s]*([A-Z\s]+)',
    #         r'MFD BY[:\s]*([A-Z\s]+)'
    #     ]
    #
    #     for pattern in mfg_patterns:
    #         match = re.search(pattern, all_text)
    #         if match:
    #             info['manufacturer'] = match.group(1).strip()
    #             break
    #
    #     return info
    def populate_fields_from_text(self, text):
        lines = text.splitlines()
        found_qty = found_exp = found_name = False
        date_pattern1 = re.compile(r'\d{4}-\d{2}-\d{2}')
        date_pattern2 = re.compile(r'\d{2}/\d{2}/\d{4}')
        qty_pattern = re.compile(r'(\d+)\s*(tabs|tablets|caps|capsules|ml|pcs|pieces|qty|quantity)?', re.I)

        for line in lines:
            l = line.lower().strip()
            if not found_qty:
                m = qty_pattern.search(l)
                if m:
                    qty = m.group(1)
                    self.med_qty.delete(0, tk.END)
                    self.med_qty.insert(0, qty)
                    found_qty = True
            if not found_exp:
                m1 = date_pattern1.search(l)
                m2 = date_pattern2.search(l)
                if m1:
                    self.med_expiry.delete(0, tk.END)
                    self.med_expiry.insert(0, m1.group(0))
                    found_exp = True
                elif m2:
                    d, m, y = m2.group(0).split('/')
                    self.med_expiry.delete(0, tk.END)
                    self.med_expiry.insert(0, f"{y}-{m}-{d}")
                    found_exp = True
            if not found_name and len(l) > 3 and not any(x in l for x in ["qty", "quantity", "exp", "expiry"]):
                self.med_name.delete(0, tk.END)
                self.med_name.insert(0, line.strip())
                found_name = True
        self.med_category.set("Tablet")

    def update_results(self, medicine_info, raw_text):
        """Update results in the GUI"""
        try:
            # Re-enable scan button
            self.scan_btn.configure(state=tk.NORMAL, text="📷 Scan Medicine")

            # Clear and update results
            self.results_text.delete(1.0, tk.END)

            if medicine_info:
                self.results_text.insert(tk.END, "=== EXTRACTED INFORMATION ===\n\n")

                for key, value in medicine_info.items():
                    if value:
                        display_key = key.replace('_', ' ').title()
                        self.results_text.insert(tk.END, f"{display_key}: {value}\n")

                self.results_text.insert(tk.END, "\n=== RAW TEXT ===\n")
                for text in raw_text:
                    self.results_text.insert(tk.END, f"• {text}\n")

                # Enable add to inventory button
                self.add_btn.configure(state=tk.NORMAL)
                self.scanned_info = medicine_info

            else:
                self.results_text.insert(tk.END, "No medicine information detected.\n")
                self.results_text.insert(tk.END, "\nRaw text found:\n")
                for text in raw_text:
                    self.results_text.insert(tk.END, f"• {text}\n")

                self.add_btn.configure(state=tk.DISABLED)

        except Exception as e:
            print(f"Error updating results: {e}")

    def add_to_inventory(self):
        """Add scanned medicine to inventory"""
        if hasattr(self, 'scanned_info') and self.callback:
            self.callback(self.scanned_info)
            self.close_scanner()

    def close_scanner(self):
        """Close the scanner window"""
        self.scanning = False
        if self.cap:
            self.cap.release()
        if self.scan_window:
            self.scan_window.destroy()