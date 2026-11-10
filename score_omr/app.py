"""One-image-at-a-time desktop interface. No upload or server needed."""
import queue
from pathlib import Path
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk
from .converter import BASE, convert, tools


class App:
    def __init__(self, root):
        self.root = root
        root.title('Ảnh bản nhạc → MuseScore')
        root.geometry('900x800')
        root.minsize(760, 700)
        self.messages = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.result = None
        self.source = tk.StringVar()
        self.enhance = tk.BooleanVar(value=True)
        self.profile = tk.StringVar(value='Tự động (bảo toàn ảnh rõ)')
        self.profile_names = {'Tự động (bảo toàn ảnh rõ)': 'auto',
                              'Ảnh rõ / scan: giữ xử lý cũ': 'legacy',
                              'Thử nghiệm sửa cong khuông, 2 lượt': 'photo',
                              'Thử nghiệm chỉnh nghiêng toàn trang': 'deskew',
                              'Giữ nguyên độ phân giải': 'original'}
        self.status = tk.StringVar(value='Chọn một ảnh bản nhạc rõ nét để bắt đầu.')
        frame = ttk.Frame(root, padding=22)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Ảnh bản nhạc → MuseScore', font=('', 23, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Chuyển từng ảnh nhỏ • xử lý trên máy • kết quả có thể chỉnh sửa').pack(anchor='w', pady=(5, 18))
        row = ttk.Frame(frame)
        row.pack(fill='x')
        self.choose = ttk.Button(row, text='1. Chọn ảnh…', command=self.pick)
        self.choose.pack(side='left')
        ttk.Entry(row, textvariable=self.source, state='readonly').pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.preview = ttk.Label(frame, text='PNG · JPG · TIFF · BMP · WebP', anchor='center')
        self.preview.pack(fill='both', expand=True, pady=15)
        ttk.Checkbutton(frame, text='Tiền xử lý ảnh: tương phản, phóng ảnh nhỏ, thêm lề (có thể nhận sai)', variable=self.enhance).pack(anchor='w')
        self.profile_box = ttk.Combobox(frame, textvariable=self.profile, values=list(self.profile_names),
                                        state='readonly', width=48)
        self.profile_box.pack(anchor='w', pady=(8, 0))
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=15)
        self.start = ttk.Button(row, text='2. Chuyển sang .mscz', command=self.start_conversion)
        self.start.pack(side='left')
        self.stop = ttk.Button(row, text='Hủy', command=self.cancel.set, state='disabled')
        self.stop.pack(side='left', padx=10)
        self.open_score = ttk.Button(row, text='Mở trong MuseScore', command=self.open_result, state='disabled')
        self.open_score.pack(side='right')
        self.open_folder = ttk.Button(row, text='Thư mục kết quả', command=self.reveal, state='disabled')
        self.open_folder.pack(side='right', padx=10)
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x')
        ttk.Label(frame, textvariable=self.status, wraplength=780).pack(anchor='w', pady=10)
        self.details = tk.Text(frame, height=6, wrap='word', state='disabled')
        self.details.pack(fill='x')
        ttk.Label(frame, text='Luôn nghe và đối chiếu nốt với ảnh gốc. Nhận dạng tự động có thể có sai sót.',
                  wraplength=780).pack(anchor='w', pady=(10, 0))
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(150, self.poll)

    def write(self, value):
        self.details.configure(state='normal')
        self.details.insert('end', value + '\n')
        self.details.see('end')
        self.details.configure(state='disabled')

    def pick(self):
        path = filedialog.askopenfilename(initialdir=BASE / "samples/images", title='Chọn ảnh bản nhạc',
                                          filetypes=[('Ảnh', '*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp')])
        if path:
            try:
                with Image.open(path) as im:
                    im = ImageOps.exif_transpose(im).convert('RGB')
                    im.thumbnail((780, 300))
                    self.photo = ImageTk.PhotoImage(im)
                self.preview.configure(image=self.photo, text='')
                self.source.set(path)
                self.result = None
                self.open_score.configure(state='disabled')
                self.open_folder.configure(state='disabled')
                self.status.set('Sẵn sàng chuyển đổi.')
            except Exception as exc:
                messagebox.showerror('Không mở được ảnh', str(exc))

    def start_conversion(self):
        if self.busy:
            return
        if not self.source.get():
            self.pick()
            if not self.source.get():
                return
        try:
            tools()
        except Exception as exc:
            messagebox.showerror('Thiếu công cụ', str(exc))
            return
        self.busy = True
        self.cancel.clear()
        self.result = None
        for button in (self.choose, self.start, self.open_score, self.open_folder):
            button.configure(state='disabled')
        self.stop.configure(state='normal')
        self.profile_box.configure(state='disabled')
        self.details.configure(state='normal')
        self.details.delete('1.0', 'end')
        self.details.configure(state='disabled')
        self.progress.configure(mode='indeterminate', value=0)
        self.progress.start(12)
        source, enhance = self.source.get(), self.enhance.get()
        profile = self.profile_names[self.profile.get()]

        def work():
            try:
                result = convert(source, enhance=enhance,
                                 notify=lambda s: self.messages.put(('status', s)), cancel=self.cancel,
                                 profile=profile)
                self.messages.put(('done', result))
            except Exception as exc:
                self.messages.put(('error', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == 'status':
                    self.status.set(value)
                    self.write(value)
                else:
                    self.busy = False
                    self.progress.stop()
                    self.progress.configure(mode='determinate', value=100 if kind == 'done' else 0)
                    self.profile_box.configure(state='readonly')
                    self.choose.configure(state='normal')
                    self.start.configure(state='normal')
                    self.stop.configure(state='disabled')
                    if kind == 'done':
                        self.result = value
                        folder, report = value
                        self.open_score.configure(state='normal')
                        self.open_folder.configure(state='normal')
                        warnings = sum(len(r['warnings']) for r in report['results'])
                        engine_warnings = len(report['recognition_warnings'])
                        self.status.set(f'Đã xuất file — chưa xác minh đúng nốt. {warnings} cảnh báo cấu trúc; '
                                        f"{report['review_priority_count']} ký hiệu ưu tiên xem lại.")
                        self.write(str(folder))
                        self.write((folder / 'Kiem_tra.txt').read_text(encoding='utf-8'))
                    else:
                        self.status.set('Chưa hoàn tất chuyển đổi.')
                        self.write(value)
                        messagebox.showerror('Chuyển đổi chưa hoàn tất', value)
        except queue.Empty:
            pass
        self.root.after(150, self.poll)

    def open_result(self):
        if self.result:
            subprocess.Popen(['open', '-a', 'MuseScore 4', self.result[1]['results'][0]['mscz']])

    def reveal(self):
        if self.result:
            subprocess.Popen(['open', str(self.result[0])])

    def close(self):
        if self.busy:
            self.cancel.set()
            self.status.set('Đang dừng xử lý; cửa sổ sẽ đóng…')
            self.root.after(300, self.close)
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
