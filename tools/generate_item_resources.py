"""Maintain models, casing translations and the belt tag for registered ammo items."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
registry = ROOT / 'src/main/java/cn/crtlprototypestudios/ammocraft/registry/AmmoItems.java'
CALIBERS = re.findall(r'new Caliber\("([^"]+)"', registry.read_text(encoding='utf-8'))
assert len(CALIBERS) == 19 and len(set(CALIBERS)) == 19


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    resources = ROOT / 'src/main/resources'
    assets = resources / 'assets/ammocraft'
    for locale in ('en_us', 'zh_cn'):
        path = assets / f'lang/{locale}.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        for ammo in CALIBERS:
            name = data['item.ammocraft.ammo_powder_' + ammo]
            name = name.removesuffix(' Propellant').removesuffix('火药')
            data['item.ammocraft.casing_' + ammo] = name + (' Casing' if locale == 'en_us' else '弹壳')
            write(assets / f'models/item/casing_{ammo}.json', {
                'parent': 'minecraft:item/generated',
                'textures': {'layer0': f'ammocraft:item/ammo/casings/{ammo}'},
            })
        data['tooltip.ammocraft.ammo_mold'] = (
            'Set in the basin filter to mix copper/iron into this caliber casing. The mold is not consumed.'
            if locale == 'en_us' else '设置在工作盆过滤槽，动力搅拌器用铜/铁制作对应弹壳。模板不消耗。')
        write(path, data)
    write(resources / 'data/create/tags/items/upright_on_belt.json', {
        'replace': False,
        'values': ['ammocraft:' + prefix + ammo for prefix in ('casing_', 'incomplete_') for ammo in CALIBERS],
    })
    print('PASS: 19 independent casing models, translations and belt tags generated.')


if __name__ == '__main__':
    main()
