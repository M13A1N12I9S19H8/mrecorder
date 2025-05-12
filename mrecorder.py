import cv2
import numpy as np
import pyautogui
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import datetime
import pystray
import sys
import os

recording = False
out = None
webcam_cap = None
start_time = None
save_path = None
webcam_enabled = True
tray_icon = None
webcam_preview_running = False
floating_stop_btn = None

def start_recording():
    global save_path
    if not save_path:
        messagebox.showwarning("No file path", "Please select a file path to save the recording.")
        return

    root.withdraw()  # Hide GUI first
    show_countdown()  # Show countdown first

def show_countdown():
    countdown_win = tk.Toplevel()
    countdown_win.overrideredirect(True)
    countdown_win.geometry("300x200+600+300")
    countdown_win.attributes("-topmost", True)
    countdown_win.configure(bg="black")

    label = tk.Label(countdown_win, text="", font=("Arial", 48), fg="white", bg="black")
    label.pack(expand=True)

    def run_countdown(n):
        if n > 0:
            label.config(text=str(n))
            countdown_win.after(1000, run_countdown, n - 1)
        else:
            countdown_win.destroy()
            begin_actual_recording()

    run_countdown(3)

def begin_actual_recording():
    global recording, out, webcam_cap, start_time
    recording = True
    start_time = datetime.datetime.now()

    screen_width, screen_height = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(save_path, fourcc, 20.0, (screen_width, screen_height))

    if webcam_enabled:
        if webcam_cap is None or not webcam_cap.isOpened():
            webcam_cap = cv2.VideoCapture(0)

    threading.Thread(target=record).start()
    update_timer()
    show_floating_stop_button()

def stop_recording():
    global recording, out, webcam_cap
    recording = False
    if webcam_cap:
        webcam_cap.release()
        webcam_cap = None
    if out:
        out.release()
    root.deiconify()
    hide_floating_stop_button()
    messagebox.showinfo("Saved", f"Recording saved to:\n{save_path}")
    timer_label.config(text="00:00:00")
    webcam_preview_label.config(image='')

def update_timer():
    if recording:
        elapsed = datetime.datetime.now() - start_time
        timer_label.config(text=str(elapsed).split(".")[0])
        root.after(1000, update_timer)

def record():
    screen_width, screen_height = pyautogui.size()
    while recording:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if webcam_enabled and webcam_cap and webcam_cap.isOpened():
            ret, webcam_frame = webcam_cap.read()
            if ret:
                webcam_frame = cv2.resize(webcam_frame, (200, 150))
                frame[10:160, screen_width - 210:screen_width - 10] = webcam_frame

        out.write(frame)

def browse_file():
    global save_path
    f = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI files", "*.avi")])
    if f:
        save_path = f
        file_label.config(text=os.path.basename(f))

def toggle_webcam():
    global webcam_enabled
    webcam_enabled = webcam_var.get()
    if webcam_enabled:
        start_webcam_preview()
    else:
        webcam_preview_label.config(image='')

def start_webcam_preview():
    global webcam_cap, webcam_preview_running
    if not webcam_enabled:
        return

    if webcam_cap is None or not webcam_cap.isOpened():
        webcam_cap = cv2.VideoCapture(0)

    if not webcam_preview_running:
        webcam_preview_running = True

        def update_preview():
            if not webcam_enabled:
                webcam_preview_label.config(image='')
                return
            if webcam_cap and webcam_cap.isOpened():
                ret, frame = webcam_cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (200, 150))
                    img = Image.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    webcam_preview_label.imgtk = imgtk
                    webcam_preview_label.config(image=imgtk)
            if webcam_preview_running:
                root.after(100, update_preview)

        update_preview()

def minimize_to_tray():
    root.withdraw()
    image = Image.open("logo.png").resize((64, 64))
    menu = pystray.Menu(pystray.MenuItem('Restore', restore_window), pystray.MenuItem('Exit', quit_app))
    global tray_icon
    tray_icon = pystray.Icon("mrecorder", image, "mrecorder", menu)
    threading.Thread(target=tray_icon.run).start()

def restore_window():
    root.deiconify()
    if tray_icon:
        tray_icon.stop()

def quit_app():
    stop_recording()
    if tray_icon:
        tray_icon.stop()
    root.destroy()
    sys.exit()

def show_floating_stop_button():
    global floating_stop_btn
    if floating_stop_btn:
        return

    floating_stop_btn = tk.Toplevel()
    floating_stop_btn.overrideredirect(True)
    floating_stop_btn.geometry("60x60+20+20")
    floating_stop_btn.attributes("-topmost", True)
    floating_stop_btn.configure(bg="black")

    stop_button = tk.Button(floating_stop_btn, text="■", fg="white", bg="red", font=("Arial", 20),
                            command=stop_recording)
    stop_button.pack(expand=True, fill=tk.BOTH)

def hide_floating_stop_button():
    global floating_stop_btn
    if floating_stop_btn:
        floating_stop_btn.destroy()
        floating_stop_btn = None

# GUI Setup
root = tk.Tk()
root.title("mrecorder")
root.geometry("320x400")
root.resizable(False, False)

tk.Label(root, text="Save file:").pack(pady=(10, 0))
file_frame = tk.Frame(root)
file_frame.pack()
file_label = tk.Label(file_frame, text="No file selected", width=25)
file_label.pack(side=tk.LEFT, padx=5)
tk.Button(file_frame, text="Browse", command=browse_file).pack(side=tk.RIGHT)

webcam_var = tk.BooleanVar(value=True)
webcam_check = tk.Checkbutton(root, text="Include Webcam", var=webcam_var, command=toggle_webcam)
webcam_check.pack(pady=10)

start_btn = tk.Button(root, text="Start Recording", bg="green", fg="white", width=25, command=start_recording)
start_btn.pack(pady=10)

stop_btn = tk.Button(root, text="Stop Recording", bg="red", fg="white", width=25, command=stop_recording)
stop_btn.pack(pady=5)

timer_label = tk.Label(root, text="00:00:00", font=("Arial", 16))
timer_label.pack(pady=5)

tk.Label(root, text="Webcam Preview:").pack()
webcam_preview_label = tk.Label(root)
webcam_preview_label.pack()

min_btn = tk.Button(root, text="Minimize to Tray", command=minimize_to_tray)
min_btn.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", minimize_to_tray)

start_webcam_preview()
root.mainloop()
