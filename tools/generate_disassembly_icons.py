"""Original pixel art for ammunition disassembly and caliber powder.

Generates 20 transparent 64px textures, matching item models, and a contact sheet.
Assets only: this does not register items or change the current production recipes.
Run: python tools/generate_disassembly_icons.py (requires Pillow).
"""
from pathlib import Path
import json
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/ammocraft'
TEXTURES = ASSETS / 'textures/item'
MODELS = ASSETS / 'models/item'
PREVIEW = ROOT / 'tools/previews/ammo_disassembly_icons.png'
TACZ_ICONS = ROOT / 'tools/reference/tacz/assets/tacz/textures/ammo/slot'
TACZ_RECIPES = ROOT / 'tools/reference/tacz/data/tacz/recipes/ammo'
RIBBON_Y = 16 * 2  # Same normalized vertical position as the 32px TaCZ ammunition icons.


def vanilla_powder_sprite():
    with Image.open(ROOT / 'tools/reference/minecraft/gunpowder.png') as source:
        sprite = source.convert('RGBA')
    assert sprite.size == (16, 16)
    return sprite


def reference_preview():
    ids = ['9mm', '45acp', '68x51fury', '762x54', '50bmg', 'rpg_rocket']
    sheet = Image.new('RGB', (6 * 276, 290), '#253340')
    draw = ImageDraw.Draw(sheet)
    for i, caliber in enumerate(ids):
        with Image.open(TACZ_ICONS / f'{caliber}.png') as source:
            icon = source.convert('RGBA')
        print(f'{caliber}: {icon.size}')
        icon = icon.resize((256, 256), Image.Resampling.NEAREST)
        sheet.paste(icon, (i * 276 + 10, 28), icon)
        draw.text((i * 276 + 10, 8), caliber, fill='#FFFFFF')
    sheet.save(PREVIEW.parent / 'tacz_ammo_reference.png')

# Preview captions only; the actual lettering comes from the installed TaCZ icons.
LABELS = {
    '9mm': '9MM', '45acp': '.45 ACP',
    '357mag': '.357 MAG', '50ae': '.50 AE',
    '46x30': '4.6x30', '57x28': '5.7x28',
    '58x42': '5.8x42', '68x51fury': '6.8 FURY',
    '556x45': '5.56x45', '762x25': '7.62x25',
    '762x39': '7.62x39', '762x54': '7.62x54',
    '308': '.308', '30_06': '.30-06', '338': '.338',
    '50bmg': '.50 BMG', '12g': '12G',
    '40mm': '40MM', 'rpg_rocket': 'RPG',
}
PISTOL = {'9mm', '45acp', '357mag', '50ae', '46x30', '57x28', '762x25'}
SNIPER = {'762x54', '308', '30_06', '338', '50bmg'}


def accent(caliber):
    if caliber in PISTOL:
        return '#DEB66E'
    if caliber in SNIPER:
        return '#AD9CD5'
    if caliber in {'12g', '40mm', 'rpg_rocket'}:
        return '#D59279'
    return '#7DC8B5'


def canvas():
    return Image.new('RGBA', (32, 32), (0, 0, 0, 0))


def enlarge(image):
    return image.resize((64, 64), Image.Resampling.NEAREST)


def tacz_ribbon(caliber):
    with Image.open(TACZ_ICONS / f'{caliber}.png') as source:
        source = source.convert('RGBA')
    assert source.size == (32, 32), f'Unexpected TaCZ texture size: {caliber}'
    # Native TaCZ ribbon: seven rows, a single line of type, and a diagonal end.
    # Mask the tail explicitly so none of the old cartridges are copied with it.
    ribbon = source.crop((0, 16, 32, 23))
    background = source.getpixel((0, 16))
    right = max(x for x in range(32) if source.getpixel((x, 16)) == background)
    assert right >= 28, caliber
    mask = Image.new('L', ribbon.size, 0)
    draw = ImageDraw.Draw(mask)
    for y in range(7):
        draw.line((0, y, right - y, y), fill=255)
    ribbon.putalpha(mask)
    return ribbon.resize((64, 14), Image.Resampling.NEAREST)


