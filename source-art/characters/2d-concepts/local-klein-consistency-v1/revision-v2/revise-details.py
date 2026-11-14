"""Repair rejected details locally from original artwork and standing palette."""
from pathlib import Path
import importlib.util
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PANTS=load('pants_palette',HERE/'pants-audit/pants_palette.py')
SWORD=load('preserve_tip',HERE/'sword-audit/preserve_tip.py')
HAND_PATCHES={
    'sword-back':[(146,368,187,437),(323,368,364,437)],
    'clothing-side':[(187,318,252,389),(351,243,411,316)],
    'run-front':[(190,266,276,351),(335,360,383,428)],
    'run-back':[(133,350,184,411)],
}
HAND_CORES={
    'sword-back':[(152,374,181,431),(329,374,358,431)],
    'clothing-side':[(195,326,244,381),(359,251,403,308)],
    'run-front':[(202,290,263,339),(343,368,375,420)],
    'run-back':[(141,358,176,403)],
}


def restore_hands(image,before,case):
    mask=np.zeros((768,512),np.uint8)
    if case=='sword-back':
        # Original foreground occludes the longer scabbard; finger gaps stay open.
        alpha=np.asarray(Image.open(ROOT/'geometry-inputs/explore-idle-back-p0-alpha.png').convert('L'))
        original=np.asarray(before).astype(float)
        result_pixels=np.asarray(image).astype(float).copy()
        for x0,y0,x1,y1 in HAND_PATCHES[case]:
            a=alpha[y0:y1,x0:x1].astype(float)/255
            old=original[y0:y1,x0:x1]
            background=result_pixels[y0:y1,x0:x1]
            # Undo the original gray review matte before placing AA skin edges
            # over the scabbard, avoiding a gray/white border around the fingers.
            foreground=np.clip((old-228*(1-a[:,:,None]))/np.maximum(a[:,:,None],1/255),0,255)
            mixed=foreground*a[:,:,None]+background*(1-a[:,:,None])
            opaque=alpha[y0:y1,x0:x1]>=250
            mixed[opaque]=old[opaque]
            result_pixels[y0:y1,x0:x1]=mixed
            mask[y0:y1,x0:x1]=np.where(opaque,255,alpha[y0:y1,x0:x1])
        result=Image.fromarray(np.clip(np.rint(result_pixels),0,255).astype('uint8'))
    else:
        for x0,y0,x1,y1 in HAND_PATCHES[case]:
            y,x=np.indices((y1-y0,x1-x0))
            distance=np.minimum.reduce([x+1,y+1,x1-x0-x,y1-y0-y])
            patch=np.clip(distance/4,0,1)*255
            mask[y0:y1,x0:x1]=np.maximum(mask[y0:y1,x0:x1],patch.astype('uint8'))
        result=Image.composite(before,image,Image.fromarray(mask))
    for x0,y0,x1,y1 in HAND_CORES[case]:
        a,b=np.asarray(result)[y0:y1,x0:x1],np.asarray(before)[y0:y1,x0:x1]
        core=mask[y0:y1,x0:x1]==255
        assert np.array_equal(a[core],b[core]),(case,'original-hand mismatch')
        if case!='sword-back': assert core.all(),(case,'hand core not fully protected')
    return result,Image.fromarray(mask)


