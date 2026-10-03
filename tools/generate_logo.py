"""Draw the crossed Create-style wrench / cartridge logo concept with Pillow."""
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools/previews'
SIZE = 512
SCALE = 3


def layer():
    return Image.new('RGBA', (SIZE * SCALE, SIZE * SCALE))


def polygon(image, points, fill, outline=None, width=1):
    points = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
    draw = ImageDraw.Draw(image)
    draw.polygon(points, fill=fill)
    if outline:
        draw.line(points + [points[0]], fill=outline, width=width * SCALE,
                  joint='curve')


def ellipse(image, box, fill, outline=None, width=1):
    ImageDraw.Draw(image).ellipse(tuple(round(v * SCALE) for v in box),
                                 fill=fill, outline=outline, width=width * SCALE)


def line(image, points, fill, width=1):
    ImageDraw.Draw(image).line([(round(x * SCALE), round(y * SCALE))
                               for x, y in points], fill=fill, width=width * SCALE,
                              joint='curve')


def gradient_shape(image, points, top, bottom, outline, width=3):
    mask = Image.new('L', image.size)
    polygon(mask, points, 255)
    colors = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(colors)
    ymin = min(y for _, y in points) * SCALE
    ymax = max(y for _, y in points) * SCALE
    for y in range(int(ymin), int(ymax) + 1):
        t = (y - ymin) / max(1, ymax - ymin)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,)
        draw.line((0, y, image.width, y), fill=color)
    image.paste(colors, (0, 0), mask)
    polygon(image, points, None, outline, width)


def gear():
    image = layer()
    points = []
    for tooth in range(12):
        for phase, radius in ((-.5, 207), (-.30, 207), (-.24, 237),
                              (.24, 237), (.30, 207), (.5, 207)):
            angle = (tooth + phase) * math.tau / 12 - math.pi / 2
            points.append((256 + math.cos(angle) * radius,
                           256 + math.sin(angle) * radius))
    gradient_shape(image, points, (247, 204, 107), (139, 85, 30), '#242328', 5)
    # A continuous bevel keeps the gold ring readable at inventory-icon size.
    line(image, points + [points[0]], '#f2c66c', 2)
    ellipse(image, (60, 60, 452, 452), None, '#8f5b29', 3)
    ellipse(image, (75, 75, 437, 437), '#25282d', '#ffe0a0', 3)
    ellipse(image, (87, 87, 425, 425), (0, 0, 0, 0), '#835325', 3)
    for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
        x, y = 256 + 191 * math.cos(angle), 256 + 191 * math.sin(angle)
        ellipse(image, (x - 5, y - 5, x + 5, y + 5), '#543f2c', '#ffe0a0', 1)
        line(image, [(x - 2, y), (x + 2, y)], '#ceb079', 1)
    return image


def cartridge():
    image = layer()
    # A pointed projectile, necked brass case and distinct extractor rim.
    gradient_shape(image, [(256, 51), (244, 68), (236, 91), (234, 126),
                           (278, 126), (276, 91), (268, 68)],
                   (244, 168, 105), (156, 75, 40), '#20252c', 5)
    line(image, [(252, 64), (245, 88), (244, 116)], '#ffe0b1', 4)
    gradient_shape(image, [(233, 123), (279, 123), (279, 163),
                           (288, 184), (288, 409), (224, 409),
                           (224, 184), (233, 163)],
                   (239, 199, 103), (153, 103, 43), '#20252c', 5)
    line(image, [(240, 131), (240, 163), (232, 187), (232, 398)], '#ffe5a1', 5)
    line(image, [(276, 186), (276, 400)], '#78502b', 5)
    line(image, [(228, 189), (283, 189)], '#bb8b43', 2)
    polygon(image, [(225, 405), (287, 405), (287, 420), (225, 420)],
            '#725333', '#20252c', 4)
    gradient_shape(image, [(220, 420), (292, 420), (292, 434),
                           (288, 439), (224, 439), (220, 434)],
                   (248, 213, 131), (154, 109, 49), '#20252c', 4)
    line(image, [(225, 424), (287, 424)], '#ffe8b0', 3)
    return image.rotate(43, Image.Resampling.BICUBIC)


