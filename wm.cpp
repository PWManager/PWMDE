#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <unistd.h>
#include <cstdlib>
#include <cstring>
#include <map>
#include <cstdio>

struct ClientWindow {
    Window win;
    int x, y, width, height;
};

Display* dpy;
Window root;
std::map<Window, ClientWindow> windows;

void create_window(Window win) {
    XWindowAttributes attr;
    XGetWindowAttributes(dpy, win, &attr);

    int x = 100, y = 100;

    XReparentWindow(dpy, win, root, x, y);
    XMoveWindow(dpy, win, x, y);
    XMapWindow(dpy, win);

    ClientWindow cw = { win, x, y, attr.width, attr.height };
    windows[win] = cw;

    // Подписываемся только на фокус и кнопки без motion events
    XSelectInput(dpy, win, FocusChangeMask | ButtonPressMask | ButtonReleaseMask);
}

void handle_map_request(XEvent* ev) {
    Window win = ev->xmaprequest.window;
    if (windows.count(win) == 0) {
        create_window(win);
    }
}

void handle_button_press(XEvent* ev) {
    // Тут ничего не делаем — отключаем drag
}

void handle_motion(XEvent* ev) {
    // Никакого перемещения
}

void handle_button_release(XEvent* ev) {
    // Никакого drag, ничего не делаем
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
