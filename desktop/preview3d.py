"""2D and isometric 3D overlay for preview + software fallback."""

from __future__ import annotations

import math
from typing import Any

from PIL import Image, ImageDraw, ImageFilter


def _luma(rgb: tuple[int, int, int]) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _lift(rgb: tuple[int, int, int], floor: float = 56.0) -> tuple[int, int, int]:
    """Keep dark vis colors readable on a dim cover."""
    y = _luma(rgb)
    if y >= floor:
        return rgb
    if y < 1:
        f = int(floor)
        return (f, f, min(255, f + 10))
    s = floor / y
    return (
        min(255, int(rgb[0] * s)),
        min(255, int(rgb[1] * s)),
        min(255, int(rgb[2] * s)),
    )


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return _lift((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))


def _rgba(rgb: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
    return (*rgb, int(max(0, min(255, a * 255))))


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return _lift(
        (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )
    )


def _line(
    draw: ImageDraw.ImageDraw,
    pts: list,
    col: tuple[int, int, int],
    a: float,
    width: int = 3,
) -> None:
    if len(pts) < 2:
        return
    if _luma(col) < 110:
        draw.line(pts, fill=_rgba((228, 232, 238), min(1.0, a * 0.8)), width=max(width + 3, 5))
    draw.line(pts, fill=_rgba(col, a), width=width)


def _place_pt(
    px: float,
    py: float,
    w: int,
    h: int,
    xoff: float,
    yoff: float,
    rot: float,
    sx: float,
    sy: float,
    mirror: bool,
) -> tuple[float, float]:
    cx = w * (0.5 + xoff * 0.45)
    cy = h * (0.58 - yoff * 0.4)
    ox = (px - w * 0.5) * sx * (-1 if mirror else 1)
    oy = (py - h * 0.58) * sy
    rad = math.radians(rot)
    ca, sa = math.cos(rad), math.sin(rad)
    return cx + ox * ca - oy * sa, cy + ox * sa + oy * ca


def project(
    x: float,
    y: float,
    z: float,
    w: int,
    h: int,
    tilt_deg: float,
    place: dict[str, Any],
) -> tuple[float, float]:
    rot = math.radians(float(place.get("rot") or 0))
    sx = float(place.get("sx") or 1)
    sy = float(place.get("sy") or 1)
    if place.get("mirror"):
        x = -x
    ca, sa = math.cos(rot), math.sin(rot)
    x, z = x * ca - z * sa, x * sa + z * ca
    x *= sx
    y *= sy
    tilt = math.radians(tilt_deg)
    yaw = 0.48
    cy, syw = math.cos(yaw), math.sin(yaw)
    x1 = x * cy + z * syw
    z1 = -x * syw + z * cy
    ct, st = math.cos(tilt), math.sin(tilt)
    y2 = y * ct - z1 * st
    z2 = y * st + z1 * ct
    f = 7.2 / (7.2 + z2)
    scale = min(w, h) * 0.092
    px = w * 0.5 + x1 * scale * f
    py = h * 0.62 - y2 * scale * f
    px += float(place.get("x") or 0) * w * 0.45
    py -= float(place.get("y") or 0) * h * 0.4
    return px, py


def _tri(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]], col: tuple[int, int, int, int]) -> None:
    draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=col)


def prism(
    draw: ImageDraw.ImageDraw,
    ox: float,
    hgt: float,
    oz: float,
    bw: float,
    bd: float,
    w: int,
    h: int,
    tilt: float,
    place: dict[str, Any],
    top: tuple[int, int, int, int],
    side: tuple[int, int, int, int],
    face: tuple[int, int, int, int],
) -> None:
    def p(x: float, y: float, z: float) -> tuple[float, float]:
        return project(x, y, z, w, h, tilt, place)

    a = p(ox, 0, oz)
    b = p(ox + bw, 0, oz)
    c = p(ox + bw, 0, oz + bd)
    e = p(ox, hgt, oz)
    f = p(ox + bw, hgt, oz)
    g = p(ox + bw, hgt, oz + bd)
    hh = p(ox, hgt, oz + bd)
    _tri(draw, [b, c, g], side)
    _tri(draw, [b, g, f], side)
    _tri(draw, [a, b, f], face)
    _tri(draw, [a, f, e], face)
    _tri(draw, [e, f, g], top)
    _tri(draw, [e, g, hh], top)