cases=json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))
reports=[]
for case in cases:
    name=case['name'];folder=Path(case['directory']);out=HERE/'results'/name
    out.mkdir(parents=True,exist_ok=True)
    before=Image.open(folder/'before.png').convert('RGB')
    previous=Image.open(ROOT/'results'/name/'constrained-candidate.png').convert('RGB')
    if name=='sword-back':
        candidate,tip_metrics=SWORD.build_candidate(before)
        pants_report=None
    else:
        direction={'clothing-side':'right','run-front':'front','run-back':'back'}[name]
        reference=Image.open(folder/'reference.png').convert('RGB')
        candidate,pants_report=PANTS.match_pants(previous,reference,direction,mask_output=out/'pants-mask.png')
        tip_metrics=None
    final,hands=restore_hands(candidate,before,name)
    # Restoration is deliberately the final pixel operation after all colour work.
    final.paste(before.crop((0,0,512,190)),(0,0))
    if name.startswith('run-'):
        final.paste(before.crop((0,650,512,768)),(0,650))
    final.save(out/'candidate-v2.png');hands.save(out/'hand-protection-mask.png')
    assert np.array_equal(np.asarray(final)[:190],np.asarray(before)[:190])
    if name.startswith('run-'):assert np.array_equal(np.asarray(final)[650:],np.asarray(before)[650:])
    report={'case':name,'output':str(out/'candidate-v2.png'),'sha256':hashlib.sha256((out/'candidate-v2.png').read_bytes()).hexdigest(),
        'hand_cores':HAND_CORES[name],'hand_patch_bounds':HAND_PATCHES[name],
        'original_hand_pixels_exact_under_full_protection':True,'head_pixels_original':True,
        'hands_restored_after_all_colour_operations':True,'pants':pants_report,'sword':tip_metrics,
        'cloud_generation':False,'new_model_inference':False,'method':'Reuse previous local-model proportions; original hand/cap pixels and standing-palette correction',
        'production_modified':False,'status':'revised single-frame sample, not installed'}
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    reports.append(report)
(HERE/'revision-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')

try:FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
except OSError:FONT=ImageFont.load_default()
board=Image.new('RGB',(1056,840),(245,245,245));draw=ImageDraw.Draw(board)
labels=['剑尖原件复用','裤色对齐站姿','正跑手部复原','背跑裤色与手部']
for i,(case,label) in enumerate(zip(cases,labels)):
    x=32+i*256;name=case['name']
    draw.text((x+8,5),label,font=FONT,fill=(25,25,25))
    board.paste(Image.open(ROOT/'results'/name/'constrained-candidate.png').resize((240,360),Image.Resampling.LANCZOS),(x+8,40))
    board.paste(Image.open(HERE/'results'/name/'candidate-v2.png').resize((240,360),Image.Resampling.LANCZOS),(x+8,455))
draw.text((4,185),'上\n轮',font=FONT,fill=(55,55,55));draw.text((4,565),'本\n轮',font=FONT,fill=(55,55,55))
board.save(HERE/'comparison-v2.jpg',quality=91,optimize=True)

detail=Image.new('RGB',(900,930),(245,245,245));draw=ImageDraw.Draw(detail)
tiles=[
 ('原剑鞘末端',ROOT/'guides/sword-back/before.png',(170,330,240,405)),
 ('上轮末端变形',ROOT/'results/sword-back/constrained-candidate.png',(139,395,209,470)),
 ('本轮末端平移复用',HERE/'results/sword-back/candidate-v2.png',(139,395,209,470)),
 ('原正跑手',ROOT/'guides/run-front/before.png',(188,266,278,356)),
 ('上轮手指错位',ROOT/'results/run-front/constrained-candidate.png',(188,266,278,356)),
 ('本轮手部复原',HERE/'results/run-front/candidate-v2.png',(188,266,278,356)),
 ('站姿裤色参考',ROOT/'geometry-inputs/explore-idle-right-p0.png',(145,395,410,645)),
 ('上轮跑步裤色',ROOT/'results/clothing-side/constrained-candidate.png',(145,395,410,645)),
 ('本轮跑步裤色',HERE/'results/clothing-side/candidate-v2.png',(145,395,410,645)),
]
for i,(label,path,box) in enumerate(tiles):
    x=(i%3)*300;y=(i//3)*310
    draw.text((x+10,y+8),label,font=FONT,fill=(25,25,25))
    im=Image.open(path).crop(box);im.thumbnail((280,260),Image.Resampling.LANCZOS)
    if i<6:im=im.resize((252,252),Image.Resampling.NEAREST)
    detail.paste(im,(x+12,y+42))
detail.save(HERE/'detail-comparison-v2.jpg',quality=93,optimize=True)
print(json.dumps([{'case':r['case'],'hand_pixels_locked':True,'tip_unchanged_shape':bool(r['sword']),'pants_matched':r['pants'] is not None} for r in reports],indent=2))
