// PwdeskWM (C++) — минимальный WM с drag окнами и запуском внешнего меню
// Требует: Xlib, POSIX

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <unistd.h>
#include <cstdlib>
#include <cstring>
#include <map>

struct ClientWindow {
    Window win;
    int x, y, width, height;
};

Display* dpy;
Window root;
std::map<Window, ClientWindow> windows;

bool dragging = false;
Window drag_win;
int drag_start_x, drag_start_y;
int win_start_x, win_start_y;

void create_window(Window win) {
    XWindowAttributes attr;
    XGetWindowAttributes(dpy, win, &attr);

    int x = 100, y = 100;

    XReparentWindow(dpy, win, root, x, y);
    XMoveWindow(dpy, win, x, y);
    XMapWindow(dpy, win);

    ClientWindow cw = { win, x, y, attr.width, attr.height };
    windows[win] = cw;

    XSelectInput(dpy, win, FocusChangeMask | ButtonPressMask | ButtonReleaseMask | PointerMotionMask);
}

void handle_map_request(XEvent* ev) {
    Window win = ev->xmaprequest.window;
    if (windows.count(win) == 0) {
        create_window(win);
    }
}

void handle_button_press(XEvent* ev) {
    Window win = ev->xbutton.window;
    if (windows.count(win)) {
        if (ev->xbutton.button == Button1) {
            dragging = true;
            drag_win = win;
            drag_start_x = ev->xbutton.x_root;
            drag_start_y = ev->xbutton.y_root;

            Window junk;
            int rx, ry;
            unsigned int bw, d;
            XGetGeometry(dpy, win, &junk, &win_start_x, &win_start_y, &d, &d, &bw, &d);
        }
    }
}

void handle_motion(XEvent* ev) {
    if (dragging && windows.count(drag_win)) {
        int dx = ev->xmotion.x_root - drag_start_x;
        int dy = ev->xmotion.y_root - drag_start_y;
        int nx = win_start_x + dx;
        int ny = win_start_y + dy;
        XMoveWindow(dpy, drag_win, nx, ny);
    }
}

void handle_button_release(XEvent* ev) {
    if (ev->xbutton.button == Button1 && dragging) {
        dragging = false;
    }
}

void spawn_menu() {
    if (fork() == 0) {
        execlp("python3", "python3", "desk.py", nullptr);
        _exit(1);
    }
}

int main() {
    dpy = XOpenDisplay(nullptr);
    if (!dpy) return 1;

    root = DefaultRootWindow(dpy);
    XSelectInput(dpy, root, SubstructureRedirectMask | SubstructureNotifyMask);
    XFlush(dpy);

    spawn_menu();

    XEvent ev;
    while (true) {
        XNextEvent(dpy, &ev);

        switch (ev.type) {
            case MapRequest:
                handle_map_request(&ev);
                break;
            case ButtonPress:
                handle_button_press(&ev);
                break;
            case MotionNotify:
                handle_motion(&ev);
                break;
            case ButtonRelease:
                handle_button_release(&ev);
                break;
        }
    }

    return 0;
}
