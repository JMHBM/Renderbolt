"""Rounded studio chrome for the Renderbolt desktop app."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

BG = "#0a0a0b"
FG = "#f4f0ea"
MUTED = "#8a8680"
CARD = "#121214"
CARD_2 = "#17171a"
BORDER = "#2a2a32"
BORDER_HOT = "#5a6570"
ICE = "#c5d0d8"
INPUT = "#0e0e10"
ACCENT_FG = "#0a0a0b"


def _font(size: int, weight: str = "normal") -> tuple:
    family = "DejaVu Sans"
    if weight == "bold":
        return (family, size, "bold")
    return (family, size)


class RoundedCard(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        radius: int = 16,
        fill: str = CARD,
        outline: str = BORDER,
        pad: int = 16,
        **kw,
    ) -> None:
        super().__init__(master, bg=BG, **kw)
        self._fill = fill
        self._outline = outline
        self._radius = radius
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=fill)
        self.body.pack(fill="both", expand=True, padx=pad, pady=pad)
        self.bind("<Configure>", self._paint)

    def _paint(self, _evt=None) -> None:
        w, h = max(self.winfo_width(), 8), max(self.winfo_height(), 8)
        self.canvas.delete("r")
        self.canvas.create_round_rect = None
        r = min(self._radius, w // 2, h // 2)
        self._round(self.canvas, 1, 1, w - 2, h - 2, r, self._fill, self._outline)

    @staticmethod
    def _round(c: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int, fill: str, outline: str) -> None:
        c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline=fill, tags="r")
        c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline=fill, tags="r")
        c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline=fill, tags="r")
        c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline=fill, tags="r")
        c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill, tags="r")
        c.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill, tags="r")
        # hairline border
        c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="arc", outline=outline, tags="r")
        c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="arc", outline=outline, tags="r")
        c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="arc", outline=outline, tags="r")
        c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="arc", outline=outline, tags="r")
        c.create_line(x1 + r, y1, x2 - r, y1, fill=outline, tags="r")
        c.create_line(x1 + r, y2, x2 - r, y2, fill=outline, tags="r")
        c.create_line(x1, y1 + r, x1, y2 - r, fill=outline, tags="r")
        c.create_line(x2, y1 + r, x2, y2 - r, fill=outline, tags="r")


def section_label(parent: tk.Misc, text: str, bg: str = CARD) -> tk.Label:
    return tk.Label(
        parent,
        text=text.upper(),
        bg=bg,
        fg=MUTED,
        font=_font(8, "bold"),
        anchor="w",
    )


def field(parent: tk.Misc, label: str, var: tk.StringVar, bg: str = CARD) -> tk.Entry:
    tk.Label(parent, text=label, bg=bg, fg=MUTED, font=_font(9), anchor="w").pack(fill="x", pady=(10, 4))
    e = tk.Entry(
        parent,
        textvariable=var,
        bg=INPUT,
        fg=FG,
        insertbackground=FG,
        relief="flat",
        font=_font(11),
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ICE,
        bd=0,
    )
    e.pack(fill="x", ipady=8, ipadx=8)
    return e


class FileCard(tk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        kicker: str,
        hint: str,
        var: tk.StringVar,
        command: Callable[[], None],
        bg: str = CARD,
    ) -> None:
        super().__init__(parent, bg=bg)
        self.configure(highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER_HOT)
        inner = tk.Frame(self, bg=CARD_2, cursor="hand2")
        inner.pack(fill="x", padx=0, pady=0)
        for w in (self, inner):
            w.bind("<Button-1>", lambda _e: command())
        col = tk.Frame(inner, bg=CARD_2)
        col.pack(fill="x", padx=12, pady=10)
        tk.Label(col, text=kicker, bg=CARD_2, fg=MUTED, font=_font(8, "bold"), anchor="w").pack(fill="x")
        name = tk.Label(col, textvariable=var, bg=CARD_2, fg=FG, font=_font(10, "bold"), anchor="w")
        name.pack(fill="x")
        tk.Label(col, text=hint, bg=CARD_2, fg=MUTED, font=_font(8), anchor="w").pack(fill="x")
        for child in col.winfo_children():
            child.bind("<Button-1>", lambda _e: command())
            child.configure(cursor="hand2")


class StyleCard(tk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        key: str,
        title: str,
        blurb: str,
        var: tk.StringVar,
        bg: str = CARD,
    ) -> None:
        super().__init__(parent, bg=bg)
        self.key = key
        self.var = var
        self.title = title
        self.blurb = blurb
        self._bg = bg
        self.configure(highlightthickness=1, highlightbackground=BORDER, cursor="hand2")
        self.t = tk.Label(self, text=title, bg=bg, fg=FG, font=_font(10, "bold"), anchor="w")
        self.t.pack(fill="x", padx=10, pady=(10, 0))
        self.b = tk.Label(self, text=blurb, bg=bg, fg=MUTED, font=_font(8), anchor="w", wraplength=130, justify="left")
        self.b.pack(fill="x", padx=10, pady=(2, 10))
        self.bind("<Button-1>", self._pick)
        self.t.bind("<Button-1>", self._pick)
        self.b.bind("<Button-1>", self._pick)
        var.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    def _pick(self, _e=None) -> None:
        self.var.set(self.key)

    def refresh(self) -> None:
        on = self.var.get() == self.key
        outline = ICE if on else BORDER
        fill = "#1b1d20" if on else self._bg
        self.configure(highlightbackground=outline, bg=fill)
        self.t.configure(bg=fill)
        self.b.configure(bg=fill)


class ThemeChip(tk.Frame):
    def __init__(self, parent: tk.Misc, name: str, colors: tuple[str, str, str], var: tk.StringVar, bg: str = CARD) -> None:
        super().__init__(parent, bg=bg, cursor="hand2")
        self.name = name
        self.var = var
        self.configure(highlightthickness=1, highlightbackground=BORDER)
        swatch = tk.Canvas(self, width=12, height=12, bg=bg, highlightthickness=0)
        swatch.create_oval(1, 1, 11, 11, fill=colors[0], outline=colors[1])
        swatch.pack(side="left", padx=(8, 4), pady=6)
        self.lbl = tk.Label(self, text=name, bg=bg, fg=FG, font=_font(8))
        self.lbl.pack(side="left", padx=(0, 8))
        for w in (self, swatch, self.lbl):
            w.bind("<Button-1>", lambda _e: var.set(name))
        var.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        on = self.var.get() == self.name
        self.configure(highlightbackground=ICE if on else BORDER)


class Segmented(tk.Frame):
    def __init__(self, parent: tk.Misc, options: list[str], var: tk.StringVar, bg: str = CARD) -> None:
        super().__init__(parent, bg="#1a1a1e")
        self.var = var
        self.buttons: dict[str, tk.Label] = {}
        for opt in options:
            lab = tk.Label(
                self,
                text=opt,
                bg="#1a1a1e",
                fg=MUTED,
                font=_font(9, "bold"),
                padx=10,
                pady=7,
                cursor="hand2",
            )
            lab.pack(side="left", fill="x", expand=True, padx=2, pady=2)
            lab.bind("<Button-1>", lambda _e, o=opt: var.set(o))
            self.buttons[opt] = lab
        var.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        for opt, lab in self.buttons.items():
            on = self.var.get() == opt
            lab.configure(bg="#2a2c32" if on else "#1a1a1e", fg=FG if on else MUTED)


class Toggle(tk.Frame):
    def __init__(self, parent: tk.Misc, text: str, var: tk.BooleanVar, bg: str = CARD) -> None:
        super().__init__(parent, bg=bg)
        tk.Label(self, text=text, bg=bg, fg=FG, font=_font(10), anchor="w").pack(side="left")
        self.var = var
        self.knob = tk.Canvas(self, width=40, height=24, bg=bg, highlightthickness=0, cursor="hand2")
        self.knob.pack(side="right")
        self.knob.bind("<Button-1>", lambda _e: var.set(not var.get()))
        var.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        on = bool(self.var.get())
        c = self.knob
        c.delete("all")
        fill = ICE if on else "#3a3a40"
        c.create_oval(2, 2, 22, 22, fill=fill, outline=fill)
        c.create_oval(18, 2, 38, 22, fill=fill, outline=fill)
        c.create_rectangle(12, 2, 28, 22, fill=fill, outline=fill)
        x = 26 if on else 4
        c.create_oval(x, 4, x + 16, 20, fill=FG, outline=FG)


class Scrollable(tk.Frame):
    """Vertical scrolling body. Put widgets in `.body`."""

    def __init__(self, master: tk.Misc, bg: str = CARD) -> None:
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", lambda _e: self._bind_wheel(True))
        self.canvas.bind("<Leave>", lambda _e: self._bind_wheel(False))
        self.body.bind("<Enter>", lambda _e: self._bind_wheel(True))
        self.body.bind("<Leave>", lambda _e: self._bind_wheel(False))
        self._wheel_bound = False

    def _on_body(self, _e=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 0, 0))

    def _on_canvas(self, e) -> None:
        self.canvas.itemconfigure(self._win, width=e.width)

    def _bind_wheel(self, on: bool) -> None:
        if on and not self._wheel_bound:
            self.canvas.bind_all("<MouseWheel>", self._wheel)
            self.canvas.bind_all("<Button-4>", self._wheel)
            self.canvas.bind_all("<Button-5>", self._wheel)
            self._wheel_bound = True
        elif not on and self._wheel_bound:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
            self._wheel_bound = False

    def _wheel(self, e) -> None:
        if getattr(e, "num", None) == 5 or getattr(e, "delta", 0) < 0:
            self.canvas.yview_scroll(3, "units")
        else:
            self.canvas.yview_scroll(-3, "units")
        return "break"


def labeled_scale(
    parent: tk.Misc,
    title: str,
    var: tk.DoubleVar,
    lo: float,
    hi: float,
    res: float = 1.0,
    fmt: str = "{:.0f}",
    bg: str = CARD,
) -> tk.Scale:
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", pady=(8, 0))
    tk.Label(row, text=title, bg=bg, fg=MUTED, font=_font(8, "bold"), anchor="w").pack(side="left")
    readout = tk.Label(row, text=fmt.format(var.get()), bg=bg, fg=FG, font=_font(8), anchor="e")
    readout.pack(side="right")
    scale = tk.Scale(
        parent,
        from_=lo,
        to=hi,
        resolution=res,
        orient="horizontal",
        variable=var,
        bg=bg,
        fg=FG,
        troughcolor=INPUT,
        highlightthickness=0,
        showvalue=0,
        sliderrelief="flat",
        activebackground=ICE,
        bd=0,
    )
    scale.pack(fill="x")

    def _upd(*_):
        try:
            readout.configure(text=fmt.format(var.get()))
        except Exception:
            pass

    var.trace_add("write", _upd)
    return scale


PALETTE = [
    "#8a1848", "#c41c4c", "#ff4d6d", "#ff9ec0", "#ffd0dc",
    "#8a2208", "#c43c08", "#ff6a1a", "#ffb070", "#ffe0b0",
    "#8a5a00", "#c49000", "#ffc400", "#ffe08a", "#fff4c8",
    "#0d5c38", "#148c54", "#22c47a", "#9ef0c0", "#d4ffe8",
    "#046060", "#089090", "#12d0c8", "#7dfff0", "#c8fff8",
    "#023e6b", "#156a96", "#1e90d0", "#5ad0ff", "#b8ecff",
    "#1e2a8a", "#3c4cc8", "#6a78ff", "#b8c4ff", "#e0e6ff",
    "#4a148c", "#7a28c4", "#a855f0", "#e0b0ff", "#f0dcff",
    "#2a2a2c", "#5a5a60", "#8a8680", "#c8c4bc", "#f0ece4",
]


class ColorStudio(tk.Frame):
    """Base + tip wells and a square palette."""

    def __init__(
        self,
        parent: tk.Misc,
        base_var: tk.StringVar,
        tip_var: tk.StringVar,
        bg: str = CARD,
        on_pick: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, bg=bg)
        self.base_var = base_var
        self.tip_var = tip_var
        self._target = "base"
        self._on_pick = on_pick
        wells = tk.Frame(self, bg=bg)
        wells.pack(fill="x", pady=(0, 8))
        self.base_well = self._well(wells, "Base", base_var, "base")
        self.tip_well = self._well(wells, "Tips", tip_var, "tip")
        pal = tk.Frame(self, bg=bg)
        pal.pack()
        cell = 18
        for i, hexcol in enumerate(PALETTE):
            r, c = divmod(i, 5)
            sw = tk.Canvas(pal, width=cell, height=cell, bg=bg, highlightthickness=1, highlightbackground=BORDER, cursor="hand2")
            sw.grid(row=r, column=c, padx=1, pady=1)
            sw.create_rectangle(0, 0, cell, cell, fill=hexcol, outline=hexcol)
            sw.bind("<Button-1>", lambda _e, h=hexcol: self._set(h))
        btns = tk.Frame(self, bg=bg)
        btns.pack(fill="x", pady=(8, 0))
        tk.Label(btns, text="Custom…", bg="#1a1a1e", fg=FG, font=_font(8), padx=8, pady=5, cursor="hand2").pack(side="left")
        btns.winfo_children()[0].bind("<Button-1>", lambda _e: self._custom())
        tk.Label(btns, text="Swap", bg="#1a1a1e", fg=FG, font=_font(8), padx=8, pady=5, cursor="hand2").pack(side="left", padx=6)
        btns.winfo_children()[1].bind("<Button-1>", lambda _e: self._swap())
        tk.Label(btns, text="Random", bg="#1a1a1e", fg=FG, font=_font(8), padx=8, pady=5, cursor="hand2").pack(side="left")
        btns.winfo_children()[2].bind("<Button-1>", lambda _e: self._random())
        base_var.trace_add("write", lambda *_: self._refresh_wells())
        tip_var.trace_add("write", lambda *_: self._refresh_wells())
        self._refresh_wells()

    def _well(self, parent: tk.Misc, label: str, var: tk.StringVar, key: str) -> tk.Canvas:
        box = tk.Frame(parent, bg=parent["bg"])
        box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(box, text=label.upper(), bg=parent["bg"], fg=MUTED, font=_font(7, "bold")).pack(anchor="w")
        c = tk.Canvas(box, width=108, height=28, highlightthickness=1, highlightbackground=ICE if key == "base" else BORDER, cursor="hand2")
        c.pack(fill="x")
        c.bind("<Button-1>", lambda _e, k=key: self._select(k))
        return c

    def _select(self, key: str) -> None:
        self._target = key
        self.base_well.configure(highlightbackground=ICE if key == "base" else BORDER)
        self.tip_well.configure(highlightbackground=ICE if key == "tip" else BORDER)

    def _set(self, hexcol: str) -> None:
        (self.base_var if self._target == "base" else self.tip_var).set(hexcol)
        if self._on_pick:
            self._on_pick()

    def _custom(self) -> None:
        from tkinter import colorchooser
        current = self.base_var.get() if self._target == "base" else self.tip_var.get()
        rgb, hx = colorchooser.askcolor(color=current, title="Visualizer color")
        if hx:
            self._set(hx)

    def _swap(self) -> None:
        a, b = self.base_var.get(), self.tip_var.get()
        self.base_var.set(b)
        self.tip_var.set(a)

    def _random(self) -> None:
        import random
        self.base_var.set(random.choice(PALETTE))
        self.tip_var.set(random.choice(PALETTE))

    def _refresh_wells(self) -> None:
        for canvas, var in ((self.base_well, self.base_var), (self.tip_well, self.tip_var)):
            canvas.delete("all")
            try:
                canvas.create_rectangle(0, 0, 200, 40, fill=var.get(), outline=var.get())
            except tk.TclError:
                canvas.create_rectangle(0, 0, 200, 40, fill="#888888", outline="#888888")

