"""Ajuste de VIVACIDADE da paleta (2026-11-02): o dono viu os moldes com as cores medidas nas fotos e disse que "a maior diferença foi que todas as cores ficaram muito mais vivas, e não é isso".
O celular exagera a saturação; aqui a cor de cada conta é puxada para o cinza no Lab (a luminosidade e o matiz ficam): croma' = croma x s, com s = 1 igual à medida na foto.
Funções (sem dependência de cv2): rgb2lab, lab2rgb, tone(hex, s) -> hex."""
import numpy as np

_M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
_W = np.array([0.95047, 1.0, 1.08883])


def rgb2lab(rgb):
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = (_M @ c) / _W
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def lab2rgb(lab):
    L, a, b = lab
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    f = np.array([fx, fy, fz]); xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787) * _W
    c = np.linalg.inv(_M) @ xyz
    c = np.where(c > 0.0031308, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255.0, 0, 255)


def tone(rgb, s):
    """cor com o croma multiplicado por s (matiz e luminosidade iguais)"""
    L, a, b = rgb2lab(rgb)
    return lab2rgb(np.array([L, a * s, b * s]))


def hex2rgb(h): return np.array([int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
def rgb2hex(t): return '#%02X%02X%02X' % tuple(int(round(v)) for v in t)


def tone_knee(rgb, s, c0=28.0):
    """compressão de croma com JOELHO: até c0 a cor não muda (pele, creme e pastéis ficam como estão); acima, croma' = c0 + (croma - c0) x s. É o que tira o aspecto neon das cores
    mais saturadas sem deixar a pele cinza (a escala linear cinzenta o bege)."""
    L, a, b = rgb2lab(rgb); c = float(np.hypot(a, b))
    if c <= c0 or s >= 1.0: return np.asarray(rgb, float)
    k = (c0 + (c - c0) * s) / c
    return lab2rgb(np.array([L, a * k, b * k]))
