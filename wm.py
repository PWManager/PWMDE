#!/usr/bin/env python3
from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq
import sys
import subprocess
import time
import threading
from datetime import datetime

MODKEY = int(X.Mod1Mask)
KEY_J = XK.string_to_keysym('j')
KEY_K = XK.string_to_keysym('k')
KEY_ENTER = XK.string_to_keysym('Return')
KEY_Q = XK.string_to_keysym('q')

class WM:
    def __init__(self):
        self.disp = display.Display()
        self.root = self.disp.screen().root
        self.clients = []
        self.focused = 0
        self.running = True
        self.setup()
        self.spawn_xterm()

    def setup(self):
        self.root.change_attributes(event_mask=(X.SubstructureRedirectMask | X.SubstructureNotifyMask | X.ButtonPressMask))
        self.grab_keys()

    def grab_keys(self):
        for keysym in [KEY_J, KEY_K, KEY_ENTER, KEY_Q]:
            keycode = self.disp.keysym_to_keycode(keysym)
            self.root.grab_key(int(keycode), MODKEY, 1, X.GrabModeAsync, X.GrabModeAsync)

    def spawn_xterm(self):
        subprocess.Popen(['xterm'])

    def run(self):
        while self.running:
            e = self.disp.next_event()
            if e.type == X.MapRequest:
                self.manage(e.window)
            elif e.type == X.DestroyNotify:
                self.unmanage(e.window)
            elif e.type == X.UnmapNotify:
                self.unmanage(e.window)
            elif e.type == X.KeyPress:
                self.handle_key(e)

    def manage(self, win):
        if win not in self.clients:
            self.clients.append(win)
        win.map()
        self.tile()

    def unmanage(self, win):
        if win in self.clients:
            self.clients.remove(win)
            if self.focused >= len(self.clients):
                self.focused = max(0, len(self.clients) - 1)
            self.tile()

    def tile(self):
        n = len(self.clients)
        if n == 0:
            return
        sw = int(self.root.get_geometry().width)
        sh = int(self.root.get_geometry().height)
        master_w = int(sw * 0.6)
        stack_w = sw - master_w
        for i, win in enumerate(self.clients):
            if i == 0:
                win.configure(x=0, y=0, width=master_w, height=sh, border_width=2)
            else:
                if n > 1:
                    h = sh // (n - 1)
                    win.configure(x=master_w, y=(i-1)*h, width=stack_w, height=h, border_width=2)
            if i == self.focused:
                win.set_input_focus(X.RevertToPointerRoot, X.CurrentTime)
                win.configure(border_pixel=int(self.disp.screen().black_pixel))
            else:
                win.configure(border_pixel=int(self.disp.screen().white_pixel))
        self.disp.sync()

    def handle_key(self, e):
        keycode = e.detail
        keysym = self.disp.keycode_to_keysym(keycode, 0)
        if keysym == KEY_J:
            self.focused = (self.focused + 1) % len(self.clients)
            self.tile()
        elif keysym == KEY_K:
            self.focused = (self.focused - 1) % len(self.clients)
            self.tile()
        elif keysym == KEY_ENTER:
            if self.focused != 0:
                self.clients[0], self.clients[self.focused] = self.clients[self.focused], self.clients[0]
                self.focused = 0
                self.tile()
        elif keysym == KEY_Q:
            self.running = False
            self.disp.close()
            sys.exit(0)

if __name__ == '__main__':
    try:
        WM().run()
    except Exception as e:
        print('Error:', e)
        sys.exit(1)