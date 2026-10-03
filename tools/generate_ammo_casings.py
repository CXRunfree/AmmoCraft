"""Draw casing blanks that exactly occupy the approved multi-round mold slots.

Standard ammunition uses separate TaCZ body/projectile material colors. RPG
uses a PG-7V-inspired olive warhead and gray-brown motor. Requires Pillow.
"""
import hashlib

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from ammo_art import ROOT, TEXTURES, TACZ_ICONS
from generate_molds import COUNTS, multi_slot, components, slot_core


PREVIEW = ROOT / 'tools/previews/ammo_casings.png'
PAIRED_PREVIEW = ROOT / 'tools/previews/ammo_mold_casing_comparison.png'

# Unobscured projectile scanline and its approximate share of the full round.
PROJECTILE_REGIONS = {
    '9mm': (10, 0.32), '45acp': (10, 0.31),
    '357mag': (5, 0.20), '50ae': (6, 0.24),
    '46x30': (7, 0.33), '57x28': (7, 0.33),
    '58x42': (7, 0.32), '68x51fury': (7, 0.33),
    '556x45': (7, 0.32), '762x25': (9, 0.35),
    '762x39': (7, 0.32), '762x54': (7, 0.35),
    '308': (7, 0.36), '30_06': (8, 0.39),
    '338': (8, 0.40), '50bmg': (8, 0.41),
    '40mm': (6, 0.27),
}

RPG_MATERIALS = (
    (0.065, ('#353b3a', '#697472', '#a4aaa0', '#c0c2b1')),  # Nose fuze.
    (0.50, ('#303a22', '#4c5932', '#768451', '#a1aa73')),  # Olive warhead.
    (0.57, ('#2f3630', '#596659', '#85917d', '#adb49c')),  # Shoulder collar.
    (0.90, ('#373932', '#606154', '#898b77', '#afb09b')),  # Metallic motor tube.
    (1.01, ('#2f3828', '#515d3c', '#7b8860', '#a0aa80')),  # Tail stabilizers.
)


def material_strip(source, row):
    xs = [x for x in range(source.width) if source.getpixel((x, row))[3]]
    assert xs, row
    right = xs[0]
    while right + 1 in xs:
        right += 1
    return [source.getpixel((x, row)) for x in range(xs[0], right + 1)]


def brightness(color):
    return color[0] * 299 + color[1] * 587 + color[2] * 114


def rpg_strip(source, rows):
    # One sampled scanline missed most of TaCZ's bright olive/gray-green facets.
    # Build a broad lit face and shaded flank from the complete visible material.
    colors = sorted({source.getpixel((x, y)) for y in rows for x in range(source.width)
                     if source.getpixel((x, y))[3]}, key=lambda c: (brightness(c), c))
    def tone(fraction):
        return colors[round((len(colors) - 1) * fraction)]
    return [tone(0.20), tone(0.60), tone(1.0), tone(0.90),
            tone(0.75), tone(0.60), tone(0.40), tone(0.20)]


def palettes(ammo):
    with Image.open(TACZ_ICONS / f'{ammo}.png') as source:
        source = source.convert('RGBA')
        if ammo == '12g':
            # Red shell sleeve and brass head, both sampled below/above the label.
            return material_strip(source, 12), material_strip(source, 27), 0.76
        if ammo == '68x51fury':
            # TaCZ depicts the hybrid case with a brass body and steel case head.
            return material_strip(source, 14), material_strip(source, 26), 0.77
        if ammo == 'rpg_rocket':
            return rpg_strip(source, range(3, 16)), rpg_strip(source, range(23, 31)), 0.62
        strip = material_strip(source, 23)
        return strip, strip, 1.0


def projectile_material(ammo):
    if ammo not in PROJECTILE_REGIONS:
        return None  # 12g and RPG already have their own distinct material bands.
    row, share = PROJECTILE_REGIONS[ammo]
    with Image.open(TACZ_ICONS / f'{ammo}.png') as source:
        return material_strip(source.convert('RGBA'), row), share


def material_at(y, top, bottom, upper, lower, split, projectile):
    progress = (y - top) / max(1, bottom - top)
    if projectile and progress < projectile[1]:
        return projectile[0]
    return lower if progress >= split else upper


