"""Generate the current multi-round molds; RPG is tilted 45 degrees up-right."""
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from ammo_art import ROOT, TEXTURES, single_round_mask


COUNTS = {
    '9mm': 3, '45acp': 2, '357mag': 2, '50ae': 2,
    '46x30': 3, '57x28': 3, '58x42': 3, '68x51fury': 2,
    '556x45': 4, '762x25': 4, '762x39': 3, '762x54': 2,
    '308': 2, '30_06': 3, '338': 3, '50bmg': 2,
    '12g': 2, '40mm': 1, 'rpg_rocket': 1,
}


def upright_contour(ammo):
    # Recover a centered, solid contour rather than magnifying the tiny source
    # sprite's row offsets. Keep the TaCZ tip, shoulder and rim width profile.
    if ammo == 'rpg_rocket':
        # Redraw the broad warhead and straight shaft on a continuous centered
        # profile. Repeatedly rotating the low-resolution icon preserved kinks.
        width, height = 112, 440
        # PG-7V-inspired nose fuze, ogive warhead, tapered shoulder, motor tube
        # and compact folded tail stabilizers, instead of a generic diamond.
        stations = [(0.0, 0.12), (0.045, 0.13), (0.07, 0.20),
                    (0.17, 0.44), (0.30, 0.78), (0.40, 1.0),
                    (0.46, 0.96), (0.51, 0.58), (0.56, 0.31),
                    (0.88, 0.31), (0.91, 0.48), (0.96, 0.48), (1.0, 0.32)]
        profile = Image.new('L', (1, height))
        values = []
        for y in range(height):
            t = y / (height - 1)
            for (a, wa), (b, wb) in zip(stations, stations[1:]):
                if a <= t <= b:
                    values.append(round(255 * (wa + (wb - wa) * (t - a) / (b - a))))
                    break
        profile.putdata(values)
        profile = profile.filter(ImageFilter.GaussianBlur(9))
        clean = Image.new('L', (width, height))
        draw = ImageDraw.Draw(clean)
        for y in range(height):
            span = max(2, round(profile.getpixel((0, y)) * width / 255))
            span += (width - span) % 2
            left = (width - span) // 2
            draw.line((left, y, left + span - 1, y), fill=255)
        return clean
    shape = single_round_mask(ammo)
    widths = []
    for y in range(shape.height):
        xs = [x for x in range(shape.width) if shape.getpixel((x, y))]
        widths.append(xs[-1] - xs[0] + 1 if xs else 0)
    profile = Image.new('L', (1, shape.height))
    profile.putdata([round(width * 255 / shape.width) for width in widths])
    profile = profile.filter(ImageFilter.GaussianBlur(0.6))
    clean = Image.new('L', (shape.width * 8, shape.height * 8))
    draw = ImageDraw.Draw(clean)
    for y in range(clean.height):
        width = max(2, round(profile.getpixel((0, y // 8)) * clean.width / 255))
        # Match parity to keep every cross-section exactly centered.
        width += (clean.width - width) % 2
        left = (clean.width - width) // 2
        draw.line((left, y, left + width - 1, y), fill=255)
    return clean.filter(ImageFilter.GaussianBlur(2.0))


def multi_slot(ammo, count):
    shape = upright_contour(ammo)
    if ammo == 'rpg_rocket':
        assert count == 1
        shape = shape.rotate(-45, Image.Resampling.BICUBIC, expand=True)
        shape = shape.point(lambda value: 255 if value >= 128 else 0)
        shape = shape.crop(shape.getbbox())
        scale = 44 / max(shape.size)
        slot = shape.resize(tuple(round(d * scale) for d in shape.size), Image.Resampling.LANCZOS)
        slot = slot.filter(ImageFilter.GaussianBlur(0.5)).point(lambda value: 255 if value >= 128 else 0)
        assert components(slot) == 1, 'RPG contour must remain intact'
        mask = Image.new('L', (64, 64))
        mask.paste(slot, ((64 - slot.width) // 2, (64 - slot.height) // 2))
        return mask
    gap = max(1, round(shape.height * 4 / 32))
    group_width = shape.width * count + gap * (count - 1)
    extent = 44 if ammo == 'rpg_rocket' else 40
    scale = extent / max(group_width, shape.height)
    final_gap = max(3, round(gap * scale))
    slot_width = min(round(shape.width * scale), (extent - final_gap * (count - 1)) // count)
    slot_height = round(shape.height * scale)
    # Rasterize ONE slot and reuse it: each round has the same clean outline,
    # instead of acquiring different distortions from resizing the whole group.
    slot = shape.resize((slot_width, slot_height), Image.Resampling.LANCZOS)
    slot = slot.filter(ImageFilter.GaussianBlur(0.5))
    slot = slot.point(lambda value: 255 if value >= 128 else 0)
    slot = ImageChops.darker(slot, ImageOps.mirror(slot))
    assert ImageChops.difference(slot, ImageOps.mirror(slot)).getbbox() is None, ammo
    assert components(slot) == 1, (ammo, 'Each round must be one intact slot')
    for y in range(slot.height):
        xs = [x for x in range(slot.width) if slot.getpixel((x, y))]
        if xs:
            assert len(xs) == xs[-1] - xs[0] + 1, (ammo, 'Broken contour')
    group = Image.new('L', (slot_width * count + final_gap * (count - 1), slot_height))
    for index in range(count):
        group.paste(slot, (index * (slot_width + final_gap), 0))
    mask = Image.new('L', (64, 64))
    mask.paste(group, ((64 - group.width) // 2, (64 - group.height) // 2))
    return mask


def slot_core(cavity):
    """The transparent opening; the remaining outer pixels are the inset bevel."""
    return cavity.filter(ImageFilter.MinFilter(3))


def mold(ammo, count, blank):
    image = blank.copy()
    cavity = multi_slot(ammo, count)
    rim = ImageChops.subtract(cavity.filter(ImageFilter.MaxFilter(3)), cavity)
    image.paste('#151515', (0, 0), rim)
    # The lip occupies the ammunition's OUTER pixels, instead of growing outside
    # its footprint. A finished round laid on the mold covers the gray/white bevel.
    lip = ImageChops.subtract(cavity, slot_core(cavity))
    image.paste((0, 0, 0, 0), (0, 0), cavity)
    image.paste('#626262', (0, 0), lip)
    shifted = Image.new('L', cavity.size)
    shifted.paste(cavity, (-1, -1))
    image.paste('#999999', (0, 0), ImageChops.multiply(ImageChops.subtract(cavity, shifted), lip))
    return image, cavity


def components(mask):
    remaining = {(x, y) for y in range(mask.height) for x in range(mask.width)
                 if mask.getpixel((x, y))}
    count = 0
    while remaining:
        pending = [remaining.pop()]
        count += 1
        while pending:
            x, y = pending.pop()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                point = x + dx, y + dy
                if point in remaining:
                    remaining.remove(point)
                    pending.append(point)
    return count


def main():
    destination = TEXTURES / 'ammo/molds'
    destination.mkdir(parents=True, exist_ok=True)
    preview = Image.new('RGBA', (1200, 896), '#282c30')
    draw = ImageDraw.Draw(preview)
    with Image.open(TEXTURES / 'blank_mold.png') as source:
        blank = source.convert('RGBA').resize((64, 64), Image.Resampling.NEAREST)
    for index, (ammo, count) in enumerate(COUNTS.items()):
        image, cavity = mold(ammo, count, blank)
        core = slot_core(cavity)
        assert components(cavity) == count, ammo
        assert set(image.getchannel('A').getdata()) == {0, 255}, ammo
        x0, y0, x1, y1 = cavity.getbbox()
        assert x0 >= 10 and y0 >= 10 and x1 <= 54 and y1 <= 54, ammo
        for y in range(64):
            for x in range(64):
                pixel = image.getpixel((x, y))
                if core.getpixel((x, y)):
                    assert pixel[3] == 0, ammo
                elif cavity.getpixel((x, y)):
                    assert pixel in ((98, 98, 98, 255), (153, 153, 153, 255)), ammo
                elif x < 8 or y < 8 or x >= 56 or y >= 56:
                    assert pixel == blank.getpixel((x, y)), ammo
        image.save(destination / f'{ammo}.png')
        x, y = index % 5 * 240, index // 5 * 224
        draw.text((x + 24, y + 12), ammo, fill='white')
        for cy in range(8):
            for cx in range(8):
                color = '#56616b' if (cx + cy) % 2 else '#414b55'
                draw.rectangle((x + 24 + cx * 24, y + 28 + cy * 24,
                                x + 47 + cx * 24, y + 51 + cy * 24), fill=color)
        preview.alpha_composite(image.resize((192, 192), Image.Resampling.NEAREST), (x + 24, y + 28))
    (ROOT / 'tools/previews').mkdir(parents=True, exist_ok=True)
    preview.save(ROOT / 'tools/previews/ammo_molds.png')
    print('PASS: 19 current multi-round molds; RPG tilted up-right; inset bevels and blank borders.')


if __name__ == '__main__':
    main()


