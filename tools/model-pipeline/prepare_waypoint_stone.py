"""Prepare a generated original rune decal and its separate, restrained glow."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'source-art/maps/waypoints-stone-v4'
RUNTIME = ROOT / 'src/cocos/assets/resources/flat2d/waypoints-v1'
SOURCE = Path(r'C:/Users/Alexa/.codex/generated_images/01a1b873-5272-72a3-a18c-03223c658990/exec-31a26be0-dc64-4ccf-97a7-5b7991652c9a.png')

def main():
    ART.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, ART / 'waystone-rune-generated.png')
    original = Image.open(SOURCE).convert('RGBA')
    core = original.resize((512, 768), Image.Resampling.LANCZOS)
    core.save(RUNTIME / 'waystone-rune-v4.png')
    # A cramped doorway uses only the same primary seal as a square floor inlay.
    floor = original.crop((0, 512, 1024, 1536)).resize((512, 512), Image.Resampling.LANCZOS)
    floor_pixels = np.array(floor)
    yy, xx = np.mgrid[:512, :512]
    edge = np.minimum(np.minimum(xx, 511-xx), np.minimum(yy, 511-yy))
    floor_pixels[:,:,3] = (floor_pixels[:,:,3] * np.clip(edge / 18., 0, 1)).astype('uint8')
    floor = Image.fromarray(floor_pixels)
    floor.save(RUNTIME / 'waystone-floor-v4.png')
    # Light stays a separate render pass; the original negative space remains clear.
    alpha = core.getchannel('A').resize((256, 384), Image.Resampling.LANCZOS)
    soft = np.asarray(alpha.filter(ImageFilter.GaussianBlur(7)), dtype=np.float32)
    wide = np.asarray(alpha.filter(ImageFilter.GaussianBlur(18)), dtype=np.float32)
    glow = Image.new('RGBA', (256, 384), (153, 96, 240, 0))
    glow.putalpha(Image.fromarray(np.minimum(160, soft * .85 + wide * .40).astype('uint8')))
    glow.save(RUNTIME / 'waystone-glow-v4.png')
    sheet = Image.new('RGB', (768, 768), '#444750')
    sheet.paste(core, (0, 0), core)
    small = core.resize((128, 192), Image.Resampling.LANCZOS)
    sheet.paste(small, (576, 280), small)
    sheet.save(ART / 'decal-review.jpg', quality=92)
    outputs = []
    for path in [ART/'waystone-rune-generated.png',RUNTIME/'waystone-rune-v4.png',RUNTIME/'waystone-glow-v4.png',RUNTIME/'waystone-floor-v4.png']:
        i=Image.open(path)
        a=np.asarray(i.getchannel('A'))
        outputs.append({'path':path.relative_to(ROOT).as_posix(),'size':list(i.size),'mode':i.mode,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'alphaAbove128Fraction':float((a>128).mean())})
    (ART/'generation.json').write_text(json.dumps({'tool':'OpenAI image_gen built-in cloud','intent':'original reference-guided generation','reference':'https://bg3.wiki/wiki/File:Underdark_Beach_Rune_Circle.png','referenceRole':'hierarchy and environment attachment research, no original game pixels installed','prompt':'prompt.txt','source':str(SOURCE),'generationStatus':'succeeded','artAcceptance':'decal reviewed; runtime pending','processing':'Pillow resize preserving source alpha; separate local alpha blur glow, no generated stone/background','outputs':outputs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__ == '__main__':
    main()