def pixel_finish(image, mask, bounds, upper, lower, split, projectile):
    """Soften fine shading into coarse MC-style pixels, preserving the slot mask."""
    finished = Image.new('RGBA', image.size)
    for columns in bounds:
        left, right = columns[0], columns[-1]
        rows = [y for y in range(64) if any(mask.getpixel((x, y)) for x in columns)]
        top, bottom = rows[0], rows[-1]
        box = (left, top, right + 1, bottom + 1)
        part = image.crop(box)
        # Work in premultiplied alpha so transparent black never darkens the edge.
        part = part.convert('RGBa').resize((max(1, (part.width + 1) // 2),
                                           max(1, (part.height + 1) // 2)), Image.Resampling.BOX)
        part = part.resize((right - left + 1, bottom - top + 1), Image.Resampling.NEAREST).convert('RGBA')
        for y in rows:
            palette = material_at(y, top, bottom, upper, lower, split, projectile)
            for x in columns:
                if mask.getpixel((x, y)):
                    color = part.getpixel((x - left, y - top))
                    # Quantize the softened color back to TaCZ's own material tones.
                    sampled = min(palette, key=lambda candidate: sum(
                        (a - b) ** 2 for a, b in zip(candidate[:3], color[:3])))
                    finished.putpixel((x, y), sampled)
    return finished


def body_detail(image, mask, bounds, upper, lower, split, projectile, ammo):
    """Keep the softened original shading, lowering broad case highlights only."""
    for columns in bounds:
        left, right = columns[0], columns[-1]
        rows = [y for y in range(64) if any(mask.getpixel((x, y)) for x in columns)]
        top, bottom = rows[0], rows[-1]
        start = next(y for y in rows if (y - top) / max(1, bottom - top)
                     >= (projectile[1] if projectile else split if ammo == 'rpg_rocket' else 0))
        for y in range(start, bottom + 1):
            palette = material_at(y, top, bottom, upper, lower, split, projectile)
            low = min(brightness(color) for color in palette)
            for x in columns:
                if not mask.getpixel((x, y)):
                    continue
                original = brightness(image.getpixel((x, y)))
                target = low + (original - low) * 0.80
                image.putpixel((x, y), min(palette, key=lambda color: abs(brightness(color) - target)))
    return image


def rpg_texture(mask):
    # Shade along the rocket's own axis; screen-space horizontal bands would
    # incorrectly cut across the newly tilted warhead and motor.
    from PIL import ImageColor
    materials = [(end, [ImageColor.getcolor(color, 'RGBA') for color in colors])
                 for end, colors in RPG_MATERIALS]
    points = [(x, y) for y in range(64) for x in range(64) if mask.getpixel((x, y))]
    tip, tail = max(x - y for x, y in points), min(x - y for x, y in points)
    sections = {}
    for x, y in points:
        sections.setdefault(x - y, []).append(x + y)
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(3)))
    image = Image.new('RGBA', mask.size)
    for x, y in points:
        progress = (tip - (x - y)) / max(1, tip - tail)
        palette = next(colors for end, colors in materials if progress < end)
        cross = sections[x - y]
        u = ((x + y) - min(cross)) / max(1, max(cross) - min(cross))
        shade = 1 if u < 0.12 else 3 if u < 0.34 else 2 if u < 0.65 else 1 if u < 0.90 else 0
        if edge.getpixel((x, y)):
            shade = min(shade, 2 if u < 0.5 else 1)
        # Narrow dark attachment rings distinguish the warhead, collar and tube.
        if 0.49 <= progress <= 0.515 or 0.56 <= progress <= 0.575:
            shade = min(shade, 1)
        image.putpixel((x, y), palette[shade])
    assert ImageChops.difference(image.getchannel('A'), mask).getbbox() is None
    assert components(mask) == 1
    return image, mask


def casing_texture(ammo):
    mask = multi_slot(ammo, COUNTS[ammo])
    if ammo == 'rpg_rocket':
        return rpg_texture(mask)
    upper, lower, split = palettes(ammo)
    projectile = projectile_material(ammo)
    image = Image.new('RGBA', (64, 64))
    bounds = []
    for x in range(64):
        if any(mask.getpixel((x, y)) for y in range(64)):
            if not bounds or x != bounds[-1][-1] + 1:
                bounds.append([x])
            else:
                bounds[-1].append(x)
    assert len(bounds) == COUNTS[ammo], ammo
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(3)))
    for columns in bounds:
        left, right = columns[0], columns[-1]
        rows = [y for y in range(64) if any(mask.getpixel((x, y)) for x in columns)]
        top, bottom = rows[0], rows[-1]
        for y in rows:
            palette = material_at(y, top, bottom, upper, lower, split, projectile)
            dark = min(palette, key=brightness)
            light = max(palette, key=brightness)
            occupied = [x for x in columns if mask.getpixel((x, y))]
            for x in occupied:
                fraction = (x - left) / max(1, right - left)
                index = min(len(palette) - 1, round(fraction * (len(palette) - 1)))
                color = palette[index]
                if edge.getpixel((x, y)):
                    color = dark
                    if ammo == 'rpg_rocket' and x == occupied[0] and y not in (top, bottom):
                        color = palette[1]
                # Keep the recessed crimp on 12g; projectile tips get their own
                # bright copper/silver highlights instead of a dark empty mouth.
                if ammo == '12g' and top + 1 <= y <= top + 2 and occupied[0] < x < occupied[-1]:
                    color = dark
                # A crisp raised extractor/head band adds depth at the case foot.
                if y == bottom - 2 and occupied[0] < x < occupied[-1]:
                    color = light
                image.putpixel((x, y), color)
    image = pixel_finish(image, mask, bounds, upper, lower, split, projectile)
    image = body_detail(image, mask, bounds, upper, lower, split, projectile, ammo)
    if projectile:
        # A fine material seam separates the nose from the case without changing
        # the shape. Each side retains its own highlight palette after softening.
        for columns in bounds:
            rows = [y for y in range(64) if any(mask.getpixel((x, y)) for x in columns)]
            top, bottom = rows[0], rows[-1]
            seam = top + max(1, round((bottom - top) * projectile[1])) - 1
            for x in columns:
                if mask.getpixel((x, seam)):
                    image.putpixel((x, seam), min(projectile[0], key=brightness))
        assert set(projectile[0]) != set(upper), (ammo, 'Projectile needs a separate material palette')
    assert ImageChops.difference(image.getchannel('A'), mask).getbbox() is None, ammo
    assert components(image.getchannel('A')) == COUNTS[ammo], ammo
    allowed = set(upper) | set(lower)
    if projectile:
        allowed |= set(projectile[0])
    assert all(pixel in allowed for pixel in image.getdata() if pixel[3]), ammo
    return image, mask