def wrench():
    image = layer()
    # Chunky open jaws, a reinforced shank, orange grip and riveted collar.
    gradient_shape(image, [(241, 153), (271, 153), (273, 279),
                           (278, 296), (278, 419), (270, 438),
                           (242, 438), (234, 419), (234, 296), (239, 279)],
                   (155, 175, 176), (67, 86, 91), '#20252c', 6)
    gradient_shape(image, [(235, 280), (277, 280), (281, 299),
                           (281, 410), (272, 432), (240, 432),
                           (231, 410), (231, 299)],
                   (218, 151, 66), (142, 80, 35), '#20252c', 5)
    line(image, [(240, 300), (240, 404), (247, 422)], '#f1c57a', 4)
    for y in (319, 342, 365, 388):
        line(image, [(247, y), (273, y)], '#70482e', 4)
        line(image, [(247, y + 4), (273, y + 4)], '#d7a566', 2)
    polygon(image, [(229, 270), (283, 270), (283, 296), (229, 296)],
            '#45595d', '#20252c', 4)
    line(image, [(234, 275), (278, 275)], '#adc6c0', 3)
    ellipse(image, (250, 277, 262, 289), '#d8c28a', '#263139', 2)
    line(image, [(253, 283), (259, 283)], '#596267', 2)
    # The open mouth faces upward; its hexagonal recess reads as a real wrench.
    jaw = [(221, 59), (220, 98), (235, 116), (277, 116),
           (292, 98), (291, 59), (315, 78), (326, 113),
           (315, 150), (283, 175), (229, 175), (197, 150),
           (186, 113), (197, 78)]
    gradient_shape(image, jaw, (212, 225, 216), (88, 111, 114), '#20252c', 6)
    line(image, [(202, 85), (194, 112), (205, 144), (233, 165)], '#ecf1d8', 4)
    line(image, [(222, 99), (235, 120), (277, 120), (291, 102)], '#405559', 5)
    line(image, [(303, 85), (313, 113), (303, 142)], '#7c9695', 4)
    polygon(image, [(240, 141), (248, 133), (264, 133),
                    (272, 141), (272, 152), (264, 160),
                    (248, 160), (240, 152)], '#d7bd7b', '#34464b', 3)
    line(image, [(249, 147), (263, 147)], '#66716b', 3)
    return image.rotate(-43, Image.Resampling.BICUBIC)


def composite_shadow(canvas, item, offset=(0, 4), opacity=150):
    shadow = layer()
    alpha = item.getchannel('A').point(lambda a: a * opacity // 255)
    shadow.paste((10, 14, 20, 255), (offset[0] * SCALE, offset[1] * SCALE), alpha)
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(2 * SCALE)))
    canvas.alpha_composite(item)


def main():
    image = gear()
    composite_shadow(image, cartridge())
    composite_shadow(image, wrench(), (0, 3), 190)
    image = image.resize((512, 512), Image.Resampling.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / 'logo_wrench_cartridge.png')
    image.save(ROOT / 'src/main/resources/ammocraft.png')
    image.resize((128, 128), Image.Resampling.LANCZOS).save(
        OUT / 'logo_wrench_cartridge_128.png')
    preview = Image.new('RGBA', (1024, 1024), '#20262d')
    preview.alpha_composite(image.resize((896, 896), Image.Resampling.LANCZOS), (64, 64))
    preview.convert('RGB').save(OUT / 'logo_wrench_cartridge_preview.png')
    print(f'Logo concept saved to {OUT}: transparent 512px, 128px and dark preview.')


if __name__ == '__main__':
    main()
