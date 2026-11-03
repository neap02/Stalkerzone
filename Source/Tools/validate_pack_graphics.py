"""Verify the generic directional PNGs that Belt/renderUtilityAsPack requires.

Run from a built StalkerZone mod directory:
    python Source/Tools/validate_pack_graphics.py

No RimWorld libraries, numpy, or Pillow are required.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

mod_root = Path(__file__).resolve().parents[2]
xml_file = mod_root / 'Common/Defs/Gear/SZ_Packs.xml'
textures_root = mod_root / 'Common/Textures'
root = ET.parse(xml_file).getroot()
paths = sorted({(el.text or '').strip() for el in root.findall('.//wornGraphicPath')
                if el.text and '/SZ_Packs/' in el.text})
missing = []
for path in paths:
    for direction in ('south', 'east', 'north'):
        candidate = textures_root / (path + '_' + direction + '.png')
        if not candidate.is_file():
            missing.append(str(candidate.relative_to(mod_root)))
if len(paths) != 10:
    print('Expected 10 pack paths; found', len(paths), file=sys.stderr)
    sys.exit(2)
if missing:
    print('Missing generic pack textures:\n' + '\n'.join(missing),file=sys.stderr)
    sys.exit(1)
print(f'OK: {len(paths)} packs x 3 directions = {len(paths)*3} generic sprites')
