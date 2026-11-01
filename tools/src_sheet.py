import sys, glob, os
from PIL import Image, ImageDraw
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
base = os.path.dirname(SP)
r = sys.argv[1]; a = int(sys.argv[2]); b = int(sys.argv[3])
fs = sorted(glob.glob(os.path.join(base, 'remessas', f'remessa {r}', '*.*')))[a:b]
T = 230; cols = 6
rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * T, rows * (T + 16)), (40, 40, 44)); d = ImageDraw.Draw(sheet)
for k, f in enumerate(fs):
    im = Image.open(f).convert('RGB'); im.thumbnail((T - 6, T - 6))
    x = (k % cols) * T; y = (k // cols) * (T + 16)
    sheet.paste(im, (x + 3, y + 16)); d.text((x + 4, y + 2), f'{r}:{a + k}', fill=(255, 255, 0))
sheet.save(os.path.join(OUT, f'src_{r}_{a}.png'))
print(len(fs))
