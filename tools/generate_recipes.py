"""Generate all 98 AmmoCraft recipes from AmmoItems; --check verifies existing JSON."""
import json
import re
import sys

from ammo_art import ROOT


def item(identifier):
    return {'item': identifier}


def result(identifier, count=1):
    return {'item': identifier, **({'count': count} if count > 1 else {})}


def processing_time(ammo):
    if ammo in ('9mm', '45acp', '46x30', '762x25'):
        return 64, 96
    if ammo in ('357mag', '57x28', '58x42', '68x51fury', '556x45', '762x39'):
        return 96, 128
    if ammo in ('338', '40mm'):
        return 192, 192
    if ammo in ('50bmg', 'rpg_rocket'):
        return 256, 256
    return 128, 128


def recipes():
    registry = (ROOT / 'src/main/java/cn/crtlprototypestudios/ammocraft/registry/AmmoItems.java').read_text(encoding='utf-8')
    entries = re.findall(r'new Caliber\("([^"]+)", "[^"]+", (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+)\)', registry)
    assert len(entries) == 19
    output = {
        'mechanical_crafting/blank_ammo_mold': {
            'type': 'create:mechanical_crafting', 'pattern': ['OO', 'OO'],
            'key': {'O': item('minecraft:obsidian')},
            'result': item('ammocraft:blank_ammo_mold'), 'acceptMirrored': True,
        },
        'crafting/ammo_disassembly_tool': {
            'type': 'minecraft:crafting_shaped', 'pattern': ['I I', ' A ', 'S S'],
            'key': {'I': item('create:iron_sheet'), 'A': item('create:andesite_alloy'), 'S': item('minecraft:stick')},
            'result': item('ammocraft:ammo_disassembly_tool'),
        },
        'pressing/lapis_dust': {
            'type': 'create:pressing', 'ingredients': [item('minecraft:lapis_lazuli')],
            'results': [item('ammocraft:lapis_dust')],
        },
    }
    for ammo, *values in entries:
        copper, iron, nuggets, blanks, gunpowder, lapis, blaze, doses = map(int, values)
        half = item('ammocraft:incomplete_' + ammo)
        casing = item('ammocraft:casing_' + ammo)
        powder = item('ammocraft:ammo_powder_' + ammo)
        sample = {'type': 'forge:partial_nbt', 'item': 'tacz:ammo', 'nbt': '{AmmoId:"tacz:' + ammo + '"}'}
        metal_time, powder_time = processing_time(ammo)
        output['mixing/ammo_blank/' + ammo] = {
            'type': 'ammocraft:ammo_mixing',
            'ingredients': [item('minecraft:copper_ingot')] * copper + [item('minecraft:iron_ingot')] * iron
                           + [item('minecraft:iron_nugget')] * nuggets,
            'results': [result(casing['item'], blanks)], 'processingTime': metal_time,
        }
        output['mixing/ammo_powder/' + ammo] = {
            'type': 'ammocraft:ammo_mixing',
            'ingredients': [item('minecraft:gunpowder')] * gunpowder + [item('ammocraft:lapis_dust')] * lapis
                           + [item('minecraft:blaze_powder')] * blaze,
            'results': [result(powder['item'], doses)], 'processingTime': powder_time,
        }
        output['deploying/ammo_mold/' + ammo] = {
            'type': 'create:deploying', 'ingredients': [item('ammocraft:blank_ammo_mold'), sample],
            'results': [item('ammocraft:ammo_mold_' + ammo)], 'keepHeldItem': True,
        }
        output['deploying/ammo_disassembly/' + ammo] = {
            'type': 'create:deploying', 'ingredients': [sample, item('ammocraft:ammo_disassembly_tool')],
            'results': [powder], 'keepHeldItem': True,
        }
        sequence = [{'type': 'create:deploying', 'ingredients': [half, powder], 'results': [half]}]
        if ammo == '12g':
            sequence.append({'type': 'create:deploying', 'ingredients': [half, item('minecraft:iron_nugget')], 'results': [half]})
        sequence.append({'type': 'create:pressing', 'ingredients': [half], 'results': [half]})
        output['sequenced_assembly/ammo/' + ammo] = {
            'type': 'create:sequenced_assembly', 'ingredient': casing, 'transitionalItem': half,
            'sequence': sequence, 'results': [{'item': 'tacz:ammo', 'nbt': {'AmmoId': 'tacz:' + ammo}}], 'loops': 1,
        }
    return output


def main():
    output = ROOT / 'src/main/resources/data/ammocraft/recipes'
    check = '--check' in sys.argv
    for identifier, data in recipes().items():
        path = output / (identifier + '.json')
        if check:
            assert json.loads(path.read_text(encoding='utf-8')) == data, identifier
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: 98 recipes {"verified" if check else "generated"}; batches, NBT and 12g assembly preserved.')


if __name__ == '__main__':
    main()
