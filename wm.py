from Xlib import X, XK, display, Xutil
import subprocess
import os
import time

disp = display.Display()
root = disp.screen().root

MOD = X.Mod1Mask
KEYS = {
    'J': XK.XK_j,
    'K': XK.XK_k,
    'Return': XK.XK_Return,
    'Q': XK.XK_q
}

IPC_FILE = "/tmp/pwdesk_ipc"
NUM_WORKSPACES = 9
workspaces = [[] for _ in range(NUM_WORKSPACES)]
current_ws = 0
focus_idx = 0

drag_win = None
drag_start = (0, 0)
drag_mode = None

def grab_keys():
    for keysym in KEYS.values():
        code = disp.keysym_to_keycode(keysym)
        root.grab_key(code, MOD, True, X.GrabModeAsync, X.GrabModeAsync)

    for i in range(1, 10):
        code = disp.keysym_to_keycode(XK.XK_0 + i)
        root.grab_key(code, MOD, True, X.GrabModeAsync, X.GrabModeAsync)

def tile_windows():
    clients = workspaces[current_ws]
    if not clients:
        return

    screen = disp.screen()
    sw = screen.width_in_pixels
    sh = screen.height_in_pixels

    master_size = int(sw * 0.6)
    stack_size = sw - master_size

    for i, win in enumerate(clients):
        try:
            if i == 0:
                win.configure(x=0, y=0, width=master_size, height=sh, border_width=1)
            else:
                h = sh // (len(clients) - 1)
                win.configure(x=master_size, y=(i - 1) * h, width=stack_size, height=h, border_width=1)
            win.map()
        except:
            pass

def focus_window(index):
    clients = workspaces[current_ws]
    if not clients:
        return
    try:
        win = clients[index]
        win.set_input_focus(X.RevertToPointerRoot, X.CurrentTime)
        win.raise_window()
    except:
        pass

def change_workspace(n):
    global current_ws, focus_idx
    for win in workspaces[current_ws]:
        try:
            win.unmap()
        except:
            pass

    current_ws = n
    focus_idx = 0
    tile_windows()
    focus_window(focus_idx)

    with open(IPC_FILE, "w") as f:
        f.write(str(current_ws + 1))

def handle_key(event):
    global focus_idx
    keysym = disp.keycode_to_keysym(event.detail, 0)

    if keysym == KEYS['J']:
        if workspaces[current_ws]:
            focus_idx = (focus_idx + 1) % len(workspaces[current_ws])
            focus_window(focus_idx)
    elif keysym == KEYS['K']:
        if workspaces[current_ws]:
            focus_idx = (focus_idx - 1) % len(workspaces[current_ws])
            focus_window(focus_idx)
    elif keysym == KEYS['Return']:
        subprocess.Popen(["xterm"])
    elif keysym == KEYS['Q']:
        print("Выход из WM")
        os._exit(0)
    elif XK.XK_1 <= keysym <= XK.XK_9:
        ws = keysym - XK.XK_1
        if ws < NUM_WORKSPACES:
            change_workspace(ws)

def setup():
    root.change_attributes(
        event_mask=X.SubstructureRedirectMask |
                   X.SubstructureNotifyMask |
                   X.ButtonPressMask |
                   X.ButtonReleaseMask |
                   X.ButtonMotionMask |
                   X.KeyPressMask
    )
    grab_keys()

    subprocess.Popen(["python3", os.path.abspath("desk.py")])

    #wallpaper_path = os.path.expanduser("~/Pictures/wallpaper.jpg")
    #if os.path.exists(wallpaper_path):
        #subprocess.Popen(["feh", "--bg-scale", wallpaper_path])

    with open(IPC_FILE, "w") as f:
        f.write(str(current_ws + 1))

setup()

print("PWDesk WM запущен. Alt+Enter - терминал, Alt+J/K - фокус, Alt+1-9 - WS, Alt+Q - выход")
print("Alt + ЛКМ - перемещение окна, Alt + ПКМ - ресайз окна")

while True:
    event = disp.next_event()

    if event.type == X.MapRequest:
        win = event.window
        workspaces[current_ws].append(win)
        tile_windows()

    elif event.type == X.DestroyNotify:
        for ws in workspaces:
            ws[:] = [w for w in ws if w.id != event.window.id]
        tile_windows()

    elif event.type == X.KeyPress:
        handle_key(event)

    elif event.type == X.ButtonPress:
        if event.state & MOD:
            drag_win = event.child
            drag_start = (event.root_x, event.root_y)
            if event.detail == 1:
                drag_mode = "move"
            elif event.detail == 3:
                drag_mode = "resize"

    elif event.type == X.ButtonRelease:
        drag_win = None
        drag_mode = None

    elif event.type == X.MotionNotify:
        if 'drag_win' in globals() and drag_win and drag_mode:
            dx = event.root_x - drag_start[0]
            dy = event.root_y - drag_start[1]
            try:
                geom = drag_win.get_geometry()
                if drag_mode == "move":
                    drag_win.configure(x=geom.x + dx, y=geom.y + dy)
                elif drag_mode == "resize":
                    drag_win.configure(width=max(geom.width + dx, 100),
                                       height=max(geom.height + dy, 100))
            except:
                pass
            drag_start = (event.root_x, event.root_y)

    disp.sync()
