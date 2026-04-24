import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import os
import sys
import argparse
import threading

def apply_perceptual_transform(input_path, output_path):
    """Ядро обработки изображения (без изменений)."""
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Не удалось прочитать файл: {input_path}")
    
    img_float = img.astype(np.float32)
    h, w = img_float.shape[:2]

    center = (w / 2, h / 2)
    angle = 0.3
    scale = 1.005
    M = cv2.getRotationMatrix2D(center, angle, scale)
    M[0, 2] += 0.3
    M[1, 2] += 0.3

    img_warped = cv2.warpAffine(img_float, M, (w, h), 
                                flags=cv2.INTER_CUBIC, 
                                borderMode=cv2.BORDER_REFLECT101)

    img_smoothed = cv2.GaussianBlur(img_warped, (3, 3), 0.3)

    gaussian_noise = np.random.normal(loc=0.0, scale=1.0, size=img_smoothed.shape)
    dither_noise = np.random.uniform(low=-0.5, high=0.5, size=img_smoothed.shape)
    img_noisy = img_smoothed + gaussian_noise + dither_noise

    img_final = np.clip(img_noisy, 0, 255).astype(np.uint8)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
    success = cv2.imwrite(output_path, img_final, encode_param)
    
    if not success:
        raise IOError("Не удалось сохранить изображение.")

class MirageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mirage - Image Transformer")
        self.root.geometry("550x220")
        
        # Поддержка высокого DPI
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        self.input_path = tk.StringVar()
        self.output_folder = tk.StringVar() # Теперь храним путь к папке
        self.create_widgets()

    def create_widgets(self):
        padding = {'padx': 10, 'pady': 10}
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both", **padding)

        # Выбор файла
        tk.Label(frame, text="Исходное фото:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.input_path, width=40).grid(row=0, column=1, padx=5)
        tk.Button(frame, text="Выбрать файл", command=self.browse_input).grid(row=0, column=2)

        # Выбор папки
        tk.Label(frame, text="Папка сохранения:").grid(row=1, column=0, sticky="w", pady=10)
        tk.Entry(frame, textvariable=self.output_folder, width=40).grid(row=1, column=1, padx=5)
        tk.Button(frame, text="Выбрать папку", command=self.browse_folder).grid(row=1, column=2)

        # Кнопка старта
        self.process_btn = tk.Button(frame, text="Обработать и сохранить", 
                                     bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                                     command=self.start_processing_thread)
        self.process_btn.grid(row=2, column=0, columnspan=3, pady=20, sticky="nsew")

        self.status_label = tk.Label(frame, text="Готов к работе", fg="gray")
        self.status_label.grid(row=3, column=0, columnspan=3)

    def browse_input(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")])
        if file_path:
            self.input_path.set(file_path)
            # Если папка еще не выбрана, предлагаем папку, где лежит оригинал
            if not self.output_folder.get():
                self.output_folder.set(os.path.dirname(file_path))

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder.set(folder_path)

    def start_processing_thread(self):
        threading.Thread(target=self.process_image, daemon=True).start()

    def process_image(self):
        in_p = self.input_path.get()
        out_f = self.output_folder.get()

        if not in_p or not out_f:
            messagebox.showwarning("Внимание", "Выберите файл и папку для сохранения!")
            return

        # Формируем имя выходного файла автоматически
        file_name = os.path.basename(in_p)
        name_part, _ = os.path.splitext(file_name)
        out_p = os.path.join(out_f, f"{name_part}_mirage.jpg")

        self.process_btn.config(state="disabled")
        self.status_label.config(text="Обработка...", fg="blue")
        
        try:
            apply_perceptual_transform(in_p, out_p)
            self.status_label.config(text="Готово!", fg="green")
            messagebox.showinfo("Успех", f"Файл успешно сохранен в папку:\n{out_f}")
        except Exception as e:
            self.status_label.config(text="Ошибка", fg="red")
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.process_btn.config(state="normal")

def main():
    parser = argparse.ArgumentParser(description="Mirage CLI")
    parser.add_argument("-i", "--input", help="Путь к файлу")
    parser.add_argument("-o", "--output", help="Путь к папке или конкретному файлу")
    
    args = parser.parse_args()

    if len(sys.argv) == 1:
        root = tk.Tk()
        app = MirageApp(root)
        root.mainloop()
    else:
        # Логика для CLI
        if not args.input or not args.output:
            print("Для CLI укажите -i (файл) и -o (папка)")
            return
        
        # Если в -o передана папка, формируем имя файла сами
        if os.path.isdir(args.output):
            fname = os.path.basename(args.input)
            name, _ = os.path.splitext(fname)
            final_out = os.path.join(args.output, f"{name}_mirage.jpg")
        else:
            final_out = args.output

        try:
            apply_perceptual_transform(args.input, final_out)
            print(f"Готово: {final_out}")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()