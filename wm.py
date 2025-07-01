from Xlib import X, display, Xutil, Xatom
from Xlib.protocol import event
import sys
import time


dpy = display.Display()
screen = dpy.screen()
root = screen.root

windows = {}  # client_id: {frame, titlebar, client, is_minimized, geometry}

# Taskbar (list of buttons)
taskbar_height = 24
taskbar = root.create_window(
    0, screen.height_in_pixels - taskbar_height,
    screen.width_in_pixels, taskbar_height,
    0,
    screen.root_depth,
    X.InputOutput,
    X.CopyFromParent,
    background_pixel=0x222222,
    event_mask=X.ExposureMask | X.ButtonPressMask
)
taskbar.map()


# Global drag tracking
dragging = None

def create_frame(client):
    geom = client.get_geometry()
    width = geom.width
    height = geom.height
    x, y = 100, 100

    frame = root.create_window(
        x, y,
        width, height + 24,
        1,
        dpy.screen().root_depth,
        X.InputOutput,
        X.CopyFromParent,
        background_pixel=0xaaaaaa,
        event_mask=X.ExposureMask | X.SubstructureRedirectMask | X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask
    )

    titlebar = frame.create_window(
        0, 0,
        width, 24,
        0,
        dpy.screen().root_depth,
        X.InputOutput,
        X.CopyFromParent,
        background_pixel=0x444444,
        event_mask=X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask
    )

    # Reparent client window
    client.reparent(frame, 0, 24)
    client.map()
    titlebar.map()
    frame.map()

    windows[client.id] = {
        'frame': frame,
        'titlebar': titlebar,
        'client': client,
        'is_minimized': False,
        'geometry': (x, y, width, height)
    }

    dpy.flush()

def minimize_window(client_id):
    win = windows[client_id]
    win['frame'].unmap()
    win['is_minimized'] = True
    add_taskbar_button(client_id)
    dpy.flush()

def restore_window(client_id):
    win = windows[client_id]
    win['frame'].map()
    win['is_minimized'] = False
    dpy.flush()

def add_taskbar_button(client_id):
    idx = list(windows.keys()).index(client_id)
    btn_width = 100
    btn = taskbar.create_window(
        idx * btn_width, 0,
        btn_width - 2, taskbar_height,
        0,
        dpy.screen().root_depth,
        X.InputOutput,
        X.CopyFromParent,
        background_pixel=0x666666,
        event_mask=X.ButtonPressMask
    )
    btn.map()
    windows[client_id]['task_button'] = btn


def handle_map_request(e):
    win = e.window
    if win.id in windows:
        return
    win.change_attributes(event_mask=X.FocusChangeMask)
    create_frame(win)

def handle_button_press(e):
    global dragging
    for cid, win in windows.items():
        if win['titlebar'].id == e.window.id:
            if e.detail == 1:  # left click drag
                dragging = {
                    'client_id': cid,
                    'start_pos': (e.root_x, e.root_y),
                    'start_geom': win['frame'].get_geometry()
                }
            elif e.detail == 3:  # right click to minimize
                minimize_window(cid)

        elif win.get('task_button') and win['task_button'].id == e.window.id:
            restore_window(cid)
            win['task_button'].unmap()
            del win['task_button']


def handle_motion(e):
    global dragging
    if dragging:
        dx = e.root_x - dragging['start_pos'][0]
        dy = e.root_y - dragging['start_pos'][1]
        cid = dragging['client_id']
        geom = dragging['start_geom']
        windows[cid]['frame'].configure(x=geom.x + dx, y=geom.y + dy)
        dpy.flush()

def handle_button_release(e):
    global dragging
    dragging = None

def main():
    root.change_attributes(event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    dpy.flush()

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
            pass

if __name__ == "__main__":
    main()
