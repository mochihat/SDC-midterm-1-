"""Road paint from the front camera vs the LiDAR intensity map (24/10): building blocks.

The LoGeR clouds limit the GNSS-free tracker to ~0.5-1 m (depth errors grow with range), while the LiDAR map's intensity
shows the road paint (lane lines, stop lines, arrows, crosswalks) to a few cm, and the front camera sees the same paint
5-18 m ahead. Inverse perspective mapping (IPM): a grid of points on the road surface (heights from the map) is
projected into the fisheye image with the camera calibration of Track*_images/camera_info (same car / camera / hood
mask on all tracks); the image brightness there is the camera's view of the ground. Paint on both sides = white
top-hat (value minus its grey opening with a --paint-size square): only bright structures narrower than ~0.7 m survive
(lines, stop lines, crosswalk bars, arrows), not cars, sidewalks or the bright side of a shadow edge.

  MapPaint(points xyzi)      ground height (0.5 m cells, low percentile) + intensity raster (0.1 m, mean intensity of
                             the points within 0.12 m of the ground); paint_raster() -> map paint
  Camera(track_dir)          OpenCV fisheye model of the front camera (gige_100_f_hdr) + mounting + hood mask
  FrameImages(cache, track)  grey front images decoded by tools/paint_images.py (raw memmap)
  bev(img, cam, mp, pose)    image brightness on a vehicle-frame ground grid
  PaintMatcher               masked zero-mean NCC of camera paint vs map paint over along / lateral shifts (FFT),
                             yaw and pitch candidates
"""
import json
import os

import numpy as np
from scipy import ndimage


def read_camera_yaml(path):
    """camera_matrix / distortion_coefficients of a ROS camera_info yaml (no yaml module needed)"""
    txt = open(path).read()

    def block(name):
        i = txt.index(name)
        j = txt.index("data:", i)
        k = txt.index("[", j)
        return np.array([float(v) for v in txt[k + 1:txt.index("]", k)].split(",")])
    K = block("camera_matrix").reshape(3, 3)
    D = block("distortion_coefficients")
    w = int(txt.split("image_width:")[1].split()[0])
    h = int(txt.split("image_height:")[1].split()[0])
    return K, D, w, h


