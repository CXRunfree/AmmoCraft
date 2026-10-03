"""Verify designed ammo batches in a packaged JAR or source resources (--resources)."""
from collections import Counter
from contextlib import nullcontext
from fractions import Fraction
from math import lcm
from io import BytesIO
from pathlib import Path
import json
import re
import zipfile
import sys

from PIL import Image
from generate_molds import COUNTS, multi_slot, slot_core

ROOT = Path(__file__).resolve().parents[1]
version = re.search(r'^mod_version=(.+)$', (ROOT / 'gradle.properties').read_text(), re.M).group(1)
artifact = ROOT / f'build/libs/ammocraft-{version}.jar'
pack = ROOT / 'tools/reference/tacz'
# Intended batch values, independent of Java metadata and original TaCZ costs.
METALS = {
    '9mm': (2, 0, 0, 12), '45acp': (4, 0, 0, 12), '357mag': (3, 0, 0, 6),
    '50ae': (5, 0, 0, 6), '46x30': (3, 0, 0, 12), '57x28': (4, 0, 0, 12),
    '58x42': (4, 0, 0, 12), '68x51fury': (5, 0, 0, 12), '556x45': (4, 0, 0, 12),
    '762x25': (3, 0, 0, 12), '762x39': (5, 0, 0, 12), '762x54': (5, 0, 0, 12),
    '308': (6, 0, 0, 12), '30_06': (10, 0, 0, 12), '338': (9, 0, 0, 6),
    '50bmg': (28, 0, 0, 6), '12g': (10, 0, 0, 12), '40mm': (5, 2, 0, 3),
    'rpg_rocket': (30, 3, 0, 3),
}
# Gunpowder, lapis dust, blaze powder and output count for independent charge batches.
POWDERS = {
    '9mm': (1, 0, 0, 24), '45acp': (2, 0, 0, 30), '357mag': (3, 0, 0, 24),
    '50ae': (5, 3, 0, 24), '46x30': (1, 0, 0, 24), '57x28': (1, 3, 0, 24),
    '58x42': (2, 0, 0, 24), '68x51fury': (3, 0, 0, 24), '556x45': (2, 0, 0, 30),
    '762x25': (1, 0, 0, 24), '762x39': (2, 0, 0, 24), '762x54': (4, 0, 0, 30),
    '308': (4, 1, 0, 24), '30_06': (3, 0, 0, 12), '338': (5, 3, 0, 12),
    '50bmg': (10, 6, 1, 12), '12g': (4, 0, 0, 12), '40mm': (5, 0, 0, 3),
    'rpg_rocket': (12, 0, 0, 3),
}
assert set(METALS) == set(POWDERS) == {path.stem for path in (pack / 'data/tacz/index/ammo').glob('*.json')}


class SourceResources:
    def __init__(self):
        self.files = {}
        for root in (ROOT / 'src/main/resources',):
            for path in root.rglob('*'):
                if path.is_file() and '.cache' not in path.parts:
                    self.files[path.relative_to(root).as_posix()] = path

    def namelist(self):
        return list(self.files)

    def read(self, path):
        return self.files[path].read_bytes()

    def testzip(self):
        return None


def legacy(name):
    return (name in {'cartridge_primer', '40mm_slug', '40mm_casing',
                     'common_propellant', 'concentrated_propellant', 'lapis_additive'}
            or name.startswith(('shotgun_', 'powder_formula_')) or name.endswith(('_head', '_casing', '_transition'))
            or 'gunpowder_cartridge' in name or name.endswith('ammunition_gunpowder'))


source_mode = '--resources' in sys.argv
if source_mode:
    capacity_source = (ROOT / 'src/main/java/cn/crtlprototypestudios/ammocraft/recipe/CasingOutputAccess.java').read_text(encoding='utf-8')
    casing_capacity = int(re.search(r'MAX_CASINGS_PER_TYPE\s*=\s*(\d+)', capacity_source).group(1))
    assert casing_capacity == 60
    for caliber, (_, _, _, batch) in METALS.items():
        assert casing_capacity % batch == 0, (caliber, 'Casing batch must divide basin capacity')
        # The last fitting batch reaches the cap exactly; the next cannot fit.
        stored = 0
        while stored <= casing_capacity - batch:
            stored += batch
        assert stored == casing_capacity, caliber
    print('PASS: source casing capacity is 60; all 19 batches fill it without a remainder. No runtime test performed.')
