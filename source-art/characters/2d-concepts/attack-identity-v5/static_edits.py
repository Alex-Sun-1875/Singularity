"""Locally assemble the accepted attack model in every equipment idle.

Cloud pixels are limited to the arm-down garment revealed by the relaxed pose.
The accepted attack head, collar, belt kit, trousers and boots are reused. Old
equipment and gripping arms are carried through a bounded pose-space warp.
"""
from pathlib import Path
import json, sys, copy, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent/'local-qwen21-unified-v3'))
import prepare, appearance
import static_gear
ROOT=HERE.parents[3]
M=json.loads(prepare.MANIFEST.read_text())
F=prepare.inventory(M)
OLD=json.loads((HERE.parent/'body-scale-v4/inventory.json').read_text())
OLD={(r['image'],r['index']):r for r in OLD['frames']}
POSE=json.loads((HERE.parent/'body-scale-v4/pose-landmarks.json').read_text())
POSE={(r['image'],r['index']):r for r in POSE['frames']}
SHEETS={}
Y,X=np.mgrid[:768,:512]

def image(r):
    n=r['image']
    if n not in SHEETS:SHEETS[n]=Image.open(prepare.ACTOR/n).convert('RGBA')
    return prepare.canvas(r,SHEETS)

def joints(r):
    key=(r['image'],r['index']);old=OLD[key];lm=POSE[key]['landmarks']
    return np.array([[256+(v['x']-old['origin'][0])*r['scale'],712+(v['y']-old['origin'][1])*r['scale']] for v in lm])

def poly(points):
    m=Image.new('L',(512,768));ImageDraw.Draw(m).polygon(points,fill=255)
    return np.asarray(m)>0

def capsule(points,radius):
    m=Image.new('L',(512,768));d=ImageDraw.Draw(m)
    p=[tuple(map(float,v)) for v in points]
    d.line(p,fill=255,width=2*radius)
    for x,y in p:d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)
    return np.asarray(m)>0

def clean(im):
    a=np.asarray(im).copy();a[a[...,3]<16]=0
    labels,_=ndi.label(a[...,3]>=16);counts=np.bincount(labels.ravel());bad=counts<16;bad[0]=False
    a[bad[labels]]=0
    return Image.fromarray(a)

def premul_affine(im,size,matrix):
    return im.convert('RGBa').transform(size,Image.Transform.AFFINE,matrix,Image.Resampling.BICUBIC).convert('RGBA')

HEAD={
 'down':[(218,68),(291,68),(299,166),(318,187),(305,205),(207,205),(207,180)],
 'right':[(208,42),(296,42),(306,119),(303,150),(287,184),(226,181),(215,145)],
 'up':[(207,77),(296,77),(297,173),(309,199),(192,199),(207,165)],
 'left':[(218,66),(315,66),(315,151),(303,184),(309,205),(223,205),(226,161)]}
WAIST={
 'down':[(192,307),(310,307),(321,420),(275,435),(256,405),(238,433),(173,419),(169,350)],
 'right':[(211,309),(302,309),(310,415),(220,408),(190,389),(191,340)],
 'up':[(187,302),(313,302),(340,391),(273,410),(252,379),(228,406),(165,388)],
 'left':[(257,310),(299,310),(324,342),(326,390),(292,407),(276,386),(290,361)]}
GEN_ARMS={
 'down':[([(183,217),(163,302),(161,426)],24), ([(323,215),(345,308),(350,429)],24)],
 'right':[([(240,202),(241,300),(256,440)],27), ([(292,210),(311,309),(328,435)],22)],
 'up':[([(185,224),(167,309),(160,434)],24), ([(316,220),(338,311),(346,432)],24)],
 'left':[([(288,217),(282,307),(266,443)],27), ([(236,219),(222,309),(219,432)],20)]}

