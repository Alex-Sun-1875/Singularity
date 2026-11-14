"""Prepare six local Qwen concept plates; reuse the approved captain as style reference."""
from pathlib import Path
import json
from PIL import Image

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / 'source-art/encounters/qwen-world-v1'
ROOT.mkdir(parents=True, exist_ok=True)
reference = PROJECT / 'assets/concepts/captain-detail-reference-v2.png'
with Image.open(reference) as im:
    im.thumbnail((512, 512))
    im.convert('RGB').save(ROOT / 'style-reference-preview.jpg', quality=85)

plates = [
    ('r1-stonebridge', 'R1 / STONEBRIDGE',
     'LEFT: Greycloak Captain, mature human commander, weathered grey cloak, heavy steel armour, battered round shield and long war hammer. RIGHT: Pit Warden, lean human quarry overseer, rope harness, rough leather, short pickaxe and small lantern.',
     'a human grey-cloaked swordsman with a plain longsword; a crouched human crossbow scout; a broad human shield guard with a rectangular wooden shield',
     'Oath Unquenched, a realistic very long narrow silver-steel sword, ruby oath nail, crimson grip, blade four times grip length; Silver Stag bow, visible dark wood core, silver antler braces and emerald; veteran leather gauntlets with reinforced steel knuckles'),
    ('r2-sunken-highlands', 'R2 / SUNKEN HIGHLANDS',
     'LEFT: Bridge Warden, human armoured sentinel, dented half plate, arch-shaped hammer crown, tall steel shield, mine dust. RIGHT: Windcut Watcher, human highland ranger, layered slate green leather, hooked longbow, wind ribbons, no wings.',
     'a human quarry pick guard; a human ridge crossbowman with goggles; a small four-legged abandoned bronze mining automaton, clearly mechanical not animal',
     'Last One on the Bridge, a practical long-handled one-handed hammer with an arched head; Survivors Chainmail, silver chain with white branch clasp; Winter Hunt, layered wood recurved bow with clear angular ice crystal grip'),
    ('r3-bell-river', 'R3 / BELL RIVER',
     'LEFT: Ash Reaver, human dock mercenary with a strapped oil flask, dark leather apron, long cleaver and fireproof gloves, no flaming body. RIGHT: Wreck Diver, human salvage captain with weathered teal coat, boat hook, rope belt and old brass diving helmet carried at hip.',
     'a human dock knifeman; a human oil thrower lifting a clay pot; a bronze bell archive guardian with hinged stone feet, no ghost',
     'Storm Approaches, a dark wood bow with forked copper string fitting and restrained lightning; Sunset Afterglow, amber pendant within a silver sun cage; Ash Prayer, a long wooden staff topped with a closed lantern cage and ruby'),
    ('r4-greyrock', 'R4 / GREYROCK',
     'LEFT: Adrian Voss, original mature human fortress commander, dark engraved half plate, navy cloak, broad shield with twin-ring fortress seal, straight long sword, no crown. RIGHT: Ironthorn Warden, human maintenance gaoler, segmented work plate, iron thorn pauldron, key belt, compact pole hammer.',
     'a human city shield soldier with cream grey tabard; a human heavy crossbow guard; a human mirror technician carrying a folded silver optical frame',
     'Oath of the Uncrowned, long blue-steel straight sword with double silver ring guard and sapphire; Twin Covenant, two interlocked silver pendants with violet crystals; Rift of Heaven, black wood staff and broken open silver star ring with suspended blue gemstone'),
    ('u1-oath-underworld', 'U1 / OATH UNDERWORLD',
     'LEFT: Echo Anvil, ancient heavy bronze forge automaton with broad hammer arms, exposed mechanical knee joints, a modest white-hot furnace slot, not lava giant. RIGHT: Gate Sword Array, three articulated ancient sword-bearing armour statues on one circular plinth, white branch engravings and visible mechanical joints.',
     'a bronze articulated forge guard with short hammer; a small six-legged resonance beetle made of scrap metal; a human prison guard with dull lantern and pole hook',
     'Brass Star Ring, a floating copper core inside a closed silver cage held as an offhand focus; Expedition Bracers, leather and steel with measured engravings; Bell Elegy, long dark wood staff topped by an inverted bell shaped clear crystal'),
    ('u2-bell-catacombs', 'U2 / BELL CATACOMBS',
     'LEFT: Sluice Watch, tall nonhuman ancient bronze maintenance automaton, wheel-shaped shield and blunt stone counterweight arm, dry stone base. RIGHT: Palimpsest Keeper, ancient bronze tripod archive automaton, two shuttered silver optical mirrors, stone inscription scroll plates, no human scholar face.',
     'a small jointed stone and bronze canal crawler; a humanoid bronze inscription sentinel; a tiny hovering three-ring optical construct with a visible physical lens, no ghost',
     'Quiet Thought, elegant openwork silver ring and violet gemstone; Silent Ritual, navy cloth boots with precise silver seam lines; Expedition Boots, practical dark leather boots with articulated ankle braces'),
]
jobs=[]
for index, (key, title, bosses, monsters, gear) in enumerate(plates):
    prompt = f'''Create an ORIGINAL western fantasy game production concept plate for {title}.
The input image is ONLY a rendering, material and adult-proportion reference. Do not copy its layout or repeat its character. Rich painterly realistic game illustration, clear readable silhouettes, natural steel, cloth, leather, bronze and gemstone materials. Natural warm neutral studio light, restrained magical highlights, no cartoon, no chibi, no modern firearms, no copied franchise characters.
Square 1024 by 1024 plate, warm light grey parchment background, clear separated objects, generous gutters. EXACT layout: TOP HALF contains TWO large full-body enemy leaders, standing three-quarter front, feet and complete weapons visible: {bosses}
MIDDLE horizontal strip contains THREE smaller distinct full-body common enemy designs, evenly spaced: {monsters}.
BOTTOM horizontal strip contains THREE large standalone equipment objects, evenly spaced, no hands or people: {gear}.
Keep each object isolated from neighbours. No environment, no scenery, no UI, no decorative borders, no writing, no labels, no logos, no numbers. The equipment must be complete and not cropped. Weapons are believable adult-sized equipment. These are DESIGN REFERENCES, not animation frames. Use all three rows and show all eight objects.'''
    jobs.append({'id':key,'region':title.split(' / ')[0], 'seed':2026110800+index,
                 'reference':reference.relative_to(PROJECT).as_posix(),'prompt':prompt})
(ROOT / 'art-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Prepared {len(jobs)} local Qwen jobs at {ROOT}')
