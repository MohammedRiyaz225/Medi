"""
MediSort - Smart Medicine Inventory Manager
Entry point for the application
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os
from datetime import datetime
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import re
from PIL import Image
import numpy as np
from auth import AuthManager
from inventory import InventoryManager
from logic.db_handler import DatabaseManager

class MediSortApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MediSort - Smart Medicine Inventory Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        self.center_window()
        self.db_manager = DatabaseManager()
        self.auth = AuthManager(self.db_manager)
        self.current_user_id = None
        self.current_username = None
        self.create_main_interface()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_main_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.main_frame = tk.Frame(self.root, bg='#34495e')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        title_frame = tk.Frame(self.main_frame, bg='#34495e')
        title_frame.pack(pady=50)
        tk.Label(title_frame, text="🏥 MediSort",
                 font=('Arial', 36, 'bold'), fg='#ecf0f1', bg='#34495e').pack()
        tk.Label(title_frame, text="Smart Medicine Inventory Manager",
                 font=('Arial', 14), fg='#bdc3c7', bg='#34495e').pack(pady=10)
        container = tk.Frame(self.main_frame, bg='#2c3e50', padx=40, pady=30)
        container.pack(pady=30)
        self.build_login(container)
        self.build_register(container)
        self.root.bind('<Return>', lambda event: self.login_user())

    def build_login(self, container):
        frame = tk.LabelFrame(container, text="Login", font=('Arial', 14, 'bold'),
                              fg='#3498db', bg='#2c3e50', padx=20, pady=20)
        frame.grid(row=0, column=0, padx=20, pady=10)
        tk.Label(frame, text="Username:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, sticky='w', pady=5)
        self.login_username = tk.Entry(frame, font=('Arial', 12), width=25)
        self.login_username.grid(row=0, column=1, padx=10)
        tk.Label(frame, text="Password:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=1, column=0, sticky='w', pady=5)
        self.login_password = tk.Entry(frame, font=('Arial', 12), width=25, show='*')
        self.login_password.grid(row=1, column=1, padx=10)
        tk.Button(frame, text="Login", font=('Arial', 12, 'bold'), bg='#3498db', fg='white',
                  command=self.login_user, width=20, pady=8).grid(row=2, column=0, columnspan=2, pady=15)

    def build_register(self, container):
        frame = tk.LabelFrame(container, text="Register New User", font=('Arial', 14, 'bold'),
                              fg='#e74c3c', bg='#2c3e50', padx=20, pady=20)
        frame.grid(row=0, column=1, padx=20, pady=10)
        tk.Label(frame, text="Username:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, sticky='w', pady=5)
        self.reg_username = tk.Entry(frame, font=('Arial', 12), width=25)
        self.reg_username.grid(row=0, column=1, padx=10)
        tk.Label(frame, text="Password:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=1, column=0, sticky='w', pady=5)
        self.reg_password = tk.Entry(frame, font=('Arial', 12), width=25, show='*')
        self.reg_password.grid(row=1, column=1, padx=10)
        tk.Label(frame, text="Confirm Password:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=2, column=0, sticky='w', pady=5)
        self.reg_confirm_password = tk.Entry(frame, font=('Arial', 12), width=25, show='*')
        self.reg_confirm_password.grid(row=2, column=1, padx=10)
        tk.Button(frame, text="Register", font=('Arial', 12, 'bold'), bg='#e74c3c', fg='white',
                  command=self.register_user, width=20, pady=8).grid(row=3, column=0, columnspan=2, pady=15)

    def login_user(self):
        username, password = self.login_username.get().strip(), self.login_password.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        user_id = self.auth.login(username, password)
        if user_id:
            self.current_user_id, self.current_username = user_id, username
            self.create_inventory_interface()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def register_user(self):
        u, p, cp = self.reg_username.get().strip(), self.reg_password.get().strip(), self.reg_confirm_password.get().strip()
        if not u or not p or not cp:
            messagebox.showerror("Error", "Please fill all fields")
            return
        if p != cp:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if len(p) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        if self.auth.register(u, p):
            messagebox.showinfo("Success", "Registered! You can now login.")
            self.reg_username.delete(0, tk.END)
            self.reg_password.delete(0, tk.END)
            self.reg_confirm_password.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Username already exists")

    def create_inventory_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.meds_frame = tk.Frame(self.root, bg='#2c3e50')
        self.meds_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.meds_frame, text=f"🏥 MediSort - Welcome, {self.current_username}!",
                 font=('Arial', 18, 'bold'), fg='#ecf0f1', bg='#34495e').pack(fill=tk.X, pady=10)
        self.build_inventory_form()
        self.build_treeview()
        self.load_medicines()

    def build_inventory_form(self):
        panel = tk.Frame(self.meds_frame, bg='#2c3e50')
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        for txt in [("Name:", 'name'), ("Qty:", 'qty'), ("Expiry (YYYY-MM-DD):", 'expiry')]:
            tk.Label(panel, text=txt[0], font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').pack()
            setattr(self, f"med_{txt[1]}", tk.Entry(panel, font=('Arial', 12), width=25))
            getattr(self, f"med_{txt[1]}").pack(pady=2)
        tk.Label(panel, text="Category:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').pack()
        self.med_category = ttk.Combobox(panel, font=('Arial', 12), width=23,
                                         values=['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream', 'Other'])
        self.med_category.pack(pady=2)
        tk.Label(panel, text="Desc:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').pack()
        self.med_desc = tk.Text(panel, font=('Arial', 12), width=25, height=4)
        self.med_desc.pack(pady=2)
        tk.Button(panel, text="Scan via Webcam", bg='#9b59b6', fg='white', font=('Arial', 12, 'bold'),
                  command=self.scan_webcam).pack(pady=5)
        tk.Button(panel, text="Add Medicine", bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                  command=self.add_medicine).pack(pady=10)
        tk.Button(panel, text="Delete Selected", bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                  command=self.delete_selected).pack(pady=5)

    def build_treeview(self):
        tree_frame = tk.Frame(self.meds_frame, bg='#2c3e50')
        tree_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(tree_frame, columns=('ID', 'Name', 'Qty', 'Expiry', 'Cat', 'Desc'), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def load_medicines(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        with self.db_manager.get_connection() as conn:
            for r in conn.execute("SELECT id, name, quantity, expiry_date, category, description FROM medicines WHERE user_id=?", (self.current_user_id,)):
                self.tree.insert("", tk.END, values=r)

    def add_medicine(self):
        n, q, e, c, d = self.med_name.get(), self.med_qty.get(), self.med_expiry.get(), self.med_category.get(), self.med_desc.get("1.0", tk.END).strip()
        if not n or not q or not e or not c:
            messagebox.showerror("Error", "Fill all fields")
            return
        try:
            q = int(q)
            datetime.strptime(e, '%Y-%m-%d')
        except:
            messagebox.showerror("Error", "Invalid qty or date")
            return
        with self.db_manager.get_connection() as conn:
            conn.execute("INSERT INTO medicines (user_id, name, quantity, expiry_date, category, description) VALUES (?,?,?,?,?,?)",
                         (self.current_user_id, n, q, e, c, d))
        self.load_medicines()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a record to delete")
            return
        item = self.tree.item(selected[0])
        med_id = item['values'][0]
        with self.db_manager.get_connection() as conn:
            conn.execute("DELETE FROM medicines WHERE id=? AND user_id=?", (med_id, self.current_user_id))
        self.load_medicines()

    def scan_webcam(self):
        cap = cv2.VideoCapture(0)
        messagebox.showinfo("Instructions", "Press SPACE to capture, ESC to cancel.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Scan Medicine Label - Press SPACE to Capture", frame)
            k = cv2.waitKey(1)
            if k % 256 == 27:
                break
            elif k % 256 == 32:
                text = pytesseract.image_to_string(frame)
                self.populate_fields_from_text(text)
                break
        cap.release()
        cv2.destroyAllWindows()

    def populate_fields_from_text(self, text):
        lines = text.splitlines()
        for line in lines:
            l = line.lower()
            if "qty" in l or "quantity" in l:
                try: self.med_qty.delete(0, tk.END); self.med_qty.insert(0, ''.join(filter(str.isdigit, l)))
                except: pass
            elif "exp" in l or "expiry" in l:
                try: self.med_expiry.delete(0, tk.END); self.med_expiry.insert(0, l[-10:])
                except: pass
            elif len(l) > 3 and not self.med_name.get():
                self.med_name.insert(0, line.strip())
        self.med_category.set("Tablet")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    MediSortApp().run()