def badge(image, caliber):
    # Match the original ammunition ribbon, including its vertical placement.
    image.alpha_composite(tacz_ribbon(caliber), (0, RIBBON_Y))
    return image


def powder_icon(caliber, vanilla, materials):
    image = canvas()
    # Use the recognizable vanilla silhouette and its original grayscale shading.
    body = vanilla.crop(vanilla.getbbox()).resize((28, 26), Image.Resampling.NEAREST)
    image.alpha_composite(body, (2, 3))
    draw = ImageDraw.Draw(image)
    # Only a few small, shaded grains; the gray powder remains the main subject.
    candidates = [(x, y) for y in range(5, 21) for x in range(4, 27)
                  if all(image.getpixel((x + dx, y + dy))[3]
                         for dx, dy in ((0, 0), (1, 0), (0, 1)))]
    used = set()

    def grains(targets, colors):
        for tx, ty in targets:
            x, y = min((p for p in candidates if p not in used),
                       key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)
            for offset, color in zip(((0, 0), (1, 0), (0, 1)), colors):
                draw.point((x + offset[0], y + offset[1]), fill=color)
                used.add((x + offset[0], y + offset[1]))

    if 'forge:gems/lapis' in materials:
        grains([(11, 9), (20, 12), (8, 17), (19, 19)],
               ['#95DBD7', '#42B7C1', '#287A91'])
    if 'forge:rods/blaze' in materials:
        grains([(16, 7), (12, 14), (24, 18)],
               ['#F6D17A', '#D2A548', '#886221'])
    return badge(enlarge(image), caliber)


