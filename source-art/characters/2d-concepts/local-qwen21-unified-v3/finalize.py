"""Bound actual local-Qwen RGB to the reviewed guides; preserve source alpha."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import numpy as np
from PIL import Image
import appearance as art

HERE=art.HERE

def tile(board,i):
    x=(i%2)*256;y=(i//2)*384
    return board.crop((x,y,x+256,y+384)).convert('RGBa').resize((512,768),Image.Resampling.BICUBIC).convert('RGBA')

def compose(guide,raw,mask,strength=1):
    a=np.asarray(guide);b=np.asarray(raw);m=np.asarray(mask)/255
    confidence=np.clip((b[...,3].astype(float)-230)/20,0,1)*np.clip((a[...,3].astype(float)-230)/20,0,1)
    w=m*confidence*strength
    result=a.copy();result[...,:3]=np.uint8(np.clip(np.rint(a[...,:3]*(1-w[...,None])+b[...,:3]*w[...,None]),0,255))
    assert np.array_equal(result[...,3],a[...,3])
    assert np.array_equal(result[m==0],a[m==0])
    return Image.fromarray(result),int((w>0).sum())

def main():
    approved=HERE/'approved';approved.mkdir(exist_ok=True)
    standing=Image.open(HERE/'results/v3-standing-four-directions/raw-model.png').convert('RGBA')
    attack=Image.open(HERE/'results/v3-attack-four-directions/raw-model.png').convert('RGBA')
    attack_mask=Image.open(HERE/'qwen-inputs/attack-edit-mask.png').convert('L')
    head_reports=json.loads((HERE/'attack-head-guide-report.json').read_text())
    reports=[]
    for i,d in enumerate(art.prepare.DIRECTIONS):
        source=Image.open(HERE/'references'/f'identity-{d}.png').convert('RGBA')
        cloth=Image.open(HERE/'references'/f'clothing-{d}.png').convert('RGBA')
        guide,_=art.grade(source,cloth)
        masks,_=art.material_masks(source)
        union=Image.fromarray(np.maximum.reduce([np.asarray(m) for m in masks.values()]))
        candidate,n=compose(guide,tile(standing,i),union,.55)
        master,_=art.grade(candidate,cloth)
        master.save(approved/f'standing-{d}.png')
        guide=Image.open(HERE/'qwen-inputs'/f'attack-{d}-guide.png').convert('RGBA')
        x=(i%2)*256;y=(i//2)*384
        mask=attack_mask.crop((x,y,x+256,y+384)).resize((512,768),Image.Resampling.BILINEAR)
        m=np.asarray(mask).copy();ny=head_reports[i]['original_neck_xy'][1]
        m[art.Y<ny-8]=0 # exact standing-derived face/hair/jaw core
        candidate,k=compose(guide,tile(attack,i),Image.fromarray(m),1)
        candidate.save(approved/f'attack-{d}.png')
        reports.append(dict(direction=d,standing_qwen_pixels=n,attack_neck_qwen_pixels=k,
            alpha_preserved=True,face_hair_core_preserved=True,raw_model_untouched=True))
    (HERE/'finalization-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps(reports))

if __name__=='__main__':main()
