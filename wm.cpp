#include <X11/Xlib.h>
#include <cstdio>
#include <cstdlib>
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
    int x = 100, y = 100;

    // Репарентим в root и мапим
    XReparentWindow(dpy, win, root, x, y);
    XMapWindow(dpy, win);

    // Подписываемся на StructureNotifyMask, чтобы ловить ConfigureNotify
    XSelectInput(dpy, win, StructureNotifyMask);

    windows[win] = {win, x, y, 0, 0};

    printf("Window %lu reparented and mapped\n", win);
}

void handle_map_request(XEvent* ev) {
    Window win = ev->xmaprequest.window;
    if (windows.count(win) == 0) {
        create_window(win);
    }
}

void handle_configure_notify(XEvent* ev) {
    Window win = ev->xconfigure.window;
    if (windows.count(win)) {
        ClientWindow& cw = windows[win];
        cw.x = ev->xconfigure.x;
        cw.y = ev->xconfigure.y;
        cw.width = ev->xconfigure.width;
        cw.height = ev->xconfigure.height;
        printf("ConfigureNotify: win %lu pos %d,%d size %dx%d\n", win, cw.x, cw.y, cw.width, cw.height);
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
    if (!dpy) {
        fprintf(stderr, "Cannot open display\n");
        return 1;
    }

    XSetErrorHandler(x_error_handler);

    root = DefaultRootWindow(dpy);

    // Перехватываем попытки создать окна
    if (XSelectInput(dpy, root, SubstructureRedirectMask | SubstructureNotifyMask) == 0) {
        fprintf(stderr, "Successfully selected SubstructureRedirectMask on root window\n");
    } else {
        fprintf(stderr, "Failed to select SubstructureRedirectMask. Is another WM running?\n");
        return 1;
    }

    XFlush(dpy);

    spawn_menu();

    XEvent ev;
    while (true) {
        XNextEvent(dpy, &ev);

        switch (ev.type) {
            case MapRequest:
                handle_map_request(&ev);
                break;
            case ConfigureNotify:
                handle_configure_notify(&ev);
                break;
            default:
                break;
        }
    }

    return 0;
}