with (nullcontext(SourceResources()) if source_mode else zipfile.ZipFile(artifact)) as jar:
    assert jar.testzip() is None
    names = set(jar.namelist())
    assert len(jar.namelist()) == len(names), 'Duplicate ZIP entries'
    assert not any('/prma/' in name or name.startswith('assets/prma/') or name.startswith('data/prma/') for name in names)

    def data(path):
        return json.loads(jar.read(path))

    recipes = {path[len('data/ammocraft/recipes/'):-5]: data(path) for path in names
               if path.startswith('data/ammocraft/recipes/') and path.endswith('.json')}
    assert len(recipes) == 98, 'Only the ammunition pipeline recipes belong in this mod'
    assert len([name for name in names if name.startswith('assets/ammocraft/models/item/') and name.endswith('.json')]) == 79
    assert len([name for name in names if name.startswith('assets/ammocraft/textures/item/') and name.endswith('.png')]) == 60
    blank = recipes['mechanical_crafting/blank_ammo_mold']
    assert blank['type'] == 'create:mechanical_crafting' and blank['pattern'] == ['OO', 'OO']
    assert blank['key'] == {'O': {'item': 'minecraft:obsidian'}}
    assert blank['result'] == {'item': 'ammocraft:blank_ammo_mold'}
    assert not any('/simple/' in path or '/ammo_components/' in path or 'cutting/ammo_blank' in path for path in recipes)
    for path, recipe in recipes.items():
        for identifier in re.findall(r'ammocraft:([a-z0-9_]+)', json.dumps(recipe)):
            assert not legacy(identifier), f'Obsolete item in {path}: {identifier}'
    for name in names:
        if name.startswith('assets/ammocraft/models/item/') and name.endswith('.json'):
            assert not legacy(Path(name).stem), f'Obsolete generated model: {name}'
    for removed in ('SimpleAmmo', 'SimpleCartridge', 'SimpleCartridgeBuilder', 'SimpleCartridgeRecipeBuilder',
                    'StandardCartridgeComponents', 'SequencedAmmoRecipeBuilder', 'SawAmmoMoldMixin', 'PowderFormulaItem'):
        assert not any(name.endswith('/' + removed + '.class') for name in names), removed

    def ingredients(recipe):
        return Counter(entry.get('item', entry.get('tag')) for entry in recipe['ingredients'])

    lapis_pressing = recipes['pressing/lapis_dust']
    assert lapis_pressing['type'] == 'create:pressing'
    assert ingredients(lapis_pressing) == Counter({'minecraft:lapis_lazuli': 1})
    assert lapis_pressing['results'] == [{'item': 'ammocraft:lapis_dust'}]
    assert data('assets/ammocraft/models/item/lapis_dust.json')['textures']['layer0'] == 'ammocraft:item/lapis_dust'
    with Image.open(BytesIO(jar.read('assets/ammocraft/textures/item/lapis_dust.png'))) as image:
        assert image.mode == 'RGBA' and image.size == (32, 32)
    for locale in ('zh_cn', 'en_us'):
        assert 'item.ammocraft.lapis_dust' in data('assets/ammocraft/lang/' + locale + '.json')
    assert not any('thermal:' in json.dumps(recipe) for recipe in recipes.values())
    for removed in ('common_propellant', 'concentrated_propellant', 'lapis_additive'):
        assert 'crafting/' + removed not in recipes
        assert not any(Path(name).stem == removed for name in names)
    for caliber, (copper, iron, nuggets, count) in METALS.items():
        half = 'ammocraft:incomplete_' + caliber
        casing = 'ammocraft:casing_' + caliber
        powder = 'ammocraft:ammo_powder_' + caliber
        mixing = recipes['mixing/ammo_blank/' + caliber]
        assert mixing['type'] == 'ammocraft:ammo_mixing'
        assert ingredients(mixing) == +Counter({'minecraft:copper_ingot': copper,
                                               'minecraft:iron_ingot': iron, 'minecraft:iron_nugget': nuggets})
        assert mixing['results'] == [{'item': casing, **({'count': count} if count > 1 else {})}]
        if caliber in ('9mm', '45acp', '46x30', '762x25'):
            metal_time, powder_time = 64, 96
        elif caliber in ('357mag', '57x28', '58x42', '68x51fury', '556x45', '762x39'):
            metal_time, powder_time = 96, 128
        elif caliber in ('338', '40mm'):
            metal_time, powder_time = 192, 192
        elif caliber in ('50bmg', 'rpg_rocket'):
            metal_time, powder_time = 256, 256
        else:
            metal_time, powder_time = 128, 128
        assert mixing['processingTime'] == metal_time
        assert len(mixing['ingredients']) <= 160
        stack_text = (pack / f'data/tacz/index/ammo/{caliber}.json').read_text()
        stack_size = int(re.search(r'"stack_size"\s*:\s*(\d+)', stack_text).group(1))
        assert (count == 3 if caliber in ('40mm', 'rpg_rocket') else count % 6 == 0)
        assert 1 <= count <= 64 and stack_size % count == 0
        engraving = recipes['deploying/ammo_mold/' + caliber]
        assert engraving['keepHeldItem'] and engraving['ingredients'][0] == {'item': 'ammocraft:blank_ammo_mold'}
        assert engraving['ingredients'][1]['type'] == 'forge:partial_nbt'
        assert engraving['ingredients'][1]['nbt'] == '{AmmoId:"tacz:' + caliber + '"}'
        dismantle = recipes['deploying/ammo_disassembly/' + caliber]
        assert dismantle['keepHeldItem'] and dismantle['ingredients'][0] == engraving['ingredients'][1]
        assert dismantle['ingredients'][1] == {'item': 'ammocraft:ammo_disassembly_tool'}
        assert dismantle['results'] == [{'item': powder}]
        assert 'deploying/powder_formula/' + caliber not in recipes
        assert not any('powder_formula_' + caliber in name or 'ammo/formulas/' + caliber in name for name in names)

        assert 'crafting/ammo_powder/' + caliber not in recipes
        propellant = recipes['mixing/ammo_powder/' + caliber]
        assert propellant['type'] == 'ammocraft:ammo_mixing' and propellant['processingTime'] == powder_time
        assert len(propellant['ingredients']) <= 160 and ingredients(propellant)[powder] == 0
        assert all(result['item'] == powder and 1 <= result.get('count', 1) <= 64
                   for result in propellant['results'])
        output_count = sum(result.get('count', 1) for result in propellant['results'])
        assert 1 <= count <= 12 and 1 <= output_count <= 30
        assert count < stack_size and output_count < stack_size, f'Batch must be smaller than a stack: {caliber}'
        assert lcm(count, output_count) % 6 == 0 or caliber in ('40mm', 'rpg_rocket')
        assert (stack_size * 2) % lcm(count, output_count) == 0
        charges = ingredients(propellant)
        expected_powder, expected_lapis, expected_blaze, expected_output = POWDERS[caliber]
        assert output_count == expected_output
        assert charges == +Counter({'minecraft:gunpowder': expected_powder,
                                    'ammocraft:lapis_dust': expected_lapis,
                                    'minecraft:blaze_powder': expected_blaze})
        original = json.loads((pack / f'data/tacz/recipes/ammo/{caliber}.json').read_text())
        reference = {entry['item']['tag']: Fraction(entry.get('count', 1), original['result']['count'])
                     for entry in original['materials']}
        costs = {'forge:ingots/copper': copper, 'forge:ingots/iron': iron,
                 'forge:nuggets/iron': count if caliber == '12g' else nuggets,
                 'forge:gunpowder': expected_powder, 'forge:gems/lapis': expected_lapis,
                 'forge:rods/blaze': Fraction(expected_blaze, 2)}
        for tag, amount in costs.items():
            output = output_count if tag in ('forge:gunpowder', 'forge:gems/lapis', 'forge:rods/blaze') else count
            baseline = reference.get(tag, 0)
            if baseline:
                bound = Fraction(3, 2) if caliber == '308' and tag == 'forge:gems/lapis' else Fraction(1, 3)
                assert abs(Fraction(amount, output) / baseline - 1) <= bound, (caliber, tag)
                if caliber == 'rpg_rocket':
                    assert Fraction(amount, output) == baseline
            else:
                assert amount == 0, (caliber, tag)

        assembly = recipes['sequenced_assembly/ammo/' + caliber]
        assert assembly['ingredient'] == {'item': casing}
        assert assembly['transitionalItem'] == {'item': half}
        assert assembly['loops'] == 1
        step_types = ['create:deploying', 'create:deploying', 'create:pressing'] if caliber == '12g' else ['create:deploying', 'create:pressing']
        assert [step['type'] for step in assembly['sequence']] == step_types
        assert assembly['sequence'][0]['ingredients'] == [{'item': half}, {'item': powder}]
        assert not assembly['sequence'][0].get('keepHeldItem', False)
        if caliber == '12g':
            assert assembly['sequence'][1]['ingredients'] == [{'item': half}, {'item': 'minecraft:iron_nugget'}]
            assert not assembly['sequence'][1].get('keepHeldItem', False)
        assert assembly['results'] == [{'item': 'tacz:ammo', 'nbt': {'AmmoId': 'tacz:' + caliber}}]
        for prefix, texture in [('ammo_mold_', 'ammo/molds/' + caliber), ('incomplete_', 'ammo/casings/' + caliber),
                                 ('casing_', 'ammo/casings/' + caliber),
                                 ('ammo_powder_', 'ammo/powders/' + caliber)]:
            assert data(f'assets/ammocraft/models/item/{prefix}{caliber}.json')['textures']['layer0'] == 'ammocraft:item/' + texture
            with Image.open(BytesIO(jar.read('assets/ammocraft/textures/item/' + texture + '.png'))) as image:
                assert image.mode == 'RGBA'
                if prefix == 'ammo_mold_':
                    assert image.size == (64, 64)
                    assert image.crop((8, 8, 56, 56)).getchannel('A').getextrema() == (0, 255)
            for locale in ('zh_cn', 'en_us'):
                assert 'item.ammocraft.' + prefix + caliber in data('assets/ammocraft/lang/' + locale + '.json')
        mask = multi_slot(caliber, COUNTS[caliber])
        core = slot_core(mask)
        with Image.open(BytesIO(jar.read(f'assets/ammocraft/textures/item/ammo/casings/{caliber}.png'))) as casing:
            assert casing.size == (64, 64) and casing.getchannel('A').tobytes() == mask.tobytes()
        with Image.open(BytesIO(jar.read(f'assets/ammocraft/textures/item/ammo/molds/{caliber}.png'))) as mold:
            for y in range(8, 56):
                for x in range(8, 56):
                    pixel = mold.getpixel((x, y))
                    assert bool(core.getpixel((x, y))) == (pixel[3] == 0), caliber
                    if mask.getpixel((x, y)) and not core.getpixel((x, y)):
                        assert pixel in ((98, 98, 98, 255), (153, 153, 153, 255)), caliber

    assert 'BasinAmmoMoldMixin' in data('ammocraft.mixins.json')['mixins']
    assert set(data('ammocraft.mixins.json')['mixins']) == {
        'BasinAmmoMoldMixin', 'BasinCasingOutputMixin', 'DeployerAmmoParticlesMixin', 'DeployerFakePlayerAccessor'}
    if not source_mode:
        assert list((ROOT / 'build/libs').glob('*.jar')) == [artifact], 'Build must produce only one distributable JAR'
        metadata = jar.read('META-INF/mods.toml').decode('utf-8')
        assert 'modId="ammocraft"' in metadata and f'version="{version}"' in metadata and 'displayName="AmmoCraft"' in metadata
        assert not any(name.startswith('tools/') or name.startswith('assets/tacz/') or '/textures/block/' in name for name in names)
        for name in names:
            if name.startswith('assets/ammocraft/textures/item/') and name.endswith('.png'):
                assert jar.read(name) == (ROOT / 'src/main/resources' / name).read_bytes(), f'Stale texture in JAR: {name}'
        assert 'ammocraft.refmap.json' in names
        assert 'MixinConfigs: ammocraft.mixins.json' in jar.read('META-INF/MANIFEST.MF').decode()
        assert not any(path.startswith('META-INF/jarjar/') or path.endswith('.jar')
                       or path.startswith('com/tterrag/registrate/') for path in names), 'Registrate must be supplied by Create'
    assert not any('/test/' in path or path.startswith('.cache/') or '/structures/empty.nbt' in path for path in names)
    print('PASS: all 19 calibers; no formula/charge ingredients; 12g iron-nugget assembly step.')
    print('PASS: independent small batches; tiered processing times; RPG original costs; raw powder mixing.')
    print('PASS: current casing artwork, matching mold footprint and overlapping inset bevels.')
    if source_mode:
        print('PASS: source recipes, textures, languages and Mixin configuration. No build performed.')
    else:
        print('PASS: textures, languages, Mixin and ZIP integrity; Registrate supplied by Create, not bundled.')
        print(f'Artifact: {artifact} ({artifact.stat().st_size} bytes)')
