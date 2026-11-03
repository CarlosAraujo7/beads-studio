"""RAMPA DE CINZAS PARA MOLDES QUASE TODOS PRETOS (2026-11-03; pedido do dono: "o Xenomorfo é todo preto, fica ruim quando feito; seria bacana ter gradientes com cinza e detalhes nesses moldes majoritariamente pretos").
Causa: `illus5.convert5` quantiza a imagem em centros de cor e acha a conta de cada centro por `r5.near120(..., dark=True)`; qualquer tom escuro (corpo azul-petróleo escuro, L 10-30) fica mais perto do PRETO H7 (L 20)
do que de qualquer outra conta (o próximo degrau neutro, o cinza escuro H5, tem L 42), então o corpo inteiro vira a mesma conta preta do contorno e o desenho vira uma silhueta.
Aqui o `center_map` do convert5 (gancho que já existe) manda os centros ESCUROS E POUCO COLORIDOS que ficaram em preto (H7/H6) e que são mais claros que o contorno para o cinza escuro H5: o contorno e as sombras mais fundas
continuam pretos (H7), o corpo ganha o cinza (H5) e os tons que o near120 já escolhia acima disso (H4, H3, brilhos coloridos) não mudam. Cores vivas (olho verde, dentes, brilho de menta) e tons escuros coloridos (vinho, verde escuro) não são tocados.
Só vale para ILUSTRAÇÃO/adesivo (convert5). Gráfico em malha ou pixel art é cópia fiel e o preto dele é o da imagem (CLAUDE.md §4.1).
uso (no CFG de um rN_exfinal):  center_map=DR.ramp()          ou      center_map=DR.ramp(lo=18, cmax=30, base=outro_center_map)
parâmetros: lo = claridade L (do centro, depois do realce) a partir da qual o escuro deixa de ser preto e vira H5 (padrão 21: o preto H7 tem L 20 e o H5 tem L 42, o ponto médio é ~31 na conta, ~22 na imagem);
            cmax = croma máximo do centro para virar cinza (acima disso é cor de verdade); hi = claridade a partir da qual não mexe (o near120 já escolhe H5/H4/H3 certo); mid2/hi2 = segundo degrau opcional (H4)."""
import os, sys, colorsys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import palette as P

L = {c['code']: c['letter'] for c in P.ALL}
BLACKS = {L['H7'], L['H6'], 'k'}


def _lab_chroma(rgb):
    """croma Lab (D65) de um RGB 0-255"""
    c = np.array(rgb, float) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    X = 0.4124564 * c[0] + 0.3575761 * c[1] + 0.1804375 * c[2]; Y = 0.2126729 * c[0] + 0.7151522 * c[1] + 0.0721750 * c[2]; Z = 0.0193339 * c[0] + 0.1191920 * c[1] + 0.9503041 * c[2]
    f = lambda t: t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0
    fx, fy, fz = f(X / 0.95047), f(Y), f(Z / 1.08883)
    a = 500 * (fx - fy); b = 200 * (fy - fz)
    return float((a * a + b * b) ** 0.5)


def ramp(lo=21.0, cmax=26.0, hi=44.0, mid2=None, base=None):
    """center_map(rgb médio, L, letra, é preto?) -> letra nova ou None. `base` = outro center_map do molde (vale primeiro)."""
    h5 = L['H5']; h4 = L['H4']

    def f(rgb, Lc, letter, is_black):
        if base:
            r = base(rgb, Lc, letter, is_black)
            if r: return r
        if is_black or letter not in BLACKS or Lc >= hi: return None
        if _lab_chroma(rgb) > cmax: return None
        if Lc < lo: return None
        if mid2 is not None and Lc >= mid2: return h4
        return h5
    return f


def black_share(rows):
    """fração das contas que são preto/quase preto (H7, H6, G8, B15, F7...) — para achar os moldes majoritariamente pretos"""
    import remap_cores as RC
    near = {c['letter'] for c in RC.NEW if c['code'] in ('H7', 'H6', 'G8', 'B15', 'B11', 'F7', 'D15')}
    n = sum(1 for r in rows for ch in r if ch != '.'); k = sum(1 for r in rows for ch in r if ch in near)
    return k / max(1, n)
