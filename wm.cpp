#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <unistd.h>
#include <cstdlib>
#include <cstdio>
#include <map>

struct ClientWindow {
    Window win;
    int x, y, width, height;
};

Display* dpy;
Window root;
std::map<Window, ClientWindow> windows;

int x_error_handler(Display* dpy, XErrorEvent* err) {
    char err_msg[1024];
    XGetErrorText(dpy, err->error_code, err_msg, sizeof(err_msg));
    fprintf(stderr, "X Error: %s\n", err_msg);
    return 0;
}

void create_window(Window win) {
    XWindowAttributes attr;
    XGetWindowAttributes(dpy, win, &attr);

    int x = 100, y = 100;
    int width = attr.width;
    int height = attr.height;

    // Репарентим окно в root и задаём позицию и размер
    XReparentWindow(dpy, win, root, x, y);

    XWindowChanges changes;
    changes.x = x;
    changes.y = y;
    changes.width = width;
    changes.height = height;
    XConfigureWindow(dpy, win, CWX | CWY | CWWidth | CWHeight, &changes);

    XMapWindow(dpy, win);

    ClientWindow cw = {win, x, y, width, height};
    windows[win] = cw;

    // Подписываемся на события для окна
    XSelectInput(dpy, win, FocusChangeMask | ButtonPressMask | ButtonReleaseMask);
    
    printf("Created window %lu at %d,%d size %dx%d\n", win, x, y, width, height);
}

void handle_map_request(XEvent* ev) {
    Window win = ev->xmaprequest.window;
    if (windows.count(win) == 0) {
        create_window(win);
    }
}

void handle_button_press(XEvent* ev) {
    // Перетаскивание отключено
}

void handle_motion(XEvent* ev) {
    // Нет перетаскивания
}

void handle_button_release(XEvent* ev) {
    // Нет перетаскивания
}

void spawn_menu() {
    if (fork() == 0) {
        execlp("python3", "python3", "desk.py", nullptr);
        _exit(1);
    }
}

int main() {
    dpy = XOpenDisplay(nullptr);
    if (!dpy) {
        fprintf(stderr, "Cannot open display\n");
        return 1;
    }

    XSetErrorHandler(x_error_handler);

    root = DefaultRootWindow(dpy);

    // Пытаемся перехватить управление окнами
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
            default:
                break;
        }
    }

    return 0;
}