from Xlib import X, display, Xutil, Xatom
from Xlib.protocol import event
import sys
import time
import subprocess


dpy = display.Display()
screen = dpy.screen()
root = screen.root

windows = {}
dragging = None

def create_window(client):
    geom = client.get_geometry()
    x, y = 100, 100
    width, height = geom.width, geom.height

    # Reparent into root and move to position
    client.reparent(root, x, y)
    client.configure(x=x, y=y)
    client.map()

    windows[client.id] = {
        'client': client,
        'geometry': (x, y, width, height)
    }

    dpy.flush()

def handle_map_request(e):
    win = e.window
    if win.id not in windows:
        win.change_attributes(event_mask=X.FocusChangeMask | X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask)
        create_window(win)

def handle_button_press(e):
    global dragging
    for cid, win in windows.items():
        if win['client'].id == e.window.id:
            if e.detail == 1:  # left click
                dragging = {
                    'client_id': cid,
                    'start_pos': (e.root_x, e.root_y),
                    'start_geom': win['client'].get_geometry()
                }


def handle_motion(e):
    global dragging
    if dragging:
        dx = e.root_x - dragging['start_pos'][0]
        dy = e.root_y - dragging['start_pos'][1]
        cid = dragging['client_id']
        geom = dragging['start_geom']
        windows[cid]['client'].configure(x=geom.x + dx, y=geom.y + dy)
        dpy.flush()

def handle_button_release(e):
    global dragging
    dragging = None

def spawn_menu():
    subprocess.Popen(["python3", "desk.py"])

def main():
    root.change_attributes(event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    dpy.flush()

    spawn_menu()

    while True:
        if dpy.pending_events():
            e = dpy.next_event()

            if isinstance(e, event.MapRequest):
                handle_map_request(e)
            elif isinstance(e, event.ButtonPress):
                handle_button_press(e)
            elif isinstance(e, event.MotionNotify):
                handle_motion(e)
            elif isinstance(e, event.ButtonRelease):
                handle_button_release(e)
        else:
            time.sleep(0.01)

if __name__ == "__main__":
    main()
