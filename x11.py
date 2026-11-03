"""Acesso mínimo à libX11 via ctypes: listar janelas e ler suas propriedades."""
import ctypes
import ctypes.util
import time

_xlib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11") or "libX11.so.6")

Window = ctypes.c_ulong
Atom = ctypes.c_ulong
IsViewable = 2
RevertToParent = 2
CurrentTime = 0
# Botões 1, 2 e 3 do mouse pressionados (Button1Mask | Button2Mask | Button3Mask).
BOTOES_MASK = (1 << 8) | (1 << 9) | (1 << 10)
AnyPropertyType = 0
XA_CARDINAL = 6
PropModeReplace = 0


class XClassHint(ctypes.Structure):
    _fields_ = [("res_name", ctypes.c_void_p), ("res_class", ctypes.c_void_p)]


class XWindowAttributes(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int),
        ("width", ctypes.c_int), ("height", ctypes.c_int),
        ("border_width", ctypes.c_int), ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p), ("root", Window),
        ("class_", ctypes.c_int), ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong), ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int), ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int), ("map_state", ctypes.c_int),
        ("all_event_masks", ctypes.c_long), ("your_event_mask", ctypes.c_long),
        ("do_not_propagate_mask", ctypes.c_long), ("override_redirect", ctypes.c_int),
        ("screen", ctypes.c_void_p),
    ]


_xlib.XOpenDisplay.restype = ctypes.c_void_p
_xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
_xlib.XDefaultRootWindow.restype = Window
_xlib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
_xlib.XQueryTree.argtypes = [
    ctypes.c_void_p, Window, ctypes.POINTER(Window), ctypes.POINTER(Window),
    ctypes.POINTER(ctypes.POINTER(Window)), ctypes.POINTER(ctypes.c_uint),
]
_xlib.XGetClassHint.argtypes = [ctypes.c_void_p, Window, ctypes.POINTER(XClassHint)]
_xlib.XGetWindowAttributes.argtypes = [ctypes.c_void_p, Window, ctypes.POINTER(XWindowAttributes)]
_xlib.XInternAtom.restype = Atom
_xlib.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_xlib.XGetWindowProperty.argtypes = [
    ctypes.c_void_p, Window, Atom, ctypes.c_long, ctypes.c_long, ctypes.c_int, Atom,
    ctypes.POINTER(Atom), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_ulong),
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_void_p),
]
_xlib.XFree.argtypes = [ctypes.c_void_p]
_xlib.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(Window), ctypes.POINTER(ctypes.c_int)]
_xlib.XSetInputFocus.argtypes = [ctypes.c_void_p, Window, ctypes.c_int, ctypes.c_ulong]
_xlib.XQueryPointer.argtypes = [
    ctypes.c_void_p, Window, ctypes.POINTER(Window), ctypes.POINTER(Window),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),
]
_xlib.XFlush.argtypes = [ctypes.c_void_p]
_xlib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
_xlib.XDefaultScreen.argtypes = [ctypes.c_void_p]
_xlib.XWithdrawWindow.argtypes = [ctypes.c_void_p, Window, ctypes.c_int]
_xlib.XChangeProperty.argtypes = [ctypes.c_void_p, Window, Atom, Atom, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_void_p, ctypes.c_int]
_xlib.XDeleteProperty.argtypes = [ctypes.c_void_p, Window, Atom]

# Ignora erros X (ex.: janela fechada no meio da varredura) em vez de abortar o processo.
_ERRHANDLER = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(lambda d, e: 0)
_xlib.XSetErrorHandler(_ERRHANDLER)


