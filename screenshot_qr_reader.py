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

    def start_selection(self):
        # Hentikan scanning yang sedang berjalan jika ada
        self.is_scanning = False
        
        # Buat jendela fullscreen transparan/overlay untuk seleksi area
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.3)  # Membuat layar agak redup
        self.overlay.config(cursor="cross")
        
        # Canvas untuk menggambar kotak seleksi
        self.canvas = tk.Canvas(self.overlay, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        
        # Bind event mouse
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        # Simpan koordinat awal klik mouse
        self.start_x = event.x
        self.start_y = event.y
        # Buat kotak awal
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline="red", width=2)

    def on_move_press(self, event):
        cur_x, cur_y = event.x, event.y
        # Perbarui ukuran kotak saat mouse di-drag
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        
        # Hitung koordinat top, left, width, height yang valid
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)
        
        # Tutup jendela overlay seleksi
        self.overlay.destroy()
        
        # Validasi jika area terlalu kecil
        if width > 10 and height > 10:
            monitor_area = {"top": top, "left": left, "width": width, "height": height}
            self.label_status.config(text="Status: Memindai area terpilih...")
            
            # Jalankan fungsi pemindaian di thread terpisah agar GUI tidak membeku (freeze)
            self.is_scanning = True
            scan_thread = threading.Thread(target=self.scan_loop, args=(monitor_area,), daemon=True)
            scan_thread.start()
        else:
            self.label_status.config(text="Status: Seleksi terlalu kecil/batal.")

    def scan_loop(self, monitor_area):
        with mss.mss() as sct:
            while self.is_scanning:
                try:
                    # Ambil gambar dari area yang sudah dipilih pengguna
                    screen_shot = sct.grab(monitor_area)
                    img = Image.frombytes("RGB", screen_shot.size, screen_shot.bgra, "raw", "BGRX")
                    
                    # Dekode QR Code
                    decoded_objects = decode(img)
                    
                    for obj in decoded_objects:
                        qr_data = obj.data.decode("utf-8")
                        
                        # Perbarui teks status di window utama Tkinter secara aman
                        self.root.after(0, self.update_status_success, qr_data)
                        
                        # Berikan jeda pemindaian jika QR berhasil ditemukan
                        time.sleep(2)
                        
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error saat memindai: {e}")
                    break

    def update_status_success(self, data):
        print(f"\n[TERDETEKSI] Data QR Code: {data}")
        self.label_status.config(text=f"Terdeteksi: {data[:25]}...")
        
        # Membuka dialog box pop-up hasil teks QR
        result_window = tk.Toplevel(self.root)
        result_window.title("Hasil QR Code")
        result_window.geometry("400x150")
        
        text_widget = tk.Text(result_window, wrap="word", height=4)
        text_widget.insert("1.0", data)
        text_widget.config(state="disabled") # Mengunci teks agar hanya bisa dibaca/disalin
        text_widget.pack(padx=10, pady=10, fill="both", expand=True)

if __name__ == "__main__":
    window = tk.Tk()
    app = ScreenQRScanner(window)
    window.mainloop()