def tool_icon():
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Native 64px art: forged steel jaws with a visible side face and bevels.
    # Warm brass / orange-brown grip colors echo Create's wrench material map.
    dark = '#292A2B'
    draw.polygon([(21, 5), (28, 5), (28, 18), (32, 24), (40, 30),
                  (40, 38), (30, 39), (18, 29), (15, 21), (17, 9)], fill=dark)
    draw.polygon([(36, 5), (43, 5), (47, 10), (49, 22), (44, 30),
                  (33, 39), (23, 38), (23, 30), (33, 23), (36, 18)], fill=dark)
    draw.polygon([(21, 7), (26, 7), (26, 19), (30, 25), (37, 31),
                  (36, 35), (29, 35), (20, 27), (18, 20), (20, 11)], fill='#93958F')
    draw.polygon([(38, 7), (42, 7), (45, 11), (47, 21), (42, 28),
                  (33, 35), (27, 35), (26, 32), (35, 24), (38, 19)], fill='#6B6E6B')
    draw.polygon([(42, 9), (45, 12), (47, 21), (42, 28), (34, 34),
                  (33, 31), (40, 25), (43, 19)], fill='#4F5352')
    draw.line([(21, 8), (20, 13), (19, 20), (22, 26), (29, 32)], fill='#D9D8C8', width=2)
    draw.line([(39, 8), (40, 19), (37, 24), (29, 31)], fill='#B6B9AF', width=2)
    draw.line([(24, 8), (24, 18)], fill='#B5B5AA', width=2)
    # Smooth recessed gripping faces: the mouth stays empty.
    draw.line([(27, 8), (27, 18), (30, 23)], fill='#424747', width=2)
    draw.line([(36, 8), (36, 18), (33, 23)], fill='#353B3B', width=2)
    # Continuous steel tangs extend from the pivot into both grips.
    draw.polygon([(22, 31), (30, 36), (23, 44), (17, 55),
                  (13, 60), (6, 57), (9, 49), (16, 37)], fill=dark)
    draw.polygon([(34, 36), (41, 31), (48, 38), (55, 49),
                  (58, 57), (51, 61), (46, 55), (40, 44)], fill=dark)
    draw.polygon([(21, 35), (26, 37), (21, 44), (14, 56),
                  (10, 55), (12, 48), (18, 38)], fill='#858B86')
    draw.polygon([(37, 37), (41, 35), (46, 40), (52, 50),
                  (54, 56), (50, 57), (43, 45)], fill='#535B59')
    draw.line([(19, 36), (14, 45), (11, 52)], fill='#D0D1BE')
    # Faceted orange-brass grips, dark flanks and transverse machining grooves.
    draw.polygon([(15, 41), (23, 45), (16, 58), (12, 61),
                  (5, 58), (7, 52)], fill='#493421')
    draw.polygon([(16, 43), (21, 46), (14, 57), (11, 59),
                  (7, 57), (9, 52)], fill='#B77E32')
    draw.line([(15, 45), (10, 54), (9, 56)], fill='#ECC16A', width=2)
    draw.line([(21, 47), (15, 58), (12, 60)], fill='#805126', width=2)
    draw.polygon([(41, 45), (49, 41), (57, 52), (59, 58),
                  (52, 62), (48, 59)], fill='#493421')
    draw.polygon([(43, 46), (48, 43), (54, 52), (56, 57),
                  (52, 59), (50, 56)], fill='#AA702E')
    draw.line([(44, 46), (50, 55), (52, 57)], fill='#DBA64F', width=2)
    draw.line([(49, 46), (55, 55), (55, 57)], fill='#744A27', width=2)
    for left, right in (((13, 48), (18, 50)), ((11, 52), (16, 54)),
                        ((46, 49), (51, 46)), ((49, 53), (54, 50))):
        draw.line([left, right], fill='#70502B')
    # Raised brass pivot housing and a recessed hexagonal steel fastener.
    draw.polygon([(26, 24), (37, 24), (43, 30), (43, 36),
                  (37, 41), (26, 41), (21, 36), (21, 30)], fill=dark)
    draw.polygon([(27, 26), (36, 26), (41, 31), (41, 35),
                  (36, 39), (27, 39), (23, 35), (23, 31)], fill='#A77B38')
    draw.line([(24, 31), (28, 27), (36, 27), (39, 30)], fill='#E9C675', width=2)
    draw.line([(40, 32), (40, 35), (36, 38), (28, 38)], fill='#684E2D', width=2)
    draw.polygon([(29, 28), (35, 28), (38, 31), (38, 35),
                  (35, 38), (29, 38), (26, 35), (26, 31)], fill='#3B403F')
    draw.polygon([(30, 29), (34, 29), (36, 31), (36, 34),
                  (34, 36), (30, 36), (28, 34), (28, 31)], fill='#8A938C')
    draw.line([(29, 31), (31, 30), (34, 30)], fill='#DBDCC9')
    return image


def write_asset(name, texture, image):
    path = TEXTURES / f'{texture}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / f'{name}.json').write_text(json.dumps({
        'parent': 'minecraft:item/generated',
        'textures': {'layer0': f'ammocraft:item/{texture}'},
    }, indent=2) + '\n', encoding='utf-8')