def draw_visualizer(
    img: Image.Image,
    analysis: dict,
    style: str,
    theme: tuple[str, str, str],
    tilt: float,
    vis_alpha: float,
    t: float,
    mode: str = "3D",
    place: dict[str, Any] | None = None,
    glow: float = 0.35,
) -> None:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    base = _hex(theme[0])
    tip = _hex(theme[1] if len(theme) > 1 else theme[0])
    a = max(0.2, min(1.0, vis_alpha))
    bands = analysis["bands"]
    td = analysis["time"]
    pulse = float(analysis.get("pulse") or 0)
    place = place or {"x": 0, "y": 0, "rot": 0, "sx": 1, "sy": 1, "mirror": False}

    if mode == "2D":
        _draw_2d(draw, w, h, analysis, style, base, tip, a, t, pulse, place)
    elif style == "EQ bars":
        n = 36
        for i in range(n - 1, -1, -1):
            tt = i / (n - 1)
            src = float(bands[int(tt * (len(bands) - 1))])
            col_t = _mix(base, tip, src)
            col_b = _mix(base, tip, src * 0.35)
            prism(
                draw, -5.1 + tt * 10.2, 0.18 + src * 3.6, -0.35, 0.2, 0.7, w, h, tilt, place,
                _rgba(col_t, 0.96 * a), _rgba(col_b, 0.7 * a), _rgba(_mix(col_b, col_t, 0.5), 0.85 * a),
            )
    elif style == "Circular":
        n = 48
        radius = 2.4 + pulse * 0.12
        for i in range(n):
            tt = i / n
            ang = tt * math.tau - math.pi / 2
            v = float(bands[int(tt * len(bands)) % len(bands)])
            col_t = _mix(base, tip, v)
            col_b = _mix(base, tip, v * 0.3)
            prism(
                draw,
                math.cos(ang) * radius - 0.08, 0.25 + v * 2.8, math.sin(ang) * radius - 0.08,
                0.16, 0.16, w, h, tilt, place,
                _rgba(col_t, 0.95 * a), _rgba(col_b, 0.65 * a), _rgba(col_t, 0.8 * a),
            )
    elif style == "Levels":
        n, rows = 28, 8
        for i in range(n):
            src = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            q = max(0, min(rows, int(round(src * rows))))
            for r in range(q):
                tt = r / max(1, rows - 1)
                col_t = _mix(base, tip, tt)
                prism(
                    draw, -5.0 + i * (10.0 / max(1, n - 1)), 0.12 + r * 0.42, -0.2, 0.22, 0.22, w, h, tilt, place,
                    _rgba(col_t, 0.95 * a), _rgba(_mix(base, col_t, 0.4), 0.7 * a), _rgba(col_t, 0.85 * a),
                )
    elif style == "Particles":
        n = 32
        for i in range(n):
            src = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            col_t = _mix(base, tip, src)
            prism(
                draw, -5.0 + i * (10.0 / max(1, n - 1)), 0.2 + src * 3.2, -0.12, 0.18, 0.18, w, h, tilt, place,
                _rgba(col_t, 0.95 * a), _rgba(_mix(base, col_t, 0.35), 0.7 * a), _rgba(col_t, 0.8 * a),
            )
    elif style == "Spine":
        n = 18
        for i in range(n):
            src = max(0.08, float(bands[int(i / max(1, n - 1) * (len(bands) - 1))]))
            s = 0.2 + src * 0.9
            col_t = _mix(base, tip, src)
            prism(
                draw, -4.6 + i * (9.2 / max(1, n - 1)), 0.35, -s * 0.5, s, s, w, h, tilt, place,
                _rgba(col_t, 0.96 * a), _rgba(_mix(base, col_t, 0.4), 0.72 * a), _rgba(col_t, 0.88 * a),
            )
    elif style == "Radial wave":
        n = 48
        inner = 1.4 + pulse * 0.1
        ring_in, ring_out = [], []
        for i in range(n + 1):
            tt = (i % n) / n
            ang = tt * math.tau - math.pi / 2
            v = float(bands[int(tt * len(bands)) % len(bands)])
            ring_in.append(project(math.cos(ang) * inner, 0.3, math.sin(ang) * inner, w, h, tilt, place))
            ring_out.append(
                project(math.cos(ang) * (inner + v * 1.8), 0.3, math.sin(ang) * (inner + v * 1.8), w, h, tilt, place)
            )
        for i in range(n):
            col = _mix(base, tip, 0.3 + 0.7 * float(bands[int(i / n * len(bands)) % len(bands)]))
            _tri(draw, [ring_in[i], ring_in[i + 1], ring_out[i + 1]], _rgba(col, 0.55 * a))
            _tri(draw, [ring_in[i], ring_out[i + 1], ring_out[i]], _rgba(col, 0.72 * a))
    elif style == "Liquid waves":
        nx, nz = 22, 12

        def height_at(xi: int, zi: int) -> float:
            band = float(bands[int(xi / (nx - 1) * (len(bands) - 1))])
            return (
                math.sin(xi * 0.55 + t + zi * 0.4) * 0.22
                + math.sin(xi * 0.2 + t * 0.6) * 0.12
                + band * 1.15
            )

        for zi in range(nz - 2, -1, -1):
            for xi in range(nx - 1):
                x0 = -5 + (xi / (nx - 1)) * 10
                x1 = -5 + ((xi + 1) / (nx - 1)) * 10
                z0 = -2.2 + (zi / (nz - 1)) * 4.4
                z1 = -2.2 + ((zi + 1) / (nz - 1)) * 4.4
                ht = height_at(xi, zi)
                a0 = project(x0, ht, z0, w, h, tilt, place)
                a1 = project(x1, height_at(xi + 1, zi), z0, w, h, tilt, place)
                a2 = project(x1, height_at(xi + 1, zi + 1), z1, w, h, tilt, place)
                a3 = project(x0, height_at(xi, zi + 1), z1, w, h, tilt, place)
                shade = max(0.0, min(1.0, (ht + 0.2) / 1.8))
                col = _mix(base, tip, shade)
                _tri(draw, [a0, a1, a2], _rgba(col, (0.35 + shade * 0.5) * a))
                _tri(draw, [a0, a2, a3], _rgba(_mix(base, col, 0.6), (0.3 + shade * 0.45) * a))
    else:
        samples = 96
        step = max(1, td.size // samples)
        vals = []
        for i in range(samples):
            chunk = td[i * step : (i + 1) * step]
            vals.append(float(chunk.mean()) if chunk.size else 0.0)
        for i in range(samples - 2, -1, -1):
            t0 = i / (samples - 1)
            t1 = (i + 1) / (samples - 1)
            x0 = -5.2 + t0 * 10.4
            x1 = -5.2 + t1 * 10.4
            y0 = vals[i] * 2.6
            y1 = vals[i + 1] * 2.6
            pa = project(x0, y0, -0.7, w, h, tilt, place)
            pb = project(x1, y1, -0.7, w, h, tilt, place)
            pc = project(x1, y1, 0.7, w, h, tilt, place)
            pd = project(x0, y0, 0.7, w, h, tilt, place)
            tt = 0.5 + 0.5 * vals[i]
            col = _mix(base, tip, tt)
            _tri(draw, [pa, pb, pc], _rgba(_mix(base, col, 0.6), 0.7 * a))
            _tri(draw, [pa, pc, pd], _rgba(col, 0.88 * a))

    if glow > 0.02:
        bloom = overlay.filter(ImageFilter.GaussianBlur(radius=max(2, int(4 + glow * 10))))
        img.alpha_composite(bloom)
    img.alpha_composite(overlay)


def _draw_2d(
    draw: ImageDraw.ImageDraw,
    w: int,
    h: int,
    analysis: dict,
    style: str,
    base: tuple[int, int, int],
    tip: tuple[int, int, int],
    a: float,
    t: float,
    pulse: float,
    place: dict[str, Any],
) -> None:
    bands = analysis["bands"]
    td = analysis["time"]

    def P(px: float, py: float) -> tuple[float, float]:
        return _place_pt(px, py, w, h, float(place.get("x") or 0), float(place.get("y") or 0),
                         float(place.get("rot") or 0), float(place.get("sx") or 1),
                         float(place.get("sy") or 1), bool(place.get("mirror")))

    if style == "EQ bars":
        n = 56
        pad, avail = w * 0.08, w * 0.84
        gap = max(2, avail * 0.006)
        bw = max(2, (avail - gap * (n - 1)) / n)
        base_y = h * 0.93
        max_h = h * 0.28
        for i in range(n):
            v = float(bands[int(i / (n - 1) * (len(bands) - 1))])
            bh = max(4, v * max_h)
            x = pad + i * (bw + gap)
            steps = max(4, int(bh / 4))
            for s in range(steps):
                tt = s / max(1, steps - 1)
                y0 = base_y - bh * (s + 1) / steps
                y1 = base_y - bh * s / steps
                col = _rgba(_mix(base, tip, tt), (0.75 + v * 0.25) * a)
                pts = [P(x, y0), P(x + bw, y0), P(x + bw, y1), P(x, y1)]
                draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=col)
    elif style == "Levels":
        n, rows = 32, 10
        pad, avail = w * 0.08, w * 0.84
        gap = max(2, avail * 0.012)
        bw = max(3, (avail - gap * (n - 1)) / n)
        cell_h = h * 0.028
        cell_gap = h * 0.006
        base_y = h * 0.93
        for i in range(n):
            v = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            q = max(0, min(rows, int(round(v * rows))))
            x = pad + i * (bw + gap)
            for r in range(q):
                y1 = base_y - r * (cell_h + cell_gap)
                y0 = y1 - cell_h
                col = _rgba(_mix(base, tip, r / max(1, rows - 1)), (0.7 + v * 0.3) * a)
                pts = [P(x, y0), P(x + bw, y0), P(x + bw, y1), P(x, y1)]
                draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=col)
    elif style == "Particles":
        n = 36
        pad, avail = w * 0.08, w * 0.84
        size = max(6, w * 0.016)
        for i in range(n):
            v = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            cx = pad + (i + 0.5) * (avail / n)
            cy = h * 0.92 - v * h * 0.62
            col = _rgba(_mix(base, tip, v), (0.75 + v * 0.25) * a)
            pts = [P(cx - size, cy - size), P(cx + size, cy - size), P(cx + size, cy + size), P(cx - size, cy + size)]
            draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=col)
    elif style == "Spine":
        n = 20
        pad, avail = w * 0.08, w * 0.84
        mid = h * 0.55
        for i in range(n):
            v = max(0.08, float(bands[int(i / max(1, n - 1) * (len(bands) - 1))]))
            half = v * min(w, h) * 0.055
            cx = pad + (i + 0.5) * (avail / n)
            col = _rgba(_mix(base, tip, v), (0.7 + v * 0.3) * a)
            pts = [P(cx - half, mid - half), P(cx + half, mid - half), P(cx + half, mid + half), P(cx - half, mid + half)]
            draw.polygon([(int(p[0]), int(p[1])) for p in pts], fill=col)
    elif style == "Radial wave":
        cx, cy = w * 0.5, h * 0.48
        inner = min(w, h) * (0.14 + pulse * 0.02)
        n = 72
        pts_out = []
        pts_in = []
        for i in range(n + 1):
            tt = (i % n) / n
            ang = tt * math.tau - math.pi / 2
            v = float(bands[int(tt * len(bands)) % len(bands)])
            pts_in.append(P(cx + math.cos(ang) * inner, cy + math.sin(ang) * inner))
            pts_out.append(P(cx + math.cos(ang) * (inner + v * min(w, h) * 0.22), cy + math.sin(ang) * (inner + v * min(w, h) * 0.22)))
        for i in range(n):
            col = _rgba(_mix(base, tip, 0.25 + 0.75 * float(bands[int(i / n * len(bands)) % len(bands)])), 0.7 * a)
            draw.polygon(
                [pts_in[i], pts_in[i + 1], pts_out[i + 1], pts_out[i]],
                fill=col,
            )
    elif style == "Circular":
        cx, cy = w * 0.5, h * 0.46
        inner = min(w, h) * (0.16 + pulse * 0.02)
        max_len = min(w, h) * 0.2
        n = 96
        ring = []
        for i in range(n + 1):
            ang = i / n * math.tau - math.pi / 2
            ring.append(P(cx + math.cos(ang) * inner, cy + math.sin(ang) * inner))
        _line(draw, [(int(p[0]), int(p[1])) for p in ring], tip, 0.85 * a, 3)
        for i in range(n):
            v = float(bands[int(i / n * len(bands)) % len(bands)])
            ang = i / n * math.tau - math.pi / 2
            length = inner + max(8, v * max_len)
            p0 = P(cx + math.cos(ang) * inner, cy + math.sin(ang) * inner)
            p1 = P(cx + math.cos(ang) * length, cy + math.sin(ang) * length)
            _line(draw, [p0, p1], _mix(base, tip, v), (0.45 + v * 0.55) * a, 3)
    elif style == "Liquid waves":
        pts_n = 48
        for layer, (amp, yf, aa, use_tip) in enumerate(
            ((0.09 + float(analysis.get("bass") or 0) * 0.08, 0.70, 0.35, False),
             (0.07, 0.76, 0.48, False),
             (0.05, 0.82, 0.7, True))
        ):
            poly = [P(0, h)]
            for i in range(pts_n + 1):
                tt = i / pts_n
                x = tt * w
                band = float(bands[int(tt * (len(bands) - 1))])
                y = (
                    h * yf
                    - math.sin(tt * math.pi * 3 + t * (0.6 + layer * 0.4)) * h * amp
                    - band * h * 0.05
                )
                poly.append(P(x, y))
            poly.append(P(w, h))
            col = tip if use_tip else base
            draw.polygon([(int(p[0]), int(p[1])) for p in poly], fill=_rgba(col, aa * a))
    else:
        mid, amp = h * 0.82, h * (0.12 + float(analysis.get("bass") or 0) * 0.08)
        step = max(1, td.size // 480)
        count = max(2, td.size // step)
        top, bot = [], []
        for i in range(count):
            v = float(td[i * step : (i + 1) * step].mean())
            x = w * 0.07 + (i / (count - 1)) * w * 0.86
            top.append(P(x, mid - v * amp))
            bot.append(P(x, mid + v * amp * 0.92))
        poly = top + list(reversed(bot))
        if len(poly) > 4:
            draw.polygon([(int(p[0]), int(p[1])) for p in poly], fill=_rgba(base, 0.55 * a))
            _line(draw, [(int(p[0]), int(p[1])) for p in top], tip, 0.95 * a, 3)


def draw_lite(
    img: Image.Image,
    analysis: dict,
    style: str,
    theme: tuple[str, str],
    vis_alpha: float,
    place: dict[str, Any] | None = None,
) -> None:
    """Cheap 2D overlay for the studio preview. No 3D, no blur."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    base = _hex(theme[0])
    tip = _hex(theme[1] if len(theme) > 1 else theme[0])
    a = max(0.35, min(1.0, vis_alpha))
    bands = analysis.get("bands")
    if bands is None or len(bands) == 0:
        bands = [0.0]
    td = analysis.get("time")
    pulse = float(analysis.get("pulse") or 0)
    place = place or {}
    xoff = float(place.get("x") or 0)
    yoff = float(place.get("y") or 0)

    def P(px: float, py: float) -> tuple[int, int]:
        return int(px + xoff * w * 0.45), int(py - yoff * h * 0.4)

    if style == "EQ bars":
        n = 28
        pad, avail = w * 0.08, w * 0.84
        gap = max(1, avail * 0.01)
        bw = max(2, (avail - gap * (n - 1)) / n)
        base_y = h * 0.93
        max_h = h * 0.28
        for i in range(n):
            v = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            bh = max(3, v * max_h)
            x = pad + i * (bw + gap)
            col = _rgba(_mix(base, tip, v), a)
            x0, y0 = P(x, base_y - bh)
            x1, y1 = P(x + bw, base_y)
            draw.rectangle([x0, y0, x1, y1], fill=col)
    elif style == "Levels":
        n, rows = 20, 8
        pad, avail = w * 0.08, w * 0.84
        gap = max(1, avail * 0.012)
        bw = max(3, (avail - gap * (n - 1)) / n)
        ch, cg = h * 0.03, h * 0.006
        base_y = h * 0.92
        for i in range(n):
            v = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            q = max(0, min(rows, int(round(v * rows))))
            x = pad + i * (bw + gap)
            for r in range(q):
                y1 = base_y - r * (ch + cg)
                col = _rgba(_mix(base, tip, r / max(1, rows - 1)), a)
                x0, y0 = P(x, y1 - ch)
                x1, y1p = P(x + bw, y1)
                draw.rectangle([x0, y0, x1, y1p], fill=col)
    elif style == "Particles":
        n = 24
        size = max(4, w * 0.018)
        for i in range(n):
            v = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            cx = w * 0.1 + (i + 0.5) * (w * 0.8 / n)
            cy = h * 0.88 - v * h * 0.55
            col = _rgba(_mix(base, tip, v), a)
            x0, y0 = P(cx - size, cy - size)
            x1, y1 = P(cx + size, cy + size)
            draw.rectangle([x0, y0, x1, y1], fill=col)
    elif style == "Spine":
        n = 16
        mid = h * 0.55
        for i in range(n):
            v = max(0.08, float(bands[int(i / max(1, n - 1) * (len(bands) - 1))]))
            half = v * min(w, h) * 0.05
            cx = w * 0.1 + (i + 0.5) * (w * 0.8 / n)
            col = _rgba(_mix(base, tip, v), a)
            x0, y0 = P(cx - half, mid - half)
            x1, y1 = P(cx + half, mid + half)
            draw.rectangle([x0, y0, x1, y1], fill=col)
    elif style == "Radial wave":
        cx, cy = w * 0.5, h * 0.5
        inner = min(w, h) * (0.14 + pulse * 0.02)
        n = 48
        pts_in, pts_out = [], []
        for i in range(n + 1):
            tt = (i % n) / n
            ang = tt * math.tau - math.pi / 2
            v = float(bands[int(tt * len(bands)) % len(bands)])
            pts_in.append(P(cx + math.cos(ang) * inner, cy + math.sin(ang) * inner))
            r = inner + v * min(w, h) * 0.2
            pts_out.append(P(cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        for i in range(n):
            col = _rgba(_mix(base, tip, 0.25 + 0.75 * float(bands[int(i / n * len(bands)) % len(bands)])), 0.7 * a)
            draw.polygon([pts_in[i], pts_in[i + 1], pts_out[i + 1], pts_out[i]], fill=col)
    elif style == "Circular":
        cx, cy = w * 0.5, h * 0.48
        inner = min(w, h) * (0.16 + pulse * 0.02)
        n = 48
        for i in range(n):
            v = float(bands[int(i / n * len(bands)) % len(bands)])
            ang = i / n * math.tau - math.pi / 2
            r0, r1 = inner, inner + v * min(w, h) * 0.2
            p0 = P(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
            p1 = P(cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)
            _line(draw, [p0, p1], _mix(base, tip, v), a, 3)
    elif style == "Liquid waves":
        pts = 40
        poly = [P(0, h), P(0, h * 0.7)]
        for i in range(pts + 1):
            tt = i / pts
            v = float(bands[int(tt * (len(bands) - 1))])
            y = h * 0.62 - math.sin(tt * math.pi * 3) * h * 0.06 - v * h * 0.12
            poly.append(P(tt * w, y))
        poly.append(P(w, h))
        draw.polygon(poly, fill=_rgba(tip, 0.35 * a))
    else:
        mid, amp = h * 0.6, h * 0.16
        n = 64
        pts = []
        if td is not None and getattr(td, "size", 0):
            step = max(1, td.size // n)
            for i in range(n):
                chunk = td[i * step : (i + 1) * step]
                v = float(chunk.mean()) if chunk.size else 0.0
                x = w * 0.08 + (i / (n - 1)) * w * 0.84
                pts.append(P(x, mid - v * amp))
        if len(pts) > 1:
            _line(draw, pts, tip, a, 4)
    img.alpha_composite(overlay)

