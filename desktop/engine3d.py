#!/usr/bin/env python3
"""ModernGL 3D visualizer for Renderbolt.

Renders isometric bars, a waveform ribbon, a circular halo, a liquid
terrain mesh, plus Levels / Particles / Spine / Radial wave (inspired by
Cavasik/CAVA, original code). Returns packed RGB24 frames for ffmpeg.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

VERT = """
#version 330
uniform mat4 u_mvp;
uniform mat4 u_model;
in vec3 in_pos;
in vec3 in_n;
in vec3 in_col;
out vec3 v_pos;
out vec3 v_n;
out vec3 v_col;
void main() {
    vec4 world = u_model * vec4(in_pos, 1.0);
    v_pos = world.xyz;
    v_n = mat3(u_model) * in_n;
    v_col = in_col;
    gl_Position = u_mvp * world;
}
"""

FRAG = """
#version 330
uniform vec3 u_light;
uniform vec3 u_eye;
uniform float u_alpha;
uniform vec3 u_fog;
in vec3 v_pos;
in vec3 v_n;
in vec3 v_col;
out vec4 f_color;
void main() {
    vec3 n = normalize(v_n);
    vec3 l = normalize(u_light - v_pos);
    vec3 e = normalize(u_eye - v_pos);
    vec3 h = normalize(l + e);
    float diff = max(dot(n, l), 0.22);
    float spec = pow(max(dot(n, h), 0.0), 36.0);
    vec3 col = v_col * (0.35 + 0.65 * diff) + v_col * spec * 0.16;
    float fog = smoothstep(6.0, 18.0, length(u_eye - v_pos));
    col = mix(col, u_fog, fog * 0.22);
    f_color = vec4(col, u_alpha);
}
"""

COVER_VERT = """
#version 330
uniform mat4 u_mvp;
in vec3 in_pos;
in vec2 in_uv;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = u_mvp * vec4(in_pos, 1.0);
}
"""

COVER_FRAG = """
#version 330
uniform sampler2D u_tex;
uniform float u_dim;
in vec2 v_uv;
out vec4 f_color;
void main() {
    vec3 c = texture(u_tex, vec2(v_uv.x, 1.0 - v_uv.y)).rgb;
    f_color = vec4(c * u_dim, 1.0);
}
"""


def _mat4_identity() -> np.ndarray:
    return np.eye(4, dtype=np.float32)


def _mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a @ b


def _perspective(fov: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(fov / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def _look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    z = eye - target
    z /= np.linalg.norm(z)
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    m = _mat4_identity()
    m[0, :3] = x
    m[1, :3] = y
    m[2, :3] = z
    m[0, 3] = -np.dot(x, eye)
    m[1, 3] = -np.dot(y, eye)
    m[2, 3] = -np.dot(z, eye)
    return m


def _translate(x: float, y: float, z: float) -> np.ndarray:
    m = _mat4_identity()
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def _scale(x: float, y: float, z: float) -> np.ndarray:
    m = _mat4_identity()
    m[0, 0] = x
    m[1, 1] = y
    m[2, 2] = z
    return m


def _rotate_z(deg: float) -> np.ndarray:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    m = _mat4_identity()
    m[0, 0] = c
    m[0, 1] = -s
    m[1, 0] = s
    m[1, 1] = c
    return m


def _hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0


def _sample(bands: np.ndarray, i: int, n: int) -> float:
    if bands.size == 0:
        return 0.0
    if n <= 1:
        return float(bands[0])
    idx = int(round(i / max(1, n - 1) * (len(bands) - 1)))
    return float(bands[max(0, min(len(bands) - 1, idx))])


def _quad_xy(x0: float, y0: float, x1: float, y1: float, z: float = 0.0) -> np.ndarray:
    return np.array(
        [
            [x0, y0, z], [x1, y0, z], [x1, y1, z],
            [x0, y0, z], [x1, y1, z], [x0, y1, z],
        ],
        dtype=np.float32,
    )


def _cube() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unit cube 0..1 with per-face normals. 36 verts."""
    faces = [
        ((0, 0, 1), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),  # +z
        ((0, 0, 0), (1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)),  # -z
        ((1, 0, 0), (1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)),  # +x
        ((-1, 0, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),  # -x
        ((0, 1, 0), (0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),  # +y
        ((0, -1, 0), (0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)),  # -y
    ]
    # redo cleanly
    def face(n, verts):
        i0, i1, i2, i3 = verts
        return [(i0, n), (i1, n), (i2, n), (i0, n), (i2, n), (i3, n)]

    quads = [
        face((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        face((0, 0, -1), [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)]),
        face((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        face((-1, 0, 0), [(0, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 0)]),
        face((0, 1, 0), [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)]),
        face((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    ]
    pos, nrm = [], []
    for q in quads:
        for p, n in q:
            pos.append(p)
            nrm.append(n)
    return (
        np.array(pos, dtype=np.float32),
        np.array(nrm, dtype=np.float32),
        np.ones((len(pos), 3), dtype=np.float32),
    )


class VisualEngine3D:
    def __init__(self, width: int, height: int) -> None:
        import moderngl

        self.w = width
        self.h = height
        self.ctx = self._context(moderngl)
        self.TRIANGLES = moderngl.TRIANGLES
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND | moderngl.CULL_FACE)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.prog = self.ctx.program(vertex_shader=VERT, fragment_shader=FRAG)
        self.cover_prog = self.ctx.program(vertex_shader=COVER_VERT, fragment_shader=COVER_FRAG)
        self.color_tex = self.ctx.texture((width, height), 3)
        self.depth_tex = self.ctx.depth_texture((width, height))
        self.fbo = self.ctx.framebuffer(color_attachments=[self.color_tex], depth_attachment=self.depth_tex)
        self.cover_tex = self.ctx.texture((8, 8), 3, np.zeros((8 * 8 * 3,), dtype=np.uint8).tobytes())
        self.cover_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.cover_tex.repeat_x = False
        self.cover_tex.repeat_y = False
        self._cover_vbo = None
        self._cover_vao = None
        self._ndc_vbo = None
        self._ndc_vao = None
        self._dyn_vbo = self.ctx.buffer(reserve=8 * 1024 * 1024)
        self._cube_pos, self._cube_n, _ = _cube()
        self._build_cover_quad()
        self._build_ndc_cover()
        info = getattr(self.ctx, "info", {}) or {}
        self.renderer = str(info.get("GL_RENDERER") or "")
        self.vendor = str(info.get("GL_VENDOR") or "")

    @staticmethod
    def _context(moderngl: Any) -> Any:
        errors: list[str] = []
        for kwargs in (
            {"standalone": True, "require": 330},
            {"standalone": True, "require": 330, "backend": "egl"},
            {"standalone": True, "require": 330, "backend": "wgl"},
        ):
            try:
                return moderngl.create_context(**kwargs)
            except Exception as exc:  # pragma: no cover
                errors.append(f"{kwargs}: {exc}")
        raise RuntimeError("ModernGL context failed (" + " | ".join(errors) + ")")

    def _build_cover_quad(self) -> None:
        # Fullscreen-ish plane in world space, facing +Z, slightly receded.
        pos = np.array(
            [
                [-8.0, -4.5, -3.2, 0.0, 1.0],
                [8.0, -4.5, -3.2, 1.0, 1.0],
                [8.0, 4.5, -3.2, 1.0, 0.0],
                [-8.0, -4.5, -3.2, 0.0, 1.0],
                [8.0, 4.5, -3.2, 1.0, 0.0],
                [-8.0, 4.5, -3.2, 0.0, 0.0],
            ],
            dtype=np.float32,
        )
        self._cover_vbo = self.ctx.buffer(pos.tobytes())
        self._cover_vao = self.ctx.simple_vertex_array(
            self.cover_prog, self._cover_vbo, "in_pos", "in_uv"
        )

    def _build_ndc_cover(self) -> None:
        pos = np.array(
            [
                [-1.0, -1.0, 0.0, 0.0, 1.0],
                [1.0, -1.0, 0.0, 1.0, 1.0],
                [1.0, 1.0, 0.0, 1.0, 0.0],
                [-1.0, -1.0, 0.0, 0.0, 1.0],
                [1.0, 1.0, 0.0, 1.0, 0.0],
                [-1.0, 1.0, 0.0, 0.0, 0.0],
            ],
            dtype=np.float32,
        )
        self._ndc_vbo = self.ctx.buffer(pos.tobytes())
        self._ndc_vao = self.ctx.simple_vertex_array(
            self.cover_prog, self._ndc_vbo, "in_pos", "in_uv"
        )

    def set_cover(self, image: Any) -> None:
        arr = np.asarray(image.convert("RGB").resize((self.w, self.h)), dtype=np.uint8)
        arr = np.flipud(arr)
        if self.cover_tex.size != (self.w, self.h):
            import moderngl

            self.cover_tex.release()
            self.cover_tex = self.ctx.texture((self.w, self.h), 3, arr.tobytes())
            self.cover_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        else:
            self.cover_tex.write(arr.tobytes())

    def _camera(self, tilt_deg: float, t: float, pulse: float) -> tuple[np.ndarray, np.ndarray]:
        tilt = math.radians(tilt_deg)
        yaw = math.radians(28.0 + math.sin(t * 0.15) * 6.0)
        dist = 9.4 - pulse * 0.45
        eye = np.array(
            [
                math.sin(yaw) * math.cos(tilt) * dist,
                math.sin(tilt) * dist + 1.1,
                math.cos(yaw) * math.cos(tilt) * dist,
            ],
            dtype=np.float32,
        )
        target = np.array([0.0, 0.35, 0.0], dtype=np.float32)
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        view = _look_at(eye, target, up)
        proj = _perspective(math.radians(42.0), self.w / self.h, 0.12, 40.0)
        return _mul(proj, view), eye

    def _draw_mesh(self, pos: np.ndarray, nrm: np.ndarray, col: np.ndarray, mvp: np.ndarray, model: np.ndarray, eye: np.ndarray, alpha: float, fog: tuple[float, float, float], light: np.ndarray) -> None:
        n = pos.shape[0]
        packed = np.concatenate([pos, nrm, col], axis=1).astype(np.float32)
        self._dyn_vbo.write(packed.tobytes())
        vao = self.ctx.simple_vertex_array(self.prog, self._dyn_vbo, "in_pos", "in_n", "in_col")
        self.prog["u_mvp"].write(mvp.T.tobytes())
        self.prog["u_model"].write(model.T.tobytes())
        self.prog["u_light"].value = tuple(float(x) for x in light)
        self.prog["u_eye"].value = tuple(float(x) for x in eye)
        self.prog["u_alpha"].value = float(alpha)
        self.prog["u_fog"].value = fog
        vao.render(mode=self.TRIANGLES, vertices=n)

    def render_rgb(
        self,
        analysis: dict,
        style: str,
        theme: tuple[str, str, str],
        bounce: float,
        zoom_state: list[float],
        tilt: float,
        vis_alpha: float,
        t: float,
        place: dict | None = None,
        mode: str = "3D",
    ) -> bytes:
        primary = _hex_rgb(theme[0])
        secondary = _hex_rgb(theme[1] if len(theme) > 1 else theme[0])
        pulse = float(analysis["pulse"]) * bounce
        target = 1.08 + pulse * 0.14 + float(analysis["bass"]) * 0.04
        zoom_state[0] = zoom_state[0] + (target - zoom_state[0]) * 0.28
        place = place or {}
        bands = np.asarray(analysis["bands"], dtype=np.float32)
        td = np.asarray(analysis["time"], dtype=np.float32)
        alpha = float(np.clip(vis_alpha, 0.18, 1.0))

        self.fbo.use()
        self.ctx.viewport = (0, 0, self.w, self.h)
        self.ctx.clear(0.04, 0.04, 0.043, 1.0)

        if str(mode).upper() == "2D":
            self._render_2d(bands, td, style, primary, secondary, pulse, zoom_state[0], alpha, t, place)
        else:
            self._render_3d(bands, td, style, primary, secondary, pulse, zoom_state[0], alpha, t, tilt, place)

        raw = self.fbo.read(components=3, alignment=1)
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(self.h, self.w, 3)
        return np.ascontiguousarray(np.flipud(frame)).tobytes()

    def _render_3d(self, bands, td, style, primary, secondary, pulse, zoom, alpha, t, tilt, place) -> None:
        mvp, eye = self._camera(tilt, t, pulse)
        light = np.array([3.2, 7.4, 5.0], dtype=np.float32)
        fog = (0.04, 0.04, 0.045)

        cover_mvp = _mul(mvp, _scale(zoom, zoom, 1.0))
        self.ctx.disable(self.ctx.DEPTH_TEST)
        self.cover_tex.use(0)
        self.cover_prog["u_tex"].value = 0
        self.cover_prog["u_dim"].value = 0.62 - pulse * 0.08
        self.cover_prog["u_mvp"].write(cover_mvp.T.tobytes())
        self._cover_vao.render()
        self.ctx.enable(self.ctx.DEPTH_TEST)

        sx = float(place.get("sx") or 1.0)
        sy = float(place.get("sy") or 1.0)
        if place.get("mirror"):
            sx = -sx
        model = _mul(
            _translate(float(place.get("x") or 0) * 4.2, float(place.get("y") or 0) * 2.4, 0.0),
            _mul(_rotate_y(float(place.get("rot") or 0)), _scale(sx, sy, abs(sx))),
        )

        if style == "EQ bars":
            pos, nrm, col = self._mesh_bars(bands, primary, secondary)
        elif style == "Circular":
            pos, nrm, col = self._mesh_halo(bands, pulse, primary, secondary)
        elif style == "Liquid waves":
            pos, nrm, col = self._mesh_terrain(bands, t, primary, secondary)
        elif style == "Levels":
            pos, nrm, col = self._mesh_levels(bands, primary, secondary)
        elif style == "Particles":
            pos, nrm, col = self._mesh_particles(bands, primary, secondary)
        elif style == "Spine":
            pos, nrm, col = self._mesh_spine(bands, primary, secondary)
        elif style == "Radial wave":
            pos, nrm, col = self._mesh_radial_wave(bands, pulse, primary, secondary)
        else:
            pos, nrm, col = self._mesh_ribbon(td, bands, t, primary, secondary)

        self._draw_mesh(pos, nrm, col, mvp, model, eye, alpha, fog, light)

    def _render_2d(self, bands, td, style, primary, secondary, pulse, zoom, alpha, t, place) -> None:
        self.ctx.disable(self.ctx.DEPTH_TEST)
        ident = _mat4_identity()
        cover_mvp = _scale(zoom, zoom, 1.0)
        self.cover_tex.use(0)
        self.cover_prog["u_tex"].value = 0
        self.cover_prog["u_dim"].value = 0.62 - pulse * 0.08
        self.cover_prog["u_mvp"].write(cover_mvp.T.tobytes())
        self._ndc_vao.render()

        sx = float(place.get("sx") or 1.0)
        sy = float(place.get("sy") or 1.0)
        if place.get("mirror"):
            sx = -sx
        model = _mul(
            _translate(float(place.get("x") or 0) * 0.9, float(place.get("y") or 0) * 0.7, 0.0),
            _mul(_rotate_z(float(place.get("rot") or 0)), _scale(sx, sy, 1.0)),
        )
        eye = np.array([0.0, 0.0, 2.0], dtype=np.float32)
        light = np.array([0.2, 0.8, 2.4], dtype=np.float32)
        fog = (0.04, 0.04, 0.045)

        if style == "EQ bars":
            pos, nrm, col = self._mesh_2d_eq(bands, primary, secondary)
        elif style == "Circular":
            pos, nrm, col = self._mesh_2d_circular(bands, pulse, primary, secondary)
        elif style == "Liquid waves":
            pos, nrm, col = self._mesh_2d_liquid(bands, t, primary, secondary)
        elif style == "Levels":
            pos, nrm, col = self._mesh_2d_levels(bands, primary, secondary)
        elif style == "Particles":
            pos, nrm, col = self._mesh_2d_particles(bands, primary, secondary)
        elif style == "Spine":
            pos, nrm, col = self._mesh_2d_spine(bands, primary, secondary)
        elif style == "Radial wave":
            pos, nrm, col = self._mesh_2d_radial(bands, pulse, primary, secondary)
        else:
            pos, nrm, col = self._mesh_2d_wave(td, primary, secondary)

        self._draw_mesh(pos, nrm, col, ident, model, eye, alpha, fog, light)

    def _mesh_2d_eq(self, bands: np.ndarray, primary, secondary):
        n = 48
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        span, gap = 1.68, 0.006
        bw = span / n - gap
        for i in range(n):
            v = float(bands[int(i / max(1, n - 1) * (len(bands) - 1))])
            x0 = -0.84 + i * (span / n)
            x1 = x0 + bw
            y0, y1 = -0.92, -0.92 + 0.05 + v * 0.42
            p = np.array(
                [[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y0, 0], [x1, y1, 0], [x0, y1, 0]],
                dtype=np.float32,
            )
            c = _grad(primary, secondary, 0.15 + v * 0.85)
            pos.append(p)
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_levels(self, bands: np.ndarray, primary, secondary):
        n, rows = 28, 10
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        span, gap = 1.72, 0.012
        bw = span / n - gap
        cell_h, cell_gap = 0.072, 0.01
        y_base = -0.90
        for i in range(n):
            v = _sample(bands, i, n)
            q = max(0, min(rows, int(round(v * rows))))
            x0 = -0.86 + i * (span / n)
            x1 = x0 + bw
            for r in range(q):
                y0 = y_base + r * (cell_h + cell_gap)
                y1 = y0 + cell_h
                c = _grad(primary, secondary, 0.12 + (r / max(1, rows - 1)) * 0.88)
                pos.append(_quad_xy(x0, y0, x1, y1))
                nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
                col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        if not pos:
            pos.append(_quad_xy(-0.02, -0.9, 0.02, -0.88))
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(np.array(primary, dtype=np.float32).reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_particles(self, bands: np.ndarray, primary, secondary):
        n = 36
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        span = 1.72
        size = 0.038
        for i in range(n):
            v = _sample(bands, i, n)
            cx = -0.86 + (i + 0.5) * (span / n)
            cy = -0.86 + v * 1.55
            c = _grad(primary, secondary, 0.2 + v * 0.8)
            pos.append(_quad_xy(cx - size, cy - size, cx + size, cy + size))
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_spine(self, bands: np.ndarray, primary, secondary):
        n = 22
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        span = 1.70
        for i in range(n):
            v = max(0.06, _sample(bands, i, n))
            half = v * 0.11
            cx = -0.85 + (i + 0.5) * (span / n)
            c = _grad(primary, secondary, v)
            pos.append(_quad_xy(cx - half, -half, cx + half, half))
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_radial(self, bands: np.ndarray, pulse: float, primary, secondary):
        n = 72
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        inner = 0.18 + pulse * 0.02
        for i in range(n):
            v0 = _sample(bands, i, n)
            v1 = _sample(bands, (i + 1) % n, n)
            a0 = i / n * math.tau - math.pi / 2
            a1 = (i + 1) / n * math.tau - math.pi / 2
            r0, r1 = inner + v0 * 0.42, inner + v1 * 0.42
            c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            p = np.array(
                [
                    [c0 * inner, s0 * inner, 0],
                    [c1 * inner, s1 * inner, 0],
                    [c1 * r1, s1 * r1, 0],
                    [c0 * inner, s0 * inner, 0],
                    [c1 * r1, s1 * r1, 0],
                    [c0 * r0, s0 * r0, 0],
                ],
                dtype=np.float32,
            )
            c = _grad(primary, secondary, 0.25 + 0.75 * v0)
            pos.append(p)
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_wave(self, td: np.ndarray, primary, secondary):
        samples = 160
        step = max(1, td.size // samples)
        vals = np.array(
            [float(td[i * step : (i + 1) * step].mean()) if td.size else 0.0 for i in range(samples)],
            dtype=np.float32,
        )
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        for i in range(samples - 1):
            x0 = -0.86 + 1.72 * (i / (samples - 1))
            x1 = -0.86 + 1.72 * ((i + 1) / (samples - 1))
            y0, y1 = -0.78 + vals[i] * 0.22, -0.78 + vals[i + 1] * 0.22
            thick = 0.018
            p = np.array(
                [
                    [x0, y0 - thick, 0], [x1, y1 - thick, 0], [x1, y1 + thick, 0],
                    [x0, y0 - thick, 0], [x1, y1 + thick, 0], [x0, y0 + thick, 0],
                ],
                dtype=np.float32,
            )
            c = _grad(primary, secondary, 0.5 + 0.5 * vals[i])
            pos.append(p)
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_circular(self, bands: np.ndarray, pulse: float, primary, secondary):
        n = 64
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        inner = 0.22 + pulse * 0.03
        for i in range(n):
            v = float(bands[int(i / n * len(bands)) % len(bands)])
            a0 = i / n * math.tau - math.pi / 2
            a1 = (i + 0.72) / n * math.tau - math.pi / 2
            outer = inner + 0.06 + v * 0.32
            c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            p = np.array(
                [
                    [c0 * inner, s0 * inner + 0.06, 0],
                    [c1 * inner, s1 * inner + 0.06, 0],
                    [c1 * outer, s1 * outer + 0.06, 0],
                    [c0 * inner, s0 * inner + 0.06, 0],
                    [c1 * outer, s1 * outer + 0.06, 0],
                    [c0 * outer, s0 * outer + 0.06, 0],
                ],
                dtype=np.float32,
            )
            c = _grad(primary, secondary, v)
            pos.append(p)
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_2d_liquid(self, bands: np.ndarray, t: float, primary, secondary):
        n = 48
        pos, nrm, col = [], [], []
        front = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        ys = []
        for i in range(n):
            tt = i / (n - 1)
            b = float(bands[int(tt * (len(bands) - 1))])
            ys.append(-0.62 - math.sin(tt * math.pi * 3 + t) * 0.08 - b * 0.12)
        for i in range(n - 1):
            x0 = -1.0 + 2.0 * (i / (n - 1))
            x1 = -1.0 + 2.0 * ((i + 1) / (n - 1))
            p = np.array(
                [
                    [x0, -1.0, 0], [x1, -1.0, 0], [x1, ys[i + 1], 0],
                    [x0, -1.0, 0], [x1, ys[i + 1], 0], [x0, ys[i], 0],
                ],
                dtype=np.float32,
            )
            c = _grad(primary, secondary, 0.35 + 0.5 * ((ys[i] + 0.4) / 0.5))
            pos.append(p)
            nrm.append(np.repeat(front.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_bars(self, bands: np.ndarray, primary, secondary) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = 48
        cube_p, cube_n = self._cube_pos, self._cube_n
        pos_list = []
        nrm_list = []
        col_list = []
        for i in range(n):
            v = float(bands[int(i / (n - 1) * (len(bands) - 1))])
            h = 0.12 + v * 3.4
            x = -4.4 + i * (8.8 / (n - 1))
            w = 0.14
            d = 0.42 + v * 0.35
            p = cube_p * np.array([w, h, d], dtype=np.float32) + np.array([x - w * 0.5, 0.0, -d * 0.5], dtype=np.float32)
            t = i / (n - 1)
            c = _grad(primary, secondary, 0.15 + v * 0.85)
            pos_list.append(p)
            nrm_list.append(cube_n)
            col_list.append(np.repeat(c.reshape(1, 3), p.shape[0], axis=0))
        return (
            np.concatenate(pos_list),
            np.concatenate(nrm_list),
            np.concatenate(col_list).astype(np.float32),
        )

    def _mesh_levels(self, bands: np.ndarray, primary, secondary):
        n, rows = 24, 8
        cube_p, cube_n = self._cube_pos, self._cube_n
        pos_list, nrm_list, col_list = [], [], []
        for i in range(n):
            v = _sample(bands, i, n)
            q = max(0, min(rows, int(round(v * rows))))
            x = -4.2 + i * (8.4 / max(1, n - 1))
            w, d, ch, gap = 0.22, 0.28, 0.28, 0.06
            for r in range(q):
                y = r * (ch + gap)
                p = cube_p * np.array([w, ch, d], dtype=np.float32) + np.array(
                    [x - w * 0.5, y, -d * 0.5], dtype=np.float32
                )
                c = _grad(primary, secondary, 0.12 + (r / max(1, rows - 1)) * 0.88)
                pos_list.append(p)
                nrm_list.append(cube_n)
                col_list.append(np.repeat(c.reshape(1, 3), p.shape[0], axis=0))
        if not pos_list:
            p = cube_p * 0.12
            pos_list.append(p)
            nrm_list.append(cube_n)
            col_list.append(np.repeat(np.array(primary, dtype=np.float32).reshape(1, 3), p.shape[0], axis=0))
        return np.concatenate(pos_list), np.concatenate(nrm_list), np.concatenate(col_list).astype(np.float32)

    def _mesh_particles(self, bands: np.ndarray, primary, secondary):
        n = 32
        cube_p, cube_n = self._cube_pos, self._cube_n
        pos_list, nrm_list, col_list = [], [], []
        size = 0.22
        for i in range(n):
            v = _sample(bands, i, n)
            x = -4.4 + i * (8.8 / max(1, n - 1))
            y = 0.15 + v * 3.2
            p = cube_p * size + np.array([x - size * 0.5, y, -size * 0.5], dtype=np.float32)
            c = _grad(primary, secondary, 0.2 + v * 0.8)
            pos_list.append(p)
            nrm_list.append(cube_n)
            col_list.append(np.repeat(c.reshape(1, 3), p.shape[0], axis=0))
        return np.concatenate(pos_list), np.concatenate(nrm_list), np.concatenate(col_list).astype(np.float32)

    def _mesh_spine(self, bands: np.ndarray, primary, secondary):
        n = 20
        cube_p, cube_n = self._cube_pos, self._cube_n
        pos_list, nrm_list, col_list = [], [], []
        for i in range(n):
            v = max(0.08, _sample(bands, i, n))
            s = 0.18 + v * 0.95
            x = -4.2 + i * (8.4 / max(1, n - 1))
            p = cube_p * s + np.array([x - s * 0.5, 0.4 - s * 0.5, -s * 0.5], dtype=np.float32)
            c = _grad(primary, secondary, v)
            pos_list.append(p)
            nrm_list.append(cube_n)
            col_list.append(np.repeat(c.reshape(1, 3), p.shape[0], axis=0))
        return np.concatenate(pos_list), np.concatenate(nrm_list), np.concatenate(col_list).astype(np.float32)

    def _mesh_radial_wave(self, bands: np.ndarray, pulse: float, primary, secondary):
        n = 64
        inner = 1.35 + pulse * 0.08
        pos, nrm, col = [], [], []
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        for i in range(n):
            v0 = _sample(bands, i, n)
            v1 = _sample(bands, (i + 1) % n, n)
            a0 = i / n * math.tau - math.pi / 2
            a1 = (i + 1) / n * math.tau - math.pi / 2
            r0, r1 = inner + v0 * 1.7, inner + v1 * 1.7
            y = 0.35
            p = np.array(
                [
                    [math.cos(a0) * inner, y, math.sin(a0) * inner],
                    [math.cos(a1) * inner, y, math.sin(a1) * inner],
                    [math.cos(a1) * r1, y, math.sin(a1) * r1],
                    [math.cos(a0) * inner, y, math.sin(a0) * inner],
                    [math.cos(a1) * r1, y, math.sin(a1) * r1],
                    [math.cos(a0) * r0, y, math.sin(a0) * r0],
                ],
                dtype=np.float32,
            )
            c = _grad(primary, secondary, 0.2 + v0 * 0.8)
            pos.append(p)
            nrm.append(np.repeat(up.reshape(1, 3), 6, axis=0))
            col.append(np.repeat(c.reshape(1, 3), 6, axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_ribbon(self, td: np.ndarray, bands: np.ndarray, t: float, primary, secondary):
        samples = 160
        step = max(1, td.size // samples)
        vals = np.array([float(td[i * step : (i + 1) * step].mean()) for i in range(samples)], dtype=np.float32)
        width_z = 1.35
        pos = []
        nrm = []
        col = []
        for i in range(samples - 1):
            x0 = -4.6 + 9.2 * (i / (samples - 1))
            x1 = -4.6 + 9.2 * ((i + 1) / (samples - 1))
            y0 = vals[i] * 2.4
            y1 = vals[i + 1] * 2.4
            z0, z1 = -width_z * 0.5, width_z * 0.5
            # two quads: top ribbon + sides for thickness
            h = 0.08
            p = np.array(
                [
                    [x0, y0, z0], [x1, y1, z0], [x1, y1, z1],
                    [x0, y0, z0], [x1, y1, z1], [x0, y0, z1],
                    [x0, y0 - h, z0], [x1, y1 - h, z0], [x1, y1, z0],
                    [x0, y0 - h, z0], [x1, y1, z0], [x0, y0, z0],
                ],
                dtype=np.float32,
            )
            n = np.array(
                [[0, 1, 0]] * 6 + [[0, 0, -1]] * 6,
                dtype=np.float32,
            )
            mix = 0.5 + 0.5 * vals[i]
            c = _grad(primary, secondary, mix)
            pos.append(p)
            nrm.append(n)
            col.append(np.repeat(c.reshape(1, 3), p.shape[0], axis=0))
        return np.concatenate(pos), np.concatenate(nrm), np.concatenate(col).astype(np.float32)

    def _mesh_halo(self, bands: np.ndarray, pulse: float, primary, secondary):
        n = 64
        radius = 2.15 + pulse * 0.12
        cube_p, cube_n = self._cube_pos, self._cube_n
        pos_list, nrm_list, col_list = [], [], []
        for i in range(n):
            ang = i / n * math.tau - math.pi / 2
            v = float(bands[int(i / n * len(bands)) % len(bands)])
            h = 0.2 + v * 2.6
            cx = math.cos(ang) * radius
            cz = math.sin(ang) * radius
            w, d = 0.11, 0.11
            p = cube_p * np.array([w, h, d], dtype=np.float32)
            # rotate around Y to face outward
            ca, sa = math.cos(ang), math.sin(ang)
            rot = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]], dtype=np.float32)
            p = p @ rot.T + np.array([cx, 0.0, cz], dtype=np.float32)
            nn = cube_n @ rot.T
            c = _grad(primary, secondary, v)
            pos_list.append(p)
            nrm_list.append(nn)
            col_list.append(np.repeat(np.clip(c, 0, 1).reshape(1, 3), p.shape[0], axis=0))
        return np.concatenate(pos_list), np.concatenate(nrm_list), np.concatenate(col_list).astype(np.float32)

    def _mesh_terrain(self, bands: np.ndarray, t: float, primary, secondary):
        nx, nz = 40, 22
        xs = np.linspace(-5.0, 5.0, nx)
        zs = np.linspace(-2.6, 2.4, nz)
        hmap = np.zeros((nz, nx), dtype=np.float32)
        for z in range(nz):
            for x in range(nx):
                b = float(bands[int(x / (nx - 1) * (len(bands) - 1))])
                hmap[z, x] = (
                    math.sin(x * 0.45 + t * 1.1 + z * 0.3) * 0.18
                    + math.sin(x * 0.15 + t * 0.5) * 0.12
                    + b * (0.9 + 0.35 * math.sin(z * 0.4 + t))
                )
        pos, nrm, col = [], [], []
        for z in range(nz - 1):
            for x in range(nx - 1):
                p00 = np.array([xs[x], hmap[z, x], zs[z]])
                p10 = np.array([xs[x + 1], hmap[z, x + 1], zs[z]])
                p11 = np.array([xs[x + 1], hmap[z + 1, x + 1], zs[z + 1]])
                p01 = np.array([xs[x], hmap[z + 1, x], zs[z + 1]])
                n = np.cross(p10 - p00, p01 - p00)
                ln = np.linalg.norm(n) or 1.0
                n = n / ln
                v = max(0.0, min(1.0, (hmap[z, x] + 0.2) / 1.6))
                c = _grad(primary, secondary, v)
                pos.extend([p00, p10, p11, p00, p11, p01])
                nrm.extend([n] * 6)
                col.extend([c] * 6)
        return (
            np.array(pos, dtype=np.float32),
            np.array(nrm, dtype=np.float32),
            np.array(col, dtype=np.float32),
        )


def _grad(base, tip, t: float) -> np.ndarray:
    t = float(max(0.0, min(1.0, t)))
    return np.array(base, dtype=np.float32) * (1.0 - t) + np.array(tip, dtype=np.float32) * t


def try_create(width: int, height: int) -> VisualEngine3D | None:
    try:
        return VisualEngine3D(width, height)
    except Exception:
        return None
