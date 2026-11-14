"""Fetch pinned, licensed glyphs over the verified physical WLAN route."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
COMMIT = '82d948812bfe3f269ef8f731dcdb07b08160edc4'
GLYPHS = {
 'WAR_01':'lorc/sword-spin', 'WAR_02':'lorc/piercing-sword',
 'WAR_03':'lorc/bordered-shield', 'WAR_04':'lorc/earth-crack', 'WAR_05':'lorc/sword-array',
 'BOW_01':'lorc/supersonic-arrow', 'BOW_02':'lorc/return-arrow',
 'BOW_03':'lorc/arrow-flights', 'BOW_04':'lorc/crosshair-arrow', 'BOW_05':'lorc/arrow-cluster',
 'FIR_01':'lorc/fireball', 'FIR_02':'lorc/burning-meteor', 'FIR_03':'lorc/fire-shield',
 'FIR_04':'lorc/flaming-sheet', 'FIR_05':'lorc/fire-wave',
 'THU_01':'lorc/focused-lightning', 'THU_02':'lorc/lightning-tree',
 'THU_03':'lorc/thunder-blade', 'THU_04':'lorc/lightning-trio', 'THU_05':'lorc/lightning-storm',
 'COM_01':'lorc/dodging', 'COM_02':'delapouite/healing',
 'WAR_P1':'lorc/crossed-swords', 'WAR_P2':'lorc/heart-inside',
 'BOW_P1':'delapouite/hunter-eyes', 'BOW_P2':'lorc/winged-arrow',
 'FIR_P1':'lorc/burning-embers', 'FIR_P2':'lorc/flame-spin',
 'THU_P1':'lorc/lightning-helix', 'THU_P2':'lorc/lightning-shield',
}

def fetch(entry):
 skill, glyph = entry
 target = ROOT / 'originals' / (skill.lower() + '.svg')
 if skill in ('COM_01','WAR_01'):
  data = (ROOT.parent / 'game-icons' / ('dash.svg' if skill == 'COM_01' else 'skill.svg')).read_bytes()
 elif target.exists() and cached.get(skill,{}).get('path') == glyph+'.svg' and hashlib.sha256(target.read_bytes()).hexdigest() == cached[skill]['sha256']:
  data = target.read_bytes()
 else:
  url = f'https://api.github.com/repos/game-icons/icons/contents/{glyph}.svg?ref={COMMIT}'
  response = subprocess.run(['curl.exe','--fail','--silent','--show-error','--compressed',
   '--noproxy','*','--interface','192.168.1.14','--resolve','api.github.com:443:20.205.243.168',
   '--connect-timeout','10','--max-time','30','-H','Accept: application/vnd.github.raw+json',url],
   check=True, capture_output=True)
  data = response.stdout
 if b'<svg' not in data:
  raise ValueError(f'Not SVG: {skill}')
 target.write_bytes(data)
 return dict(id=skill, path=glyph+'.svg', author=glyph.split('/')[0],
  url=f'https://raw.githubusercontent.com/game-icons/icons/{COMMIT}/{glyph}.svg',
  sha256=hashlib.sha256(data).hexdigest(), source=target.relative_to(PROJECT).as_posix())

if __name__ == '__main__':
 (ROOT/'originals').mkdir(parents=True, exist_ok=True)
 cached={i['id']:i for i in json.loads((ROOT/'sources.json').read_text(encoding='utf8'))['assets']} if (ROOT/'sources.json').exists() else {}
 tree = {i['path'] for i in json.loads((PROJECT/'temp/game-icons-tree.json').read_text())['tree']}
 assert all(p+'.svg' in tree for p in GLYPHS.values())
 with ThreadPoolExecutor(max_workers=4) as pool:
  assets = list(pool.map(fetch, GLYPHS.items()))
 record = dict(repository='https://github.com/game-icons/icons', commit=COMMIT, license='CC-BY-3.0',
  date='2026-11-10', downloadRoute='Physical WLAN 192.168.1.14; proxy explicitly disabled; API DNS resolved via LAN gateway; TLS host verified; direct remote 20.205.243.168. COM_01 and WAR_01 reuse existing pinned sources.',
  construction='Distinct licensed SVG silhouettes; existing deterministic metal relief; no new dependency or generative model.', assets=assets,
  artReview=dict(export='Pending', isolated='Pending', runtime='Pending', userAcceptance='Not recorded'))
 (ROOT/'sources.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(f'Fetched {len(assets)} pinned per-skill glyphs.')