def preview(calibers, tool, powders):
    width, tile_width, tile_height, header = 1440, 288, 186, 170
    sheet = Image.new('RGB', (width, header + 4 * tile_height), '#17212C')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    sheet.paste(tool.resize((128, 128), Image.Resampling.NEAREST), (28, 18),
                tool.resize((128, 128), Image.Resampling.NEAREST))
    draw.text((176, 36), 'AMMUNITION DISASSEMBLY / TACZ-MATCHED RIBBONS', fill='#EDE4D0', font=font)
    draw.text((176, 61), 'DISASSEMBLY PLIERS | 19 POWDERS', fill='#ABC7CD', font=font)
    draw.text((176, 86), 'Caliber powder also selects the basin mixing recipe', fill='#ABC7CD', font=font)
    draw.text((176, 111), '64 x 64 RGBA textures; nearest-neighbor preview at 2x', fill='#ABC7CD', font=font)
    draw.text((176, 136), 'Single-line native TaCZ lettering; ribbon occupies only 14 of 64 rows', fill='#ABC7CD', font=font)
    draw.text((790, 61), 'VANILLA POWDER SHAPE | CYAN: LAPIS | GOLD: BLAZE', fill='#ABC7CD', font=font)
    for i, caliber in enumerate(calibers):
        x, y = (i % 5) * tile_width, header + (i // 5) * tile_height
        draw.rectangle((x + 4, y + 4, x + tile_width - 5, y + tile_height - 5), outline='#3B4E60')
        draw.text((x + 12, y + 12), LABELS[caliber], fill=accent(caliber), font=font)
        for j, icon in enumerate((powders[caliber],)):
            left, top = x + 10 + j * 140, y + 33
            for cy in range(0, 128, 16):
                for cx in range(0, 128, 16):
                    color = '#253340' if (cx // 16 + cy // 16) % 2 == 0 else '#2D3D4B'
                    draw.rectangle((left + cx, top + cy, left + cx + 15, top + cy + 15), fill=color)
            enlarged = icon.resize((128, 128), Image.Resampling.NEAREST)
            sheet.paste(enlarged, (left, top), enlarged)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)


def main():
    registry = ROOT / 'src/main/java/cn/crtlprototypestudios/ammocraft/registry/AmmoItems.java'
    calibers = re.findall(r'new Caliber\("([^"]+)"', registry.read_text(encoding='utf-8'))
    assert len(calibers) == 19 and set(calibers) == set(LABELS)
    vanilla = vanilla_powder_sprite()
    materials = {
        caliber: {entry['item'].get('tag') for entry in
                  json.loads((TACZ_RECIPES / f'{caliber}.json').read_text(encoding='utf-8'))['materials']}
        for caliber in calibers
    }
    tool = tool_icon()
    write_asset('ammo_disassembly_tool', 'ammo_disassembly_tool', tool)
    tool_preview = Image.new('RGBA', (512, 512), '#20262D')
    tool_preview.alpha_composite(tool.resize((448, 448), Image.Resampling.NEAREST), (32, 32))
    tool_preview.save(PREVIEW.parent / 'disassembly_pliers_preview.png')
    powders = {}
    for caliber in calibers:
        powders[caliber] = powder_icon(caliber, vanilla, materials[caliber])
        write_asset(f'ammo_powder_{caliber}', f'ammo/powders/{caliber}', powders[caliber])
    preview(calibers, tool, powders)
    reference_preview()
    for image in [tool, *powders.values()]:
        assert image.mode == 'RGBA' and image.size == (64, 64)
        alpha = image.getchannel('A')
        assert alpha.getextrema() == (0, 255)
        assert set(alpha.getdata()) == {0, 255}, 'Unexpected antialiasing'
    assert len({image.tobytes() for image in powders.values()}) == 19
    for x in range(30, 35):
        for y in range(2, 20):
            assert tool.getpixel((x, y))[3] == 0, 'The pliers must have empty jaws'
    for caliber in calibers:
        subject_colors = set(powders[caliber].crop((0, 0, 64, RIBBON_Y)).getdata())
        assert ((66, 183, 193, 255) in subject_colors) == ('forge:gems/lapis' in materials[caliber])
        assert ((210, 165, 72, 255) in subject_colors) == ('forge:rods/blaze' in materials[caliber])
        ribbon = tacz_ribbon(caliber)
        assert ribbon.size == (64, 14)
        for image in (powders[caliber],):
            for y in range(14):
                for x in range(64):
                    if ribbon.getpixel((x, y))[3]:
                        assert image.getpixel((x, y + RIBBON_Y)) == ribbon.getpixel((x, y))
    for caliber in calibers:
        for name in (f'ammo_powder_{caliber}',):
            model = json.loads((MODELS / f'{name}.json').read_text(encoding='utf-8'))
            texture = model['textures']['layer0'].removeprefix('ammocraft:')
            assert (ASSETS / 'textures' / f'{texture}.png').is_file()
    print('PASS: 20 transparent 64x64 textures, 20 models, and 19 exact single-line TaCZ ribbons.')
    print('PASS: empty pliers jaws; powder additives match the actual TaCZ material recipes.')
    print(f'Preview: {PREVIEW}')


if __name__ == '__main__':
    main()
