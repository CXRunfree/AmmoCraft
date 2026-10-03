"""Shared paths and TaCZ single-round contours for current AmmoCraft artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / 'src/main/resources/assets/ammocraft/textures/item'
TACZ_PACK = ROOT / 'tools/reference/tacz'
TACZ_ICONS = TACZ_PACK / 'assets/tacz/textures/ammo/slot'

def single_round_mask(ammo):
    """Trace the first TaCZ round; bridge the ribbon and overlapping rounds."""
    with Image.open(TACZ_ICONS / f'{ammo}.png') as source:
        alpha = source.convert('RGBA').getchannel('A')
    assert alpha.size == (32, 32), ammo
    spans = {}
    for y in range(32):
        if 16 <= y < 23:
            continue
        xs = [x for x in range(32) if alpha.getpixel((x, y))]
        if not xs:
            continue
        left = xs[0]
        right = left
        while right + 1 in xs:
            right += 1
        spans[y] = (left, right)
    if ammo in {'30_06', '338', '50bmg'}:
        # A horizontal round overlaps the foot of the first upright cartridge.
        # Continue its visible case walls rather than copying the extra round.
        left, right = spans[24]
        for y in range(25, max(spans) + 1):
            spans[y] = (left, right)
    elif ammo == '762x54':
        # The two upright cartridge rims touch on the final row.
        left, right = spans[28]
        spans[29] = (left - 1, right + 1)
    before, after = spans[15], spans[23]
    for y in range(16, 23):
        t = (y - 15) / 8
        spans[y] = tuple(round(a + (b - a) * t) for a, b in zip(before, after))
    mask = Image.new('L', (32, 32))
    draw = ImageDraw.Draw(mask)
    for y, (left, right) in spans.items():
        draw.line((left, y, right, y), fill=255)
    return mask.crop(mask.getbbox())


