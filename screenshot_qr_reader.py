import tkinter as tk
import mss
import numpy as np
import threading
import time
from PIL import Image
from pyzbar.pyzbar import decode

class ScreenQRScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen QR Reader")
        self.root.geometry("300x150")
        
        # Tombol utama untuk mulai memilih area
        self.btn_select = tk.Button(
            root, 
            text="Pilih Area Layar", 
            command=self.start_selection,
            bg="#4CAF50", 
            fg="white", 
            font=("Arial", 12, "bold"),
            padx=10,
            pady=5
        )
        self.btn_select.pack(expand=True)
        
        # Label status
        self.label_status = tk.Label(root, text="Status: Siap", font=("Arial", 10))
        self.label_status.pack(pady=10)
        
        # Variabel koordinat seleksi
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.is_scanning = False
        
        # PENGUNCI POP-UP: Mencegah pop-up muncul berlapis-lapis
        self.popup_open = False 

    def start_selection(self):
        self.is_scanning = False
        
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.3)
        self.overlay.config(cursor="cross")
        
        self.canvas = tk.Canvas(self.overlay, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline="red", width=2)

    def on_move_press(self, event):
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)
        
        self.overlay.destroy()
        
        if width > 10 and height > 10:
            monitor_area = {"top": top, "left": left, "width": width, "height": height}
            self.label_status.config(text="Status: Memindai area terpilih...")
            
            self.is_scanning = True
            scan_thread = threading.Thread(target=self.scan_loop, args=(monitor_area,), daemon=True)
            scan_thread.start()
        else:
            self.label_status.config(text="Status: Seleksi terlalu kecil/batal.")

    def scan_loop(self, monitor_area):
        with mss.mss() as sct:
            while self.is_scanning:
                try:
                    # JIKA POP-UP MASIH TERBUKA, lewati pemindaian untuk sementara waktu
                    if self.popup_open:
                        time.sleep(0.5)
                        continue

                    screen_shot = sct.grab(monitor_area)
                    img = Image.frombytes("RGB", screen_shot.size, screen_shot.bgra, "raw", "BGRX")
                    
                    decoded_objects = decode(img)
                    
                    for obj in decoded_objects:
                        qr_data = obj.data.decode("utf-8")
                        
                        # Set kunci pop_open ke True agar loop berikutnya mengantre
                        self.popup_open = True
                        
                        # Kirim data ke GUI utama
                        self.root.after(0, self.update_status_success, qr_data)
                        
                        # Keluar dari loop objek untuk memproses satu QR terlebih dahulu
                        break 
                        
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error saat memindai: {e}")
                    break

    def update_status_success(self, data):
        print(f"\n[TERDETEKSI] Data QR Code: {data}")
        self.label_status.config(text=f"Terdeteksi: {data[:25]}...")
        
        result_window = tk.Toplevel(self.root)
        result_window.title("Hasil QR Code")
        result_window.geometry("400x150")
        
        # Jika jendela hasil ditutup oleh user, ubah status kunci kembali ke False
        result_window.protocol("WM_DELETE_WINDOW", lambda: self.close_popup(result_window))
        
        text_widget = tk.Text(result_window, wrap="word", height=4)
        text_widget.insert("1.0", data)
        text_widget.config(state="disabled")
        text_widget.pack(padx=10, pady=10, fill="both", expand=True)

    def close_popup(self, window):
        # Hancurkan jendela pop-up
        window.destroy()
        # Buka kembali kunci pemindaian layar
        self.popup_open = False
        self.label_status.config(text="Status: Memindai area terpilih...")

if __name__ == "__main__":
    window = tk.Tk()
    app = ScreenQRScanner(window)
    window.mainloop()