class X11:
    def __init__(self):
        self.dpy = _xlib.XOpenDisplay(None)
        if not self.dpy:
            raise RuntimeError("Não foi possível abrir o display X11 (XWayland).")
        self.root = _xlib.XDefaultRootWindow(self.dpy)
        self._net_wm_name = _xlib.XInternAtom(self.dpy, b"_NET_WM_NAME", False)
        self._utf8 = _xlib.XInternAtom(self.dpy, b"UTF8_STRING", False)
        self._wm_name = _xlib.XInternAtom(self.dpy, b"WM_NAME", False)
        self._net_wm_pid = _xlib.XInternAtom(self.dpy, b"_NET_WM_PID", False)

    def _children(self, win):
        root, parent = Window(), Window()
        kids = ctypes.POINTER(Window)()
        n = ctypes.c_uint()
        if not _xlib.XQueryTree(self.dpy, win, ctypes.byref(root), ctypes.byref(parent),
                                ctypes.byref(kids), ctypes.byref(n)):
            return []
        out = [kids[i] for i in range(n.value)]
        if kids:
            _xlib.XFree(kids)
        return out

    def wm_class(self, win):
        hint = XClassHint()
        if not _xlib.XGetClassHint(self.dpy, win, ctypes.byref(hint)):
            return None
        cls = ctypes.string_at(hint.res_class).decode(errors="replace") if hint.res_class else ""
        # res_name/res_class são alocados pelo Xlib; liberar evita vazamento.
        if hint.res_name:
            _xlib.XFree(hint.res_name)
        if hint.res_class:
            _xlib.XFree(hint.res_class)
        return cls

    def _prop(self, win, atom, typ):
        """Lê uma propriedade X11; devolve (ponteiro, nº de itens) ou (None, 0)."""
        rtype, fmt = Atom(), ctypes.c_int()
        nitems, after = ctypes.c_ulong(), ctypes.c_ulong()
        data = ctypes.c_void_p()
        ok = _xlib.XGetWindowProperty(self.dpy, win, atom, 0, 1024, False, typ,
                                      ctypes.byref(rtype), ctypes.byref(fmt), ctypes.byref(nitems),
                                      ctypes.byref(after), ctypes.byref(data))
        if ok != 0 or not data.value:
            return None, 0
        return data, nitems.value

    def _prop_str(self, win, atom, typ):
        data, n = self._prop(win, atom, typ)
        if data is None:
            return None
        text = ctypes.string_at(data.value, n).decode(errors="replace")
        _xlib.XFree(data)
        return text

    def pid(self, win):
        """PID do processo dono da janela (_NET_WM_PID), ou None."""
        data, n = self._prop(win, self._net_wm_pid, XA_CARDINAL)
        if data is None:
            return None
        # Propriedades de formato 32 chegam como 'long' do C (8 bytes em 64 bits).
        value = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[0] if n else None
        _xlib.XFree(data)
        return value

    def title(self, win):
        return (self._prop_str(win, self._net_wm_name, self._utf8)
                or self._prop_str(win, self._wm_name, AnyPropertyType) or "")

    def geometry(self, win):
        attr = XWindowAttributes()
        if not _xlib.XGetWindowAttributes(self.dpy, win, ctypes.byref(attr)):
            return None
        return attr

    def find_windows(self, wm_class, max_depth=3):
        """Janelas visíveis cujo WM_CLASS é wm_class, sem diferenciar maiúsculas (busca na
        árvore inteira, pois o KWin pode colocar as janelas dentro de molduras)."""
        found = []

        def walk(win, depth):
            for child in self._children(win):
                cls = self.wm_class(child)
                if cls and cls.lower() == wm_class.lower():
                    attr = self.geometry(child)
                    if attr and attr.map_state == IsViewable:
                        found.append(child)
                    continue
                if depth < max_depth:
                    walk(child, depth + 1)

        walk(self.root, 0)
        return found

    # ---- teclado -----------------------------------------------------------

    def withdraw(self, win):
        """Tira a janela do controle do gerenciador de janelas (ICCCM: desmapeia e avisa a raiz).

        Sem isso, gerenciadores novos (Mutter 50) readotam a janela assim que ela é encaixada
        em outro pai e a tiram do socket logo em seguida (o AnyDesk abre e fecha na hora).
        """
        _xlib.XWithdrawWindow(self.dpy, win, _xlib.XDefaultScreen(self.dpy))
        _xlib.XSync(self.dpy, False)
        # O gerenciador demora uns 30 ms para largar a moldura; encaixar antes disso falha.
        limite = time.monotonic() + 0.5
        while not self.is_toplevel_free(win) and time.monotonic() < limite:
            time.sleep(0.005)

    def is_toplevel_free(self, win):
        """True se a janela está direto na raiz (o gerenciador de janelas já largou a moldura)."""
        root, parent = Window(), Window()
        kids = ctypes.POINTER(Window)()
        n = ctypes.c_uint()
        if not _xlib.XQueryTree(self.dpy, win, ctypes.byref(root), ctypes.byref(parent),
                                ctypes.byref(kids), ctypes.byref(n)):
            return False
        if kids:
            _xlib.XFree(kids)
        return parent.value == self.root

    def focused(self):
        """Janela que recebe o teclado agora."""
        win, revert = Window(), ctypes.c_int()
        _xlib.XGetInputFocus(self.dpy, ctypes.byref(win), ctypes.byref(revert))
        return win.value

    def set_focus(self, win):
        _xlib.XSetInputFocus(self.dpy, win, RevertToParent, CurrentTime)
        _xlib.XFlush(self.dpy)

    def contains(self, ancestor, win):
        """True se win é ancestor ou está dentro dele."""
        while win and win != self.root:
            if win == ancestor:
                return True
            root, parent = Window(), Window()
            kids = ctypes.POINTER(Window)()
            n = ctypes.c_uint()
            if not _xlib.XQueryTree(self.dpy, win, ctypes.byref(root), ctypes.byref(parent),
                                    ctypes.byref(kids), ctypes.byref(n)):
                return False
            if kids:
                _xlib.XFree(kids)
            win = parent.value
        return False

    def clicked_inside(self, win):
        """True se o mouse está sobre win com algum botão pressionado."""
        root, child = Window(), Window()
        rx, ry, wx, wy = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
        mask = ctypes.c_uint()
        if not _xlib.XQueryPointer(self.dpy, win, ctypes.byref(root), ctypes.byref(child),
                                   ctypes.byref(rx), ctypes.byref(ry), ctypes.byref(wx),
                                   ctypes.byref(wy), ctypes.byref(mask)):
            return False
        attr = self.geometry(win)
        dentro = attr and 0 <= wx.value < attr.width and 0 <= wy.value < attr.height
        return bool(dentro and mask.value & BOTOES_MASK)

    # ---- efeito vidro ------------------------------------------------------

    def set_blur(self, win, rects):
        """Pede ao KWin para desfocar o que está atrás dos retângulos (x, y, w, h) da janela.
        rects=None desliga o desfoque."""
        atom = _xlib.XInternAtom(self.dpy, b"_KDE_NET_WM_BLUR_BEHIND_REGION", False)
        if rects is None:
            _xlib.XDeleteProperty(self.dpy, win, atom)
        else:
            valores = [v for r in rects for v in r]
            # Propriedades de formato 32 são passadas como 'long' do C.
            dados = (ctypes.c_ulong * len(valores))(*valores)
            _xlib.XChangeProperty(self.dpy, win, atom, XA_CARDINAL, 32, PropModeReplace,
                                  dados, len(valores))
        _xlib.XFlush(self.dpy)