def checker(draw, left, top):
    for y in range(8):
        for x in range(8):
            color = '#56616b' if (x + y) % 2 else '#414b55'
            draw.rectangle((left + x * 16, top + y * 16,
                            left + x * 16 + 15, top + y * 16 + 15), fill=color)


def main():
    destination = TEXTURES / 'ammo/casings'
    destination.mkdir(parents=True, exist_ok=True)
    paired = Image.new('RGBA', (1600, 800), '#282c30')
    paired_draw = ImageDraw.Draw(paired)
    sheet = Image.new('RGBA', (800, 800), '#282c30')
    draw = ImageDraw.Draw(sheet)
    for index, ammo in enumerate(COUNTS):
        path = TEXTURES / f'ammo/molds/{ammo}.png'
        original_hash = hashlib.sha256(path.read_bytes()).digest()
        image, mask = casing_texture(ammo)
        with Image.open(path) as source:
            mold = source.convert('RGBA')
        # The round overlaps the inset bevel; the remaining center is transparent.
        core = slot_core(mask)
        for y in range(8, 56):
            for x in range(8, 56):
                assert bool(core.getpixel((x, y))) == (mold.getpixel((x, y))[3] == 0), ammo
                if mask.getpixel((x, y)) and not core.getpixel((x, y)):
                    assert mold.getpixel((x, y)) in ((98, 98, 98, 255), (153, 153, 153, 255)), ammo
        overlay = Image.alpha_composite(mold, image)
        for y in range(64):
            for x in range(64):
                if mask.getpixel((x, y)):
                    assert overlay.getpixel((x, y)) == image.getpixel((x, y)), (ammo, 'Uncovered bevel')
        image.save(destination / f'{ammo}.png')
        x, y = index % 5 * 320, index // 5 * 200
        paired_draw.text((x + 16, y + 10), ammo, fill='white')
        paired_draw.text((x + 16, y + 32), 'MOLD', fill='#B5BDC7')
        paired_draw.text((x + 176, y + 32), 'CASING BLANK', fill='#B5BDC7')
        for offset, texture in ((16, mold), (176, image)):
            checker(paired_draw, x + offset, y + 56)
            paired.alpha_composite(texture.resize((128, 128), Image.Resampling.NEAREST), (x + offset, y + 56))
        x, y = index % 5 * 160, index // 5 * 200
        draw.text((x + 16, y + 16), ammo, fill='white')
        checker(draw, x + 16, y + 48)
        sheet.alpha_composite(image.resize((128, 128), Image.Resampling.NEAREST), (x + 16, y + 48))
        assert hashlib.sha256(path.read_bytes()).digest() == original_hash, ammo
    sheet.save(PREVIEW)
    paired.save(PAIRED_PREVIEW)
    rpg_preview = Image.new('RGBA', (640, 352), '#282c30')
    rpg_draw = ImageDraw.Draw(rpg_preview)
    with Image.open(TEXTURES / 'ammo/molds/rpg_rocket.png') as source:
        rpg_mold = source.convert('RGBA')
    rpg_casing, _ = casing_texture('rpg_rocket')
    for left, title, texture in ((32, 'RPG MOLD', rpg_mold), (352, 'RPG CASING BLANK', rpg_casing)):
        rpg_draw.text((left, 24), title, fill='white')
        for y in range(8):
            for x in range(8):
                color = '#56616b' if (x + y) % 2 else '#414b55'
                rpg_draw.rectangle((left + x * 32, 56 + y * 32,
                                    left + x * 32 + 31, 56 + y * 32 + 31), fill=color)
        rpg_preview.alpha_composite(texture.resize((256, 256), Image.Resampling.NEAREST), (left, 56))
    rpg_preview.save(ROOT / 'tools/previews/rpg_mold_casing.png')
    overlay_preview = Image.new('RGBA', (528, 560), '#282c30')
    overlay_draw = ImageDraw.Draw(overlay_preview)
    for row, ammo in enumerate(('9mm', '762x54', 'rpg_rocket')):
        with Image.open(TEXTURES / f'ammo/molds/{ammo}.png') as source:
            mold_image = source.convert('RGBA')
        round_image, _ = casing_texture(ammo)
        combined = Image.alpha_composite(mold_image, round_image)
        top = row * 184
        overlay_draw.text((16, top + 8), ammo, fill='white')
        for left, title, texture in ((16, 'MOLD', mold_image), (192, 'AMMUNITION', round_image),
                                     (368, 'OVERLAY', combined)):
            overlay_draw.text((left, top + 28), title, fill='#B5BDC7')
            checker(overlay_draw, left, top + 48)
            overlay_preview.alpha_composite(texture.resize((128, 128), Image.Resampling.NEAREST), (left, top + 48))
    overlay_preview.save(ROOT / 'tools/previews/ammo_mold_overlay_preview.png')
    print('PASS: 19 transparent 64x64 casing textures; all inset mold bevels covered by ammunition.')
    print('PASS: TaCZ material colors for standard ammunition; realistic distinct RPG materials.')
    print('PASS: softened 2px material blocks; crisp binary alpha; no transparent-edge dark fringe.')
    print('PASS: separate TaCZ projectile/body palettes and independently colored highlights.')
    print('PASS: reduced case highlights without added stripes or wear; projectile colors preserved.')
    print(f'Textures: {destination}')
    print(f'Preview: {PAIRED_PREVIEW}')


if __name__ == '__main__':
    main()