def masters():
    cloud=Image.open(HERE/'cloud-neutral-candidate.png').convert('RGBA')
    out={};report=[];board=Image.new('RGB',(1000,768),'#34383b')
    for di,d in enumerate(prepare.DIRECTIONS):
        r=prepare.find(F,'attack_sword_W01',d,0);ref=clean(image(r))
        c=cloud.crop(((di%2)*512,(di//2)*768,(di%2+1)*512,(di//2+1)*768))
        ri,_=appearance.hair(ref);ci,_=appearance.hair(c)
        # Match ground and hair center without normalizing to individual bounds.
        sy=(712-ri['center'][1])/(712-ci['center'][1]);sx=1.0
        dx=ri['center'][0]-ci['center'][0]
        c=premul_affine(c,(512,768),(1/sx,0,-dx/sx,0,1/sy,712-712/sy))
        a=np.asarray(c).copy();a[a[...,3]<32]=0
        # Exact accepted head/neck and collar, no generated identity replacement.
        h=HEAD[d];hm=poly(h)
        # Do not clear beyond the inserted head patch: an expanded clear mask
        # leaves a transparent horizontal neck/shoulder seam. Blend only the
        # lowest collar pixels back into the existing garment below it.
        bottom=max(p[1] for p in h)
        collar_weight=np.clip((bottom-Y)/8,0,1)
        clear=hm&(Y<bottom-8)
        a[clear]=0
        patch=np.asarray(ref).copy();patch[~hm]=0
        labels,_=ndi.label(patch[...,3]>=16);counts=np.bincount(labels.ravel());counts[0]=0
        patch[labels!=counts.argmax()]=0
        patch[...,3]=np.uint8(np.rint(patch[...,3]*collar_weight))
        c=Image.alpha_composite(Image.fromarray(a),Image.fromarray(patch))
        # Preserve the original belt, pouches and split panels wherever visible.
        wm=poly(WAIST[d]);patch=np.asarray(ref).copy();patch[~wm]=0
        c=Image.alpha_composite(c,Image.fromarray(patch))
        # Preserve the original full lower legs and embossed boots, not model
        # output boot variants. No original hand extends into this region.
        arr=np.asarray(c).copy();arr[Y>=438]=np.asarray(ref)[Y>=438]
        c=clean(Image.fromarray(arr));out[d]=c
        (HERE/'masters').mkdir(exist_ok=True);c.save(HERE/'masters'/f'neutral-{d}.png')
        t=c.resize((250,375),Image.Resampling.LANCZOS);board.paste(t,(di*250,0),t)
        t=ref.resize((250,375),Image.Resampling.LANCZOS);board.paste(t,(di*250,390),t)
        report.append(dict(direction=d,cloudHairCenter=ci['center'],acceptedHairCenter=ri['center'],cloudRegistration={'sx':sx,'sy':sy,'dx':dx},headSource='exact attack phase0 pixels',lowerBodySource='exact attack phase0 pixels below y438',waistSource='exact visible attack phase0 belt/pouch pixels; left occluded cloth remains arm-down repair'))
    board.save(HERE/'master-review.jpg',quality=92)
    (HERE/'master-report.json').write_text(json.dumps(report,indent=2))
    return out

def warp_original(im,j,canon):
    s=j[[11,12]].mean(0);h=j[[23,24]].mean(0)
    cs=canon[[11,12]].mean(0);ch=canon[[23,24]].mean(0)
    # Monotone piecewise vertical map: neck/shoulders and hip, ground held fixed.
    dst=np.array([0,cs[1],ch[1],712,768.]);src=np.array([s[1]-cs[1],s[1],h[1],712,768.])
    yp=np.interp(np.arange(768),dst,src)
    dx=np.interp(np.arange(768),[0,cs[1],ch[1],712,768],[cs[0]-s[0],cs[0]-s[0],ch[0]-h[0],0,0])
    coords=np.array([np.broadcast_to(yp[:,None],(768,512)),X-dx[:,None]])
    a=np.asarray(im.convert('RGBa'));v=np.stack([ndi.map_coordinates(a[...,k],coords,order=1,mode='constant',cval=0) for k in range(4)],-1).astype('uint8')
    result=Image.fromarray(v,'RGBa').convert('RGBA')
    q=j.copy();q[:,1]=np.interp(j[:,1],src,dst);q[:,0]+=np.interp(q[:,1],np.arange(768),dx)
    return result,q

def gear_mask(im,r,j):
    a=np.asarray(im);rgb=a[...,:3].astype(int);rr,gg,bb=np.moveaxis(rgb,-1,0)
    hsv=np.asarray(im.convert('RGB').convert('HSV'))
    opaque=a[...,3]>=16
    # Leather/metal equipment, excluding wine fabric and charcoal sleeves.
    material=((rr-gg>4)&(gg-bb>10)&(rr>65))|((hsv[...,1]>65)&(bb>rr*1.08))|((rgb.min(-1)>150)&(hsv[...,1]<65))
    d=r['direction'];refs=' '.join(x['action'] for x in r['refs'])
    bow=any(x in refs for x in ('W07','W08','L02'));staff='W11' in refs
    if d=='down':
        back=poly([(165,75),(239,75),(239,255),(180,300),(152,205)])
        if bow:back|=poly([(278,76),(350,76),(355,339),(274,342)])
    elif d=='up':
        back=capsule([(318,124),(180,448)],15)
        if bow:back|=poly([(271,85),(338,90),(339,334),(265,338)])
    elif d=='right':back=poly([(178,74),(243,74),(241,430),(182,435)])
    else:back=poly([(282,74),(343,74),(353,433),(287,433)])
    # Side-view scabbards sit behind the shoulder. Keeping a broad warm-colour
    # rectangle also retains the old gold collar rim, which creates a duplicate
    # collar. Limit that equipment band to its actual back edge.
    if d=='right':back&=X<234
    if d=='left':back&=X>302
    result=back&material&opaque
    return ndi.binary_dilation(result,iterations=1)&opaque

def make_one(r,master):
    before=clean(image(r));j=joints(r)
    cr=prepare.find(F,'attack_sword_W01',r['direction'],0);cj=joints(cr)
    old,q=warp_original(before,j,cj);oa=np.asarray(old)
    arms=np.zeros((768,512),bool)
    d=r['direction']
    # Visible arm guard uses the original pose's actual pixels. Occluded-side
    # keypoints can be unreliable, so limit side guards to the visible arm.
    sides=(0,1) if d in ('down','up') else ((1,) if d=='right' else (0,))
    for side in sides:
        sh,el,wr=q[[11+side,13+side,15+side]]
        arms|=capsule([sh,el,wr],22 if d in ('down','up') else 24)
        arms|=capsule([wr,wr+(wr-el)*.22],17)
    orgb=oa[...,:3].astype(int);orr,ogg,obb=np.moveaxis(orgb,-1,0)
    wine=(orr>ogg+10)&(orr>obb+12)&(ogg-obb<14)
    arm_material=~wine
    # A shoulder capsule must never bring the old neck/collar along with the
    # sleeve: it otherwise produces two stacked collars under the new head.
    # The elbow-down source RGBA is already the exact gripping arm/cuff/hand.
    # A wine-colour gate also rejects pink skin and embroidered cuff pixels,
    # making tiny holes. Preserve the complete original foreground instead.
    arms&=(oa[...,3]>=16)&(Y>275)
    # A wrist is not a fingertip: include the entire source hand beyond it.
    # Seed skin in a broad hand envelope, then retain its actual RGB/alpha
    # boundary instead of pasting old trouser pixels in a rectangular patch.
    rgb0=oa[...,:3].astype(int);r0,g0,b0=np.moveaxis(rgb0,-1,0)
    flesh=(r0>g0+12)&(g0>b0+5)&(g0-b0<60)&(r0>145)&(g0>95)&(b0>65)
    for side in sides:
        el,wr=q[[13+side,15+side]]
        hand_roi=capsule([wr,wr+(wr-el)*.60],25)
        hand_seed=ndi.binary_fill_holes(ndi.binary_closing(flesh&hand_roi,iterations=1))
        hand=ndi.binary_dilation(hand_seed,iterations=2)&hand_roi
        arms|=hand&(oa[...,3]>=16)&(Y>275)
    gear=np.zeros((768,512),bool)
    raw_gear=static_gear.make_equipment_mask(before,r,j)
    ga=np.zeros((768,512,4),dtype=np.uint8);ga[raw_gear]=255
    warped_gear,_=warp_original(Image.fromarray(ga),j,cj)
    gear|=(np.asarray(warped_gear)[...,3]>=8)&(oa[...,3]>=8)
    guard=arms|gear
    ma=np.asarray(master).copy()
    # Remove generated arm silhouettes completely before restoring the source
    # arm; this prevents a second wrist/hand when equipment idle poses differ.
    erase=np.zeros((768,512),bool)
    for points,rad in GEN_ARMS[d]:erase|=capsule(points,rad)
    # Remove the complete generated lower arm/hand once. Dark pink shadow is
    # not reliably separable from burgundy fabric by colour; restore the clean
    # accepted torso underneath, then place the real source arm on top.
    erase&=(Y>=300)
    ma[erase]=0
    # Recover cloth/pants occluded by the generated relaxed hands from the
    # accepted attack drawing, before placing the real gripping arm on top.
    ref=np.asarray(clean(image(cr)))
    trunk=poly([(196,300),(305,300),(326,433),(320,736),(182,736),(181,431)])
    if d=='right':trunk=poly([(215,300),(303,300),(309,410),(307,432),(338,736),(216,736),(204,426)])
    if d=='left':trunk=poly([(220,300),(312,300),(325,437),(323,736),(198,736),(217,426)])
    fill=erase&(trunk|poly(WAIST[d]))&(Y>=300)&(ref[...,3]>=16)
    if d=='right':fill&=~((X>=312)&(Y>=330)&(Y<437))
    ma[fill]=ref[fill]
    ma[guard]=oa[guard]
    result=clean(Image.fromarray(ma))
    return before,result,{'direction':d,'source':r['image'],'index':r['index'],'armPixels':int(arms.sum()),'equipmentPixels':int(gear.sum()),'acceptedReferenceScale':cr['scale'],'headAndBody':'attack phase0 authority; source gripping arms/equipment transformed around shoulder/hip, foot anchor fixed'}

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');args=p.parse_args()
    ms=masters();records=[]
    for r in F.values():
        if not any('idle' in v['action'] for v in r['refs']):continue
        if args.pilot and not any(v['action'] in ('idle_W01','explore_idle_W01') for v in r['refs']):continue
        records.append(r)
    out=HERE/'edits/static';out.mkdir(parents=True,exist_ok=True)
    report=[];edits=[];board=Image.new('RGB',(len(records)//4*400,840),'#34383b');draw=ImageDraw.Draw(board)
    columns={};counter=0
    for r in records:
        before,after,info=make_one(r,ms[r['direction']]);report.append(info)
        cr=prepare.find(F,'attack_sword_W01',r['direction'],0);scale=cr['scale']
        # Store at the accepted attack's native pixel density to avoid inventing
        # additional detail through idle-atlas upsampling.
        a=np.asarray(after);ys,xs=np.nonzero(a[...,3]>=16);box=[xs.min()-3,ys.min()-3,xs.max()+4,ys.max()+4]
        size=(math.ceil((box[2]-box[0])/scale),math.ceil((box[3]-box[1])/scale))
        crop=premul_affine(after,size,(scale,0,box[0],0,scale,box[1]))
        filename=f'static-{len(edits):03d}-{r["direction"]}.png';crop.save(out/filename)
        factor=M['frameScaleFactors'][r['image'].removesuffix('.png')][r['index']]*scale/r['scale']
        edits.append(dict(image=r['image'],index=r['index'],cropPath=filename,origin=[(256-box[0])/scale,(712-box[1])/scale],newFactor=factor))
        action=next(v['action'] for v in r['refs'] if 'idle' in v['action'])
        if action not in columns:columns[action]=len(columns)
        col=columns[action];row=prepare.DIRECTIONS.index(r['direction']);y=row*210
        for off,im in ((0,before),(200,after)):
            t=im.resize((140,210),Image.Resampling.LANCZOS);board.paste(t,(col*400+off+30,y),t)
        draw.text((col*400+4,y+2),f'{action} / {r["direction"]}',fill='white')
    (out/'static.json').write_text(json.dumps(edits,indent=2))
    (HERE/'static-report.json').write_text(json.dumps({'status':'candidate; visual review required','frames':report},indent=2))
    board.save(HERE/('static-pilot-review.jpg' if args.pilot else 'all-static-review.jpg'),quality=92)
    print({'staticFrames':len(edits),'columns':len(columns),'pilot':args.pilot})

if __name__=='__main__':main()
