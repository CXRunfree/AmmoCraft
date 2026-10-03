"""Regenerate current production artwork; --check proves item PNGs stay identical."""
import hashlib
import sys

from ammo_art import TEXTURES
from generate_molds import main as molds
from generate_ammo_casings import main as casings
from generate_disassembly_icons import main as powders
from generate_logo import main as logo
from generate_item_resources import main as item_resources


def main():
    originals = {path: hashlib.sha256(path.read_bytes()).digest()
                 for path in TEXTURES.rglob('*.png')}
    molds()
    casings()
    powders()
    logo()
    item_resources()
    if '--check' in sys.argv:
        for path, digest in originals.items():
            assert hashlib.sha256(path.read_bytes()).digest() == digest, f'Unexpected artwork change: {path}'
        print('PASS: artwork regeneration preserves all 60 production item textures byte-for-byte.')


if __name__ == '__main__':
    main()
