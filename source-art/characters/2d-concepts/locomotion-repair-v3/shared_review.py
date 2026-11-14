"""Preview the exact shared body and separate rigid weapon/socket composition."""
from pathlib import Path
import json
import math
import sys

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent/'local-qwen21-unified-v3'))
import prepare
import appearance

M=json.loads((HERE/'shared-candidate/manifest.json').read_text('utf-8'))
F=prepare.inventory(M)
SHEETS={}
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)


def body(action,direction,phase):
    r=prepare.find(F,action,direction,phase)
    path=HERE/'shared-candidate'/r['image']
    if not path.exists():path=prepare.ACTOR/r['image']
    if str(path) not in SHEETS:SHEETS[str(path)]=Image.open(path).convert('RGBA')
    return prepare.canvas(r,{r['image']:SHEETS[str(path)]}),r


def combined(action,direction,phase,weapon):
    image,r=body(action,direction,phase)
    a=M['actions'][action];carry=a['equipmentLayer'];anchor=a['equipmentAnchors'][carry][direction][phase]
    g=M['movementEquipment']['weapons'][weapon][carry]
    index=g['directionFrameIndices'][M['directions'].index(direction)]
    rect=g['perFrameRects'][index];origin=g['perFrameOrigins'][index]
    path=HERE/'shared-candidate'/g['image']
    if str(path) not in SHEETS:SHEETS[str(path)]=Image.open(path).convert('RGBA')
    x,y,w,h=rect;crop=SHEETS[str(path)].crop((x,y,x+w,y+h))
    theta=math.radians(anchor['angle']);c,s=math.cos(theta),math.sin(theta)
    rotation=np.array([[c,s],[-s,c]])
    target=np.array([256+anchor['x']*400,712-anchor['y']*400])
    inverse=rotation.T;offset=np.array(origin)-inverse@target
    matrix=np.column_stack([inverse,offset])
    layer=crop.convert('RGBa').transform((512,768),Image.Transform.AFFINE,tuple(matrix.ravel()),Image.Resampling.BICUBIC).convert('RGBA')
    foreground=carry=='held' and direction!='up' or carry=='stowed' and direction=='up'
    result=Image.alpha_composite(image,layer) if foreground else Image.alpha_composite(layer,image)
    quiver=M['movementEquipment']['weapons'][weapon].get('quiver') if carry=='held' else None
    if quiver:
        back=a['equipmentAnchors']['stowed'][direction][phase];i=quiver['directionFrameIndices'][M['directions'].index(direction)]
        bx,by,bw,bh=quiver['perFrameRects'][i];crop=SHEETS[str(path)].crop((bx,by,bx+bw,by+bh));origin=quiver['perFrameOrigins'][i]
        theta=math.radians(back['angle']);c,s=math.cos(theta),math.sin(theta);inverse=np.array([[c,-s],[s,c]])
        target=np.array([256+back['x']*400,712-back['y']*400]);matrix=np.column_stack([inverse,np.array(origin)-inverse@target])
        layer=crop.convert('RGBa').transform((512,768),Image.Transform.AFFINE,tuple(matrix.ravel()),Image.Resampling.BICUBIC).convert('RGBA')
        result=Image.alpha_composite(result,layer) if direction=='up' else Image.alpha_composite(layer,result)
    hands=M['movementEquipment']['hands'][a['handOcclusion']]
    hi=M['directions'].index(direction)*hands['columns']+hands['frameIndices'][phase]
    hx,hy,hw,hh=hands['perFrameRects'][hi];origin=hands['perFrameOrigins'][hi]
    crop=SHEETS[str(path)].crop((hx,hy,hx+hw,hy+hh))
    # Occlusion crops use the same 250px/m density as the native body sheet.
    scale=400*hands['worldUnitsPerPixel'];layer=crop.convert('RGBa').transform((512,768),Image.Transform.AFFINE,
        (1/scale,0,origin[0]-256/scale,0,1/scale,origin[1]-712/scale),Image.Resampling.BICUBIC).convert('RGBA')
    return Image.alpha_composite(result,layer)


def main():
    weapons=['W01','W02','L01','W07','W08','L02','W11']
    metrics=[]
    for state,count in [('walk',4),('run',8)]:
        for carry in ['held','stowed']:
            board=Image.new('RGB',(7*180,4*292),'#22211f');draw=ImageDraw.Draw(board)
            for wi,weapon in enumerate(weapons):
                action=('explore_'+state+'_' if carry=='stowed' else state+'_')+weapon
                for di,direction in enumerate(M['directions']):
                    im=combined(action,direction,0,weapon).resize((180,270),Image.Resampling.LANCZOS)
                    board.paste(im,(wi*180,di*292+22),im)
                    draw.text((wi*180+2,di*292+1),f'{weapon} {carry} {direction}',font=FONT,fill='white')
            board.save(HERE/f'shared-{state}-{carry}-preview.jpg',quality=94)
    for state,count in [('walk',4),('run',8)]:
        for di,direction in enumerate(M['directions']):
            action='explore_'+state+'_W01';heads=[]
            for phase in range(count):
                im,r=body(action,direction,phase)
                heads.append(appearance.hair(im,r)[0]['center'])
            metrics.append(dict(state=state,direction=direction,headRangePixels400=np.ptp(heads,axis=0).tolist(),headCenters=heads))
    (HERE/'shared-head-registration.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print('Shared-body head range at 400px/m:',np.max([r['headRangePixels400'] for r in metrics],axis=0).tolist())


if __name__=='__main__':main()
