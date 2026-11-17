"""Deterministic atlas preparation. No local generative model is used."""
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
import json, hashlib

HERE=Path(__file__).resolve().parent
OUT=HERE/'assets'
OUT.mkdir(exist_ok=True)

def soft_edges(im):
    a=np.asarray(im,dtype=np.float32).copy()
    # Preserve the generated alpha, gently suppressing isolated low-alpha grains.
    alpha=a[:,:,3]/255
    a[:,:,3]=255*alpha*np.clip(alpha/.09,0,1)
    return Image.fromarray(np.uint8(np.clip(a,0,255)))

def main():
    source=Image.open(HERE/'raw/fire-lifecycle.png').convert('RGBA')
    assert source.size==(1536,1024),source.size
    atlas=soft_edges(source)
    atlas.save(OUT/'fire-pyro-v7.png')
    rolls=Image.new('RGBA',(4*128,8*96))
    for phase in range(16):
        cell=atlas.crop(((phase%4)*384,(phase//4)*256,(phase%4+1)*384,(phase//4+1)*256))
        for side in range(2):
            # Preserve a whole flame silhouette. Cutting a hot frame in half creates
            # an obvious rectangular slab when that piece is rendered at ground level.
            crop=cell.crop((0,48,384,256)).resize((128,96),Image.Resampling.LANCZOS)
            if side:crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            tile=Image.new('RGBA',(128,96))
            tile.paste(crop,(0,0))
            index=phase+side*16
            rolls.paste(tile,((index%4)*128,(index//4)*96))
    rolls.save(OUT/'fire-low-rolls-v7.png')
    lance=Image.open(HERE/'raw/fire-lance.png').convert('RGBA')
    cw,ch=lance.width//2,lance.height//2
    strip=Image.new('RGBA',(1024,256))
    for index in range(4):
        tile=soft_edges(lance.crop(((index%2)*cw,(index//2)*ch,(index%2+1)*cw,(index//2+1)*ch)))
        a=np.asarray(tile.getchannel('A'))
        y,x=np.where(a>24)
        crop=tile.crop((max(0,int(x.min())-10),max(0,int(y.min())-10),min(cw,int(x.max())+11),min(ch,int(y.max())+11)))
        target_w=218
        target_h=min(132,round(crop.height*target_w/crop.width))
        crop=crop.resize((target_w,target_h),Image.Resampling.LANCZOS)
        strip.paste(crop,(index*256+5,128-target_h//2))
    strip.save(OUT/'fire-bolt-v9.png')
    provenance={
        'backend':'OpenAI image_gen built-in cloud tool',
        'generated':[{'raw':'raw/fire-lifecycle.png','layout':'4x4 RGBA, 384x256 cells','purpose':'ignition, peak, collapse, low flames, embers'},
                     {'raw':'raw/fire-lance.png','layout':'2x2 RGBA; repacked to existing 4x1 bolt atlas','purpose':'coherent pointed fire lance'}],
        'references':['src/cocos/assets/resources/vfx/production/fire-pyro-v7.png','src/cocos/assets/resources/vfx/production/fire-bolt-v9.png','src/.tmp/current-vfx-refinement-v4/final/refined/FIR_02/027.jpg'],
        'promptSummary':[
            'Preserve current Cocos 3D visual language and exact 4x4 atlas/foot anchors. Sixteen coherent frames: ignition 0-3, curled luminous flame peak 4-7, settling fire 8-10, low residual tongues and sparse embers 11-15. Warm amber cores, orange-red folded fire. Transparent RGBA. No characters, circles, rocks, text, mushroom smoke, dotted debris, hard floor edge.',
            'Four phases of one long pointed fire lance, 2x2 RGBA. Hot pointed tip at right, continuous curled orange-red tail at left. Refine current projectile rather than replace the gameplay. Consistent head position, proportions and lighting. Transparent background, no labels or circles.'
        ],
        'promptRecord':'Summaries of the two tool prompts; full verbatim calls remain in this conversation.',
        'deterministicProcessing':'Pillow and NumPy; alpha cleanup, resizing, crop feather, repacking only. No local model inference.',
        'generationStatus':'Both calls completed successfully',
        'artAcceptance':'Candidate pending user review',
        'productIntegration':False,
        'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*sorted((HERE/'raw').glob('*.png')),*sorted(OUT.glob('*.png'))]}
    }
    (HERE/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({p.name:Image.open(p).size for p in OUT.glob('*.png')}))

if __name__=='__main__':main()