class Camera:
    """front camera; mounting (vehicle frame x forward, y left, z up): position (lx, ly, height above the road) and
    pitch (down, deg), roll, yaw (left, deg). Images may be row crops (row0, rows); mask: True = usable pixel"""

    def __init__(self, track, data="/w/data", name="gige_100_f_hdr", lx=0.0, ly=0.0, height=1.646, pitch=0.5,
                 roll=0.0, yaw=0.0, row0=0, rows=None, mask=None):
        d = os.path.join(data, f"Track{track}", f"Track{track}_images", "camera_info")
        K, D, w, h = read_camera_yaml(os.path.join(d, f"{name}_camera_info.yaml"))
        self.K, self.D, self.w, self.full_h = K, D, w, h
        self.row0, self.rows = row0, (h - row0 if rows is None else rows)
        self.mask = mask
        self.set_mount(lx, ly, height, pitch, roll, yaw)

    def set_mount(self, lx, ly, height, pitch, roll, yaw):
        self.lx, self.ly, self.height = lx, ly, height
        self.pitch, self.roll, self.yaw = pitch, roll, yaw
        p, r, y = np.radians([pitch, roll, yaw])
        cy, sy, cp, sp, cr, sr = np.cos(y), np.sin(y), np.cos(p), np.sin(p), np.cos(r), np.sin(r)
        Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
        Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
        Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
        R0 = np.array([[0.0, 0.0, 1.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])   # camera axes (right, down, fwd) in V
        self.R_vc = Rz @ Ry @ Rx @ R0

    def project(self, Pv):
        """vehicle-frame points (n, 3), z relative to the road plane under the vehicle -> (u, v in the crop), valid"""
        Pc = (Pv - np.array([self.lx, self.ly, self.height])) @ self.R_vc     # = R_vc^T (Pv - t)
        x, y, z = Pc[:, 0], Pc[:, 1], Pc[:, 2]
        r = np.hypot(x, y)
        th = np.arctan2(r, z)
        th2 = th * th
        k1, k2, k3, k4 = self.D
        thd = th * (1 + k1 * th2 + k2 * th2 ** 2 + k3 * th2 ** 3 + k4 * th2 ** 4)
        sc = np.where(r > 1e-9, thd / np.maximum(r, 1e-9), 0.0)
        u = self.K[0, 0] * sc * x + self.K[0, 2]
        v = self.K[1, 1] * sc * y + self.K[1, 2]
        ok = (z > 0.5) & (u >= 0) & (u <= self.w - 1) & (v >= self.row0) & (v <= self.row0 + self.rows - 1)
        if self.mask is not None:
            ok[ok] = self.mask[np.round(v[ok]).astype(int), np.round(u[ok]).astype(int)]
        return u, v - self.row0, ok


def load_mask(cache, track):
    """hood mask (camera_info/gige_100_f_hdr_mask.png, converted by tools/paint_images.py): True = usable"""
    m = np.fromfile(os.path.join(cache, f"Track{track}", "img", "f_mask.raw"), np.uint8).reshape(928, 1440)
    return m < 128


class FrameImages:
    """grey front-camera images (crop rows row0..row0+rows) of tools/paint_images.py; frame k -> array or None"""

    def __init__(self, cache, track):
        d = os.path.join(cache, f"Track{track}", "img")
        meta = json.load(open(os.path.join(d, "f_gray.json")))
        self.row0, self.rows, self.width, self.first = meta["row0"], meta["rows"], meta["width"], meta["first_frame"]
        self.raw = np.memmap(os.path.join(d, meta["file"]), np.uint8, "r").reshape(-1, self.rows, self.width)

    def get(self, k):
        j = k - self.first
        if j < 0 or j >= len(self.raw):
            return None
        return np.asarray(self.raw[j], dtype=np.float32)


def bilinear(img, u, v):
    u0 = np.clip(np.floor(u).astype(int), 0, img.shape[1] - 2)
    v0 = np.clip(np.floor(v).astype(int), 0, img.shape[0] - 2)
    du, dv = u - u0, v - v0
    a = img[v0, u0] * (1 - du) + img[v0, u0 + 1] * du
    b = img[v0 + 1, u0] * (1 - du) + img[v0 + 1, u0 + 1] * du
    return a * (1 - dv) + b * dv


class MapPaint:
    """ground height and road-surface intensity rasters of the LiDAR map"""

    def __init__(self, pts, res=0.1, gcell=0.5, band=0.12, imax=255.0):
        self.res, self.gcell = res, gcell
        self.x0, self.y0 = float(np.floor(pts[:, 0].min())), float(np.floor(pts[:, 1].min()))
        gx = ((pts[:, 0] - self.x0) / gcell).astype(np.int32)
        gy = ((pts[:, 1] - self.y0) / gcell).astype(np.int32)
        self.gnx, self.gny = gx.max() + 1, gy.max() + 1
        cell = gx.astype(np.int64) * self.gny + gy
        # ground: 10th percentile of z per cell (lexsort by cell, then z)
        o = np.lexsort((pts[:, 2], cell))
        cs = cell[o]
        start = np.r_[0, np.flatnonzero(np.diff(cs)) + 1]
        cnt = np.diff(np.r_[start, len(cs)])
        pick = o[start + (cnt * 0.1).astype(np.int64)]
        g = np.full(self.gnx * self.gny, np.nan, np.float32)
        g[cs[start]] = pts[pick, 2]
        g = g.reshape(self.gnx, self.gny)
        # cells with too few points or above their neighbours (cars, walls): replace by a robust neighbourhood minimum
        n = np.zeros(self.gnx * self.gny, np.int64)
        n[cs[start]] = cnt
        n = n.reshape(self.gnx, self.gny)
        g[n < 5] = np.nan
        filled = ndimage.generic_filter(np.nan_to_num(g, nan=1e4), np.nanmin, size=3, mode="nearest")
        low = ndimage.percentile_filter(np.where(np.isnan(g), 1e4, g), 30, size=5, mode="nearest")
        bad = np.isnan(g) | (g > low + 0.25)
        g[bad] = np.minimum(filled, low)[bad]
        g[g > 1e3] = np.nan
        self.ground = g
        zg = self.ground_at(pts[:, 0], pts[:, 1])
        on = np.abs(pts[:, 2] - zg) < band
        p = pts[on]
        self.nx = int(np.ceil((pts[:, 0].max() - self.x0) / res)) + 1
        self.ny = int(np.ceil((pts[:, 1].max() - self.y0) / res)) + 1
        ix = ((p[:, 0] - self.x0) / res).astype(np.int64)
        iy = ((p[:, 1] - self.y0) / res).astype(np.int64)
        flat = ix * self.ny + iy
        s = np.bincount(flat, weights=np.minimum(p[:, 3], imax), minlength=self.nx * self.ny)
        c = np.bincount(flat, minlength=self.nx * self.ny)
        with np.errstate(invalid="ignore"):
            inten = (s / c).reshape(self.nx, self.ny).astype(np.float32)
        self.count = c.reshape(self.nx, self.ny)
        self.inten = inten

    @classmethod
    def load(cls, path):
        """rasters saved by tools/paint_map.py"""
        z = np.load(path)
        mp = cls.__new__(cls)
        mp.x0, mp.y0, mp.res, mp.gcell = float(z["x0"]), float(z["y0"]), float(z["res"]), float(z["gcell"])
        mp.ground, mp.inten, mp.count = z["ground"], z["inten"], z["count"]
        mp.gnx, mp.gny = mp.ground.shape
        mp.nx, mp.ny = mp.inten.shape
        return mp

    def ground_at(self, x, y):
        """bilinear ground height (NaN outside / unknown)"""
        fx = (np.asarray(x) - self.x0) / self.gcell - 0.5
        fy = (np.asarray(y) - self.y0) / self.gcell - 0.5
        i0 = np.clip(np.floor(fx).astype(int), 0, self.gnx - 2)
        j0 = np.clip(np.floor(fy).astype(int), 0, self.gny - 2)
        dx, dy = np.clip(fx - i0, 0, 1), np.clip(fy - j0, 0, 1)
        g = self.ground
        return (g[i0, j0] * (1 - dx) * (1 - dy) + g[i0 + 1, j0] * dx * (1 - dy) + g[i0, j0 + 1] * (1 - dx) * dy
                + g[i0 + 1, j0 + 1] * dx * dy)

    def sample(self, x, y, raster=None):
        """nearest-cell value of a 0.1 m raster (default: intensity); NaN outside"""
        r = self.inten if raster is None else raster
        ix = np.round((np.asarray(x) - self.x0) / self.res).astype(int)
        iy = np.round((np.asarray(y) - self.y0) / self.res).astype(int)
        ok = (ix >= 0) & (ix < self.nx) & (iy >= 0) & (iy < self.ny)
        out = np.full(ix.shape, np.nan, np.float32)
        out[ok] = r[ix[ok], iy[ok]]
        return out


def white_tophat(r, size_cells, valid=None):
    """r minus its grey opening (square of size_cells): bright structures narrower than the square; 0 where invalid"""
    if valid is None:
        valid = np.isfinite(r)
    lo = np.nanmin(r[valid]) if valid.any() else 0.0
    f = np.where(valid, r, lo)
    th = f - ndimage.grey_opening(f, size=(size_cells, size_cells))
    th[~valid] = 0.0
    return th


def local_level(r, valid, block=5, q=70.0, win=7):
    """local 'sunlit road' level: q-th percentile per block x block cells, median over win x win blocks, upsampled"""
    na, nl = r.shape
    pa, pl = (-na) % block, (-nl) % block
    f = np.pad(np.where(valid, r, np.nan), ((0, pa), (0, pl)), constant_values=np.nan)
    blk = f.reshape(f.shape[0] // block, block, f.shape[1] // block, block).transpose(0, 2, 1, 3).reshape(
        f.shape[0] // block, f.shape[1] // block, -1)
    srt = np.sort(blk, axis=2)                                  # NaN last
    nv = np.isfinite(blk).sum(axis=2)
    idx = np.clip(np.floor(q / 100.0 * (nv - 1)).astype(int), 0, blk.shape[2] - 1)
    bq = np.take_along_axis(srt, idx[..., None], axis=2)[..., 0]
    bq[nv == 0] = np.nan
    fill = np.nanmedian(bq) if np.isfinite(bq).any() else 0.0
    bq = ndimage.median_filter(np.where(np.isfinite(bq), bq, fill), size=win, mode="nearest")
    return np.repeat(np.repeat(bq, block, axis=0), block, axis=1)[:na, :nl]


def camera_paint_image(b, seen, k, q_level=70.0):
    """camera paint: brightness above BOTH its grey opening (thin bright structures) and the local sunlit-road level
    (the sunny gaps of tree shadows are road, not paint)"""
    lo = np.nanmin(b[seen]) if seen.any() else 0.0
    f = np.where(seen, b, lo)
    base = np.maximum(ndimage.grey_opening(f, size=(k, k)), local_level(b, seen, q=q_level))
    th = np.clip(f - base, 0, None)
    th[~seen] = 0.0
    return th


def paint_raster(mp, size_m=0.7, q=99.5):
    """map paint: white top-hat of the road-surface intensity, scaled by its q-th percentile, clipped to [0, 1]"""
    have = mp.count > 0
    k = max(3, int(round(size_m / mp.res)) | 1)
    th = white_tophat(mp.inten.astype(np.float32), k, have)
    pos = th[th > 0]
    s = np.percentile(pos, q) if len(pos) else 1.0
    return np.clip(th / s, 0, 1).astype(np.float32)


def ground_frame(mp, x, y, yaw, along=(-2.0, 3.0), lat=(-1.5, 1.5)):
    """road plane under the car: (z0, slope along, slope left) fitted to the map ground raster under the wheels"""
    a, l = np.meshgrid(np.arange(along[0], along[1] + 0.01, 0.5), np.arange(lat[0], lat[1] + 0.01, 0.5),
                       indexing="ij")
    a, l = a.ravel(), l.ravel()
    c, s = np.cos(yaw), np.sin(yaw)
    z = mp.ground_at(x + a * c - l * s, y + a * s + l * c)
    ok = np.isfinite(z)
    if ok.sum() < 6:
        return np.array([np.nanmedian(z) if ok.any() else 0.0, 0.0, 0.0])
    A = np.stack([np.ones(ok.sum()), a[ok], l[ok]], axis=1)
    return np.linalg.lstsq(A, z[ok], rcond=None)[0]


def bev_grid(along=(5.0, 18.0), lat=(-7.0, 7.0), res=0.1):
    a = np.arange(along[0], along[1] + 1e-6, res)
    l = np.arange(lat[0], lat[1] + 1e-6, res)
    A, L = np.meshgrid(a, l, indexing="ij")
    return A, L


def bev(img, cam, mp, x, y, yaw, A, L, plane=None):
    """image brightness on the road grid (A along, L left, vehicle frame) at pose (x, y, yaw); NaN where unseen.
    Heights: the map ground under each grid point relative to the road plane under the vehicle"""
    c, s = np.cos(yaw), np.sin(yaw)
    z0, ga, gl = ground_frame(mp, x, y, yaw) if plane is None else plane
    zg = mp.ground_at(x + A * c - L * s, y + A * s + L * c)
    zrel = np.where(np.isfinite(zg), zg - (z0 + ga * A + gl * L), 0.0)
    Pv = np.stack([A.ravel(), L.ravel(), zrel.ravel()], axis=1)
    u, v, ok = cam.project(Pv)
    out = np.full(A.size, np.nan, np.float32)
    out[ok] = bilinear(img, u[ok], v[ok])
    return out.reshape(A.shape), (z0, ga, gl)


class PaintMatcher:
    """masked zero-mean NCC of the camera paint (IPM white top-hat) with the map paint, over along / lateral shifts
    (FFT, scipy.signal.fftconvolve), yaw candidates and camera pitch candidates (the car pitches with acceleration)"""

    def __init__(self, mp, paint, cam, along=(5.0, 18.0), lat=(-7.0, 7.0), res=0.1, s_along=2.0, s_lat=1.0,
                 yaws=np.arange(-1.5, 1.51, 0.25), pitches=(0.0,), paint_size=0.7, min_seen=2000, q_level=70.0):
        from scipy.signal import fftconvolve
        self.fftconvolve = fftconvolve
        self.mp, self.paint, self.cam, self.res = mp, paint, cam, res
        self.A, self.L = bev_grid(along, lat, res)
        na, nl = int(round(s_along / res)), int(round(s_lat / res))
        self.na, self.nl = na, nl
        a = along[0] - na * res + res * np.arange(self.A.shape[0] + 2 * na)
        l = lat[0] - nl * res + res * np.arange(self.A.shape[1] + 2 * nl)
        self.Ae, self.Le = np.meshgrid(a, l, indexing="ij")
        self.yaws, self.pitches = np.asarray(yaws, float), np.asarray(pitches, float)
        self.k = max(3, int(round(paint_size / res)) | 1)
        self.min_seen = min_seen
        self.q_level = q_level

    def camera_paint(self, img, x, y, yaw):
        """camera paint for every pitch candidate: (zero-mean paint on the seen cells / 0 elsewhere, seen mask)"""
        out = []
        p0 = self.cam.pitch
        plane = ground_frame(self.mp, x, y, yaw)
        for dp in self.pitches:
            self.cam.set_mount(self.cam.lx, self.cam.ly, self.cam.height, p0 + dp, self.cam.roll, self.cam.yaw)
            b, _ = bev(img, self.cam, self.mp, x, y, yaw, self.A, self.L, plane)
            seen = np.isfinite(b)
            th = camera_paint_image(b, seen, self.k, self.q_level) if self.q_level > 0 else white_tophat(b, self.k, seen)
            if seen.sum() >= self.min_seen:
                q = np.percentile(th[seen], 99.5)
                th = np.clip(th / max(q, 1.0), 0, 1)
            out.append((th, seen))
        self.cam.set_mount(self.cam.lx, self.cam.ly, self.cam.height, p0, self.cam.roll, self.cam.yaw)
        return out

    def ncc_volume(self, img, x, y, yaw):
        """NCC volume (pitch, yaw, along shift, lateral shift). One 'seen' mask (cells seen at every pitch) for all
        candidates, so the map window statistics are per yaw only; FFTs of the camera paint per pitch and of the map
        per yaw are shared (scipy.fft)"""
        from scipy import fft as sfft
        cams = self.camera_paint(img, x, y, yaw)
        seen = np.logical_and.reduce([sn for _, sn in cams])
        n = int(seen.sum())
        P, Y = len(self.pitches), len(self.yaws)
        vol = np.full((P, Y, 2 * self.na + 1, 2 * self.nl + 1), -1.0)
        if n < self.min_seen:
            return vol
        shape = (self.Ae.shape[0], self.Ae.shape[1])
        fshape = [sfft.next_fast_len(v, real=True) for v in shape]
        sl = (slice(self.A.shape[0] - 1, shape[0]), slice(self.A.shape[1] - 1, shape[1]))
        w = seen.astype(np.float64)
        Fw = sfft.rfft2(w[::-1, ::-1], fshape)
        Fc, cc = [], []
        for th, _ in cams:
            cz = np.where(seen, th - th[seen].mean(), 0.0)
            cc.append(float((cz * cz).sum()))
            Fc.append(sfft.rfft2(cz[::-1, ::-1], fshape))
        for iy_, dy in enumerate(np.radians(self.yaws)):
            c, s = np.cos(yaw + dy), np.sin(yaw + dy)
            m = np.nan_to_num(self.mp.sample(x + self.Ae * c - self.Le * s, y + self.Ae * s + self.Le * c,
                                             self.paint), nan=0.0).astype(np.float64)
            Fm = sfft.rfft2(m, fshape)
            s1 = sfft.irfft2(Fm * Fw, fshape)[sl]
            s2 = sfft.irfft2(sfft.rfft2(m * m, fshape) * Fw, fshape)[sl]
            var = np.maximum(s2 - s1 * s1 / n, 1e-9)
            for ip in range(P):
                if cc[ip] <= 1e-9:
                    continue
                num = sfft.irfft2(Fm * Fc[ip], fshape)[sl]
                vol[ip, iy_] = num / np.sqrt(cc[ip] * var)
        return vol

    def peak(self, vol):
        """(d_along, d_lat, d_yaw deg, d_pitch deg, ncc) of the volume maximum, sub-cell by parabola fits.
        Camera cell p matching map cell p + s -> the vehicle is s further along / left"""
        k = np.unravel_index(np.argmax(vol), vol.shape)
        ip, iy_, ia, il = k

        def sub(v, i):
            if 0 < i < len(v) - 1:
                d = v[i - 1] - 2 * v[i] + v[i + 1]
                if d < 0:
                    return 0.5 * (v[i - 1] - v[i + 1]) / d
            return 0.0
        da = (ia - self.na + sub(vol[ip, iy_, :, il], ia)) * self.res
        dl = (il - self.nl + sub(vol[ip, iy_, ia, :], il)) * self.res
        sy = self.yaws[1] - self.yaws[0] if len(self.yaws) > 1 else 0.0
        dyw = self.yaws[iy_] + sub(vol[ip, :, ia, il], iy_) * sy
        sp = self.pitches[1] - self.pitches[0] if len(self.pitches) > 1 else 0.0
        dpt = self.pitches[ip] + sub(vol[:, iy_, ia, il], ip) * sp
        return da, dl, dyw, dpt, float(vol[k])
