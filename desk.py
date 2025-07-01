import tkinter as tk
import subprocess
import datetime
import threading
import os
import time

IPC_FILE = "/tmp/pwdesk_ipc"

def launch_app(cmd):
    subprocess.Popen(cmd, shell=True)

def update_time():
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S %d.%m.%Y")
    time_label.config(text=time_str)
    root.after(1000, update_time)

def watch_workspace():
    while True:
        if os.path.exists(IPC_FILE):
            with open(IPC_FILE) as f:
                txt = f.read().strip()
                ws_label.config(text=f"WS: {txt}")
        time.sleep(0.5)

root = tk.Tk()
root.title("PWDesk Panel")
root.geometry("1024x32+0+0")
root.configure(bg="#222222")
root.attributes("-topmost", True)
root.overrideredirect(True)

# Меню приложений
menu_frame = tk.Frame(root, bg="#222222")
menu_frame.pack(side="left", padx=5)

apps = {
    "Terminal": "xterm",
    "Firefox": "firefox",
    "Files": "nautilus"
}

for name, cmd in apps.items():
    b = tk.Button(menu_frame, text=name, command=lambda c=cmd: launch_app(c),
                  bg="#444", fg="white", relief="flat", width=10)
    b.pack(side="left", padx=2)

# Метка текущего рабочего стола
ws_label = tk.Label(root, text="WS: 1", fg="white", bg="#222222", font=("Courier", 12))
ws_label.pack(side="right", padx=10)

# Метка времени
time_label = tk.Label(root, text="", fg="white", bg="#222222", font=("Courier", 12))
time_label.pack(side="right", padx=10)

update_time()

threading.Thread(target=watch_workspace, daemon=True).start()

root.mainloop()
