#!/usr/bin/env python3
from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq
import sys
import subprocess
import time
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np

MODKEY = int(X.Mod1Mask)
KEY_J = XK.string_to_keysym('j')
KEY_K = XK.string_to_keysym('k')
KEY_ENTER = XK.string_to_keysym('Return')
KEY_Q = XK.string_to_keysym('q')

MENU_HEIGHT = 28
MENU_BG = (34, 34, 34)
MENU_FG = (255, 255, 255)
MENU_ITEMS = [
    ('XTerm', ['xterm']),
    ('Firefox', ['firefox']),
    ('Exit', None)
]

class WM:
    def __init__(self):
        self.disp = display.Display()
        self.root = self.disp.screen().root
        self.clients = []
        self.focused = 0
        self.menu_win = None
        self.clock_text = ''
        self.running = True
        self.menu_pixmap = None
        self.setup()
        self.start_clock_thread()

    def setup(self):
        self.root.change_attributes(event_mask=(X.SubstructureRedirectMask | X.SubstructureNotifyMask | X.ButtonPressMask))
        self.grab_keys()
        self.create_menu()

    def grab_keys(self):
        for keysym in [KEY_J, KEY_K, KEY_ENTER, KEY_Q]:
            keycode = self.disp.keysym_to_keycode(keysym)
            self.root.grab_key(int(keycode), MODKEY, 1, X.GrabModeAsync, X.GrabModeAsync)

    def create_menu(self):
        sw = int(self.root.get_geometry().width)
        self.menu_win = self.root.create_window(
            0, 0, sw, MENU_HEIGHT, 0,
            self.disp.screen().root_depth,
            X.InputOutput,
            X.CopyFromParent,
            background_pixel=self.rgb_to_pixel(MENU_BG),
            event_mask=(X.ExposureMask | X.ButtonPressMask)
        )
        self.menu_win.map()
        self.draw_menu()

    def draw_menu(self):
        sw = int(self.root.get_geometry().width)
        img = Image.new('RGB', (sw, MENU_HEIGHT), MENU_BG)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 14)
        except:
            font = ImageFont.load_default()
        x = 10
        for i, (label, _) in enumerate(MENU_ITEMS):
            draw.text((x, 6), label, font=font, fill=MENU_FG)
            x += 80
        clock_x = sw - 120
        draw.text((clock_x, 6), self.clock_text, font=font, fill=MENU_FG)
        data = np.array(img)
        pixmap = self.menu_win.create_pixmap(sw, MENU_HEIGHT, self.disp.screen().root_depth)
        gc = self.menu_win.create_gc()
        # Convert RGB to packed integer for XImage
        raw = data.astype('uint8').tobytes()
        image = self.disp.image_from_bytes(raw, sw, MENU_HEIGHT, 24)
        pixmap.put_image(gc, image, 0, 0, 0, 0, sw, MENU_HEIGHT)
        self.menu_win.copy_area(pixmap, gc, 0, 0, 0, 0, sw, MENU_HEIGHT)
        self.menu_pixmap = pixmap
        self.disp.flush()

    def rgb_to_pixel(self, rgb):
        r, g, b = rgb
        return (r << 16) | (g << 8) | b

    def update_clock(self):
        while self.running:
            self.clock_text = datetime.now().strftime('%H:%M:%S')
            self.draw_menu()
            time.sleep(1)

    def start_clock_thread(self):
        t = threading.Thread(target=self.update_clock, daemon=True)
        t.start()

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
            elif e.type == X.Expose and e.window == self.menu_win:
                self.draw_menu()
            elif e.type == X.ButtonPress and e.window == self.menu_win:
                self.handle_menu_click(e)

    def handle_menu_click(self, e):
        x = int(e.event_x)
        item_width = 80
        for i, (label, cmd) in enumerate(MENU_ITEMS):
            if 10 + i*item_width <= x < 10 + (i+1)*item_width:
                if label == 'Exit':
                    self.running = False
                    self.disp.close()
                    sys.exit(0)
                elif cmd:
                    subprocess.Popen(cmd)
                break

    def manage(self, win):
        if win == self.menu_win:
            return
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
                win.configure(x=0, y=MENU_HEIGHT, width=master_w, height=sh-MENU_HEIGHT, border_width=2)
            else:
                h = (sh-MENU_HEIGHT) // (n - 1)
                win.configure(x=master_w, y=MENU_HEIGHT+(i-1)*h, width=stack_w, height=h, border_width=2)
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